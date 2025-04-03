import json
import random
import requests
from app.utils.ph_auth import get_cached_token

EXTERNAL_DATE_THRESHOLD = "2023-01-01T00:00:00Z"
MAX_FOLLOWERS = 500
BATCH_SIZE = 1
MAX_BATCHES = 30
GRAPHQL_URL = "https://api.producthunt.com/v2/api/graphql"

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Authorization": f"Bearer {get_cached_token()}",
    "Host": "api.producthunt.com",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
}

def make_graphql_request(query: str):
    response = requests.post(GRAPHQL_URL, headers=HEADERS, json={"query": query})
    
    # Log rate limit headers
    print("X-Rate-Limit-Limit:", response.headers.get("X-Rate-Limit-Limit"))
    print("X-Rate-Limit-Remaining:", response.headers.get("X-Rate-Limit-Remaining"))
    print("X-Rate-Limit-Reset:", response.headers.get("X-Rate-Limit-Reset"))
    
    # Check for rate limit
    if response.status_code == 429:
        print("Rate limit exceeded. Back off and retry later.")
        return None

    return response.json()

def get_batch_query():
    # after_clause = f', after: "{after_cursor}"' if after_cursor else ''
    skip_clause = 0;
    return f"""
    query {{
      posts(first: {BATCH_SIZE}, topic: "artificial-intelligence", order: RANKING) {{
        edges {{
          node {{
            id
            name
            description
            website
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
    # cursor_pool = []
    # after = None

    # # Phase 1: Collect 3 cursors to randomly pick from
    # for _ in range(3):
    #     query = get_batch_query(after)
    #     data = make_graphql_request(query)
    #     if not data:
    #         break
    #     page_info = data['data']['posts']['pageInfo']
    #     if page_info['endCursor']:
    #         cursor_pool.append(page_info['endCursor'])
    #     if not page_info['hasNextPage']:
    #         break
    #     after = page_info['endCursor']

    # # Phase 2: Random batch querying
    # for _ in range(MAX_BATCHES):
    #     random_cursor = random.choice(cursor_pool) if cursor_pool else None
    #     query = get_batch_query(random_cursor)
    #     batch_data = make_graphql_request(query)
    #     if not batch_data:
    #         break
    #     print(json.dumps(batch_data, indent=2))
    query = get_batch_query()
    data = make_graphql_request(query)
    print(json.dumps(data, indent=2))
if __name__ == "__main__":
    main()