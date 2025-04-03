import os, json, random
import time
import requests
import signal, sys
from app.utils.ph_auth import get_cached_token

# Config - each post crawl takes 10 complexity credits - 6250 per 15 minutes
GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"
BATCH_SIZE = 10
INITIAL_COMPLEXITY_CREDITS = 6250
POLITE_DELTA = random.randint(1, 5) # randomize polite delta
MAX_WAIT_TIME = 900 + POLITE_DELTA # 15 minutes + 5 seconds for polite
OUTPUT_FILE = "app/data/scrapes/ph_ai_db.json"
CACHE_FILE = "app/data/scrapes/ph_ai_cache.json"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {get_cached_token()}",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
}

# Globals to use in SIGINT handler
existing_map = {}
cache_map = {
    "after": None,
    "remaining_credits": INITIAL_COMPLEXITY_CREDITS,
    "rate_limit_reset_time": time.time() + MAX_WAIT_TIME, # stores timestamp of when rate limit will reset
    "batch_count": 0
}

# OS helpers
def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            try:
                data = json.load(f)
                cache_map["after"] = data.get("after")
                cache_map["remaining_credits"] = data.get("remaining_credits")
                cache_map["rate_limit_reset_time"] = data.get("rate_limit_reset_time")
                cache_map["batch_count"] = data.get("batch_count")
            except:
                print("⚠️ Failed to load cache; using defaults.")

def save_cache():
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(cache_map, f, indent=2)

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
    
    if response.status_code == 429:
        print("⚠️ Rate limit exceeded. returning for next iteration.")
        return None

    if response.status_code != 200:
        print(f"⚠️ Error {response.status_code}: {response.text}")
        return None
    
    remainingCredits = int(response.headers.get("X-Rate-Limit-Remaining", "0"))
    reset_in_seconds = int(response.headers.get("X-Rate-Limit-Reset", "0"))

    # Update cache with new credits and reset time
    cache_map["remaining_credits"] = remainingCredits
    cache_map["rate_limit_reset_time"] = time.time() + reset_in_seconds

    return response.json()

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
            votesCount
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

# Graceful shutdown on Ctrl+C or interrupt signal
def handle_exit(signum, frame):
    print("\n⚠️ Interrupted. Saving current state...")
    save_posts(list(existing_map.values()))
    save_cache()
    print("✅ State saved. Exiting.")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

def main():
    global existing_map

    # Load existing cache and posts
    load_cache()
    existing_map = {p["id"]: p for p in load_existing_posts()}

    print("🔁 Infinite Scraper started. Press [ctrl] + [c] anytime to quit gracefully.\n")
    # Infinite crawl loop
    while True:
        print(f"\n🕒 Batch {cache_map['batch_count']} started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Current credits: {cache_map['remaining_credits']}")

        # Pause if rate limit is too low
        if cache_map["remaining_credits"] < 100:
            wait_time = cache_map["rate_limit_reset_time"] - time.time()
            wait_time = max(wait_time, 0)  # EDGE: avoid negative wait
            print(f"⏳ Waiting {int(wait_time)}s for rate limit reset...")
            time.sleep(wait_time + POLITE_DELTA)

        # Run the query
        query = get_batch_query(cache_map["after"])
        result = make_graphql_request(query)
        if not result:
            print("⚠️ Continuing to next iteration.")
            continue  # loop will wait if needed on next pass

        cache_map["batch_count"] += 1
        print(f"✅ Successful batch {cache_map['batch_count']} | Remaining credits: {cache_map['remaining_credits']}")

        # Merge new posts
        collected_edges = result["data"]["posts"]["edges"]
        for edge in collected_edges:
            post = edge["node"]
            existing_map[post["id"]] = post  # Dedup by ID

        # Advance cursor
        page_info = result["data"]["posts"]["pageInfo"]
        cache_map["after"] = page_info["endCursor"]

        # Save state
        save_cache()
        save_posts(list(existing_map.values()))

        # EDGE: Stop if end of posts reached
        if not page_info["hasNextPage"]:
            print("✅ Reached end of feed. Exiting.")
            break;

        # Polite delay
        time.sleep(POLITE_DELTA)


if __name__ == "__main__":
    main()