import os, json, random
import time
import requests
import signal, sys
from datetime import datetime
from app.utils.ph_auth import get_cached_token

# Config - each post crawl takes 10 complexity credits - 6250 per 15 minutes
GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"
BATCH_SIZE = 10
INITIAL_COMPLEXITY_CREDITS = 6250
POLITE_DELTA = random.randint(1, 5) # randomize polite delta
MAX_WAIT_TIME = 900 + POLITE_DELTA # 15 minutes + 5 seconds for polite
MAX_FAILURES = 10  # Number of consecutive failed attempts allowed
CONSECUTIVE_FAILURES = 0

OUTPUT_FILE = "app/data/scrapes/ph_scrape.json"
PROGRESS_CACHE_FILE = ".cache/scrapes/meta_ph/ph_progress_cache.json"
CACHE_FOLDER = ".cache/scrapes/checkpoints_ph/"
CACHE_EVERY_N_BATCHES = 400

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
    "rate_limit_reset_time": time.time() + MAX_WAIT_TIME,
    "batch_count": 0
}

# OS helpers
def load_cache():
    if os.path.exists(PROGRESS_CACHE_FILE):
        with open(PROGRESS_CACHE_FILE, "r") as f:
            try:
                data = json.load(f)
                cache_map["after"] = data.get("after")
                cache_map["remaining_credits"] = data.get("remaining_credits")
                cache_map["rate_limit_reset_time"] = data.get("rate_limit_reset_time")
                cache_map["batch_count"] = data.get("batch_count")
            except:
                print("⚠️ Failed to load cache; using defaults.")

def save_cache():
    os.makedirs(os.path.dirname(PROGRESS_CACHE_FILE), exist_ok=True)
    with open(PROGRESS_CACHE_FILE, "w") as f:
        json.dump(cache_map, f, indent=2)

def save_checkpoint(data, batch_idx):
    os.makedirs(CACHE_FOLDER, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(CACHE_FOLDER, f"ph_scrape_cp_batch{batch_idx}_{timestamp}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"💾 Cached checkpoint at {path}")

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

    cache_map["remaining_credits"] = remainingCredits
    cache_map["rate_limit_reset_time"] = time.time() + reset_in_seconds

    return response.json()

def get_batch_query():
    after_clause = f', after: "{cache_map["after"]}"' if cache_map["after"] else ""
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
            topics(first: 5) {{
              edges {{
                node {{
                  name
                }}
              }}
            }}
            comments(first: 5, order: VOTES_COUNT) {{
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

def handle_exit(signum, frame):
    print("\n⚠️ Interrupted. Saving current state...")
    save_posts(list(existing_map.values()))
    save_cache()
    print("✅ State saved. Exiting.")
    sys.exit(0)

signal.signal(signal.SIGINT, handle_exit)

def main():
    global existing_map

    load_cache()
    existing_map = {p["id"]: p for p in load_existing_posts()}

    print("🔁 Infinite Scraper started. Press [ctrl] + [c] anytime to quit gracefully.\n")

    failure_count = 0

    while True:
        print(f"\n🕒 Batch {cache_map['batch_count']} started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Current credits: {cache_map['remaining_credits']}")

        if cache_map["remaining_credits"] < 100:
            wait_time = cache_map["rate_limit_reset_time"] - time.time()
            wait_time = max(wait_time, 0)
            print(f"⏳ Waiting {int(wait_time)}s for rate limit reset...")
            time.sleep(wait_time + POLITE_DELTA)

        query = get_batch_query()
        result = make_graphql_request(query)

        if not result:
            failure_count += 1
            print(f"❌ Batch failed ({failure_count}/{MAX_FAILURES})")

            if failure_count >= MAX_FAILURES:
                print("🛑 Too many consecutive failures. Exiting scraper.")
                save_posts(list(existing_map.values()))
                save_cache()
                break

            continue
        else:
            failure_count = 0

        cache_map["batch_count"] += 1
        print(f"✅ Successful batch {cache_map['batch_count']} | Remaining credits: {cache_map['remaining_credits']}")

        collected_edges = result["data"]["posts"]["edges"]
        for edge in collected_edges:
            post = edge["node"]
            existing_map[post["id"]] = post

        page_info = result["data"]["posts"]["pageInfo"]
        cache_map["after"] = page_info["endCursor"]
        print(f"✅ Stored {len(existing_map)} unique entries so far.")

        if not page_info["hasNextPage"]:
            print("✅ Reached end of feed. Exiting.")
            break;

        if cache_map["batch_count"] % CACHE_EVERY_N_BATCHES == 0:
            save_checkpoint(list(existing_map.values()), cache_map["batch_count"])

        save_posts(list(existing_map.values()))
        save_cache()
        time.sleep(POLITE_DELTA)

    save_posts(list(existing_map.values()))
    print(f"🔁 Terminated! Saving {len(existing_map)} unique entries to {OUTPUT_FILE}.")
    save_cache()

if __name__ == "__main__":
    main()