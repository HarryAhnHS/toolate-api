import os, json
import time
import requests
from app.utils.ph_auth import get_cached_token

# Config - each post crawl takes 10 complexity credits - 6250 per 15 minutes
GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"
EXTERNAL_DATE_THRESHOLD = "2023-01-01T00:00:00Z"
BATCH_SIZE = 10
MAX_BATCHES = 1
OUTPUT_FILE = "data/scrapes/ph_ai.json"
CURSOR_FILE = "data/scrapes/ph_ai_cursor.json"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {get_cached_token()}",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
}

# OS helpers
def load_cursor():
    if os.path.exists(CURSOR_FILE):
        with open(CURSOR_FILE, "r") as f:
            try:
                return json.load(f).get("after")
            except:
                return None
    return None

def save_cursor(after_cursor):
    with open(CURSOR_FILE, "w") as f:
        json.dump({"after": after_cursor}, f)

def load_existing_posts():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

def save_posts(posts):
    with open(OUTPUT_FILE, "w") as f:
        json.dump(posts, f, indent=2)

def make_graphql_request(query: str):
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": query})
    
    remainingCredits = int(response.headers.get("X-Rate-Limit-Remaining"))
    print("X-Rate-Limit-Remaining:", response.headers.get("X-Rate-Limit-Remaining"))
    
    if response.status_code == 429 or remainingCredits < 100:
        print("Rate limit exceeded. Backing off.")
        time.sleep(10)
        return None

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return None

    return response.json(), remainingCredits

def get_batch_query(after_cursor=None):
    after_clause = f', after: "{after_cursor}"' if after_cursor else ""
    return f"""
    query {{
      posts(first: {BATCH_SIZE}, topic: "artificial-intelligence", order: RANKING{after_clause}) {{
        edges {{
          node {{
            id
            name
            description
            website
            url
            createdAt
            topics(first: 3) {{
              edges {{
                node {{
                  name
                }}
              }}
            }}
            comments(first: 3, order: VOTES_COUNT) {{
              edges {{
                node {{
                  body
                }}
              }}
            }}
          }}
        }}
        pageInfo {{
          endCursor
          hasNextPage
        }}
      }}
    }}
    """

def main():
    after_cursor = load_cursor()
    existing_map = {p["id"]: p for p in load_existing_posts()}

    # Collect posts from new batches
    for i in range(MAX_BATCHES):
        print(f"Fetching batch {i+1}")
        query = get_batch_query()
        result, remainingCredits = make_graphql_request(query)
        if not result:
            print("Stopping early due to rate limits or failure.")
            break

        print(f"Successful Batch {i+1}: {result}")
        print(f"Remaining credits: {remainingCredits}")
        
        collected_edges = result["data"]["posts"]["edges"]
        for edge in collected_edges:
            post = edge["node"]
            existing_map[post["id"]] = post  # Dedup/merge by ID, else append to existing map

        page_info = result["data"]["posts"]["pageInfo"]
        after_cursor = page_info["endCursor"]

        # Save the cursor
        save_cursor(after_cursor)

        if not page_info["hasNextPage"]:
            print("✅ Reached end of feed.")
            break

        time.sleep(1)  # polite crawl
    print(f"\n✅ Collected {len(existing_map)} unique posts")

    # After session, save the posts to json
    save_posts(list(existing_map.values()))
    print(f"\n✅ Merged and saved {len(existing_map)} posts to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()