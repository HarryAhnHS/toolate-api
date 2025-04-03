from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from app.utils.ph_auth import get_ph_access_token
import json, os, random

OUTPUT_PATH = "app/data/ph_general_seed.json"

# Step 1: Get access token
token = get_ph_access_token()

# Step 2: Set up GraphQL client
transport = RequestsHTTPTransport(
    url="https://api.producthunt.com/v2/api/graphql",
    headers={"Authorization": f"Bearer {token}"},
    use_json=True,
)

client = Client(transport=transport, fetch_schema_from_transport=True)

# Step 3: Define query
query = gql("""
query GetPosts($cursor: String) {
  posts(first: 50, after: $cursor, order: RANK) {
    edges {
      node {
        name
        tagline
        url
        postedAt
        topics {
          edges {
            node {
              name
            }
          }
        }
      }
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
""")

# Step 4: Fetch and store data
cursor = None
all_posts = []
seen_urls = set()

while len(all_posts) < 200:
    result = client.execute(query, variable_values={"cursor": cursor})
    posts = result["posts"]["edges"]

    for post in posts:
        node = post["node"]
        url = node["url"]

        if url in seen_urls:
            continue

        topics = [t["node"]["name"] for t in node["topics"]["edges"]]
        all_posts.append({
            "name": node["name"],
            "description": node["tagline"],
            "url": url,
            "topics": topics,
            "postedAt": node["postedAt"],
            "source": "Product Hunt"
        })
        seen_urls.add(url)

    if not result["posts"]["pageInfo"]["hasNextPage"]:
        break

    cursor = result["posts"]["pageInfo"]["endCursor"]

random.shuffle(all_posts)
with open(OUTPUT_PATH, "w") as f:
    json.dump(all_posts[:200], f, indent=2)

print(f"✅ Saved {len(all_posts[:200])} Product Hunt posts to {OUTPUT_PATH}")