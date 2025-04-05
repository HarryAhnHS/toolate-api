import json
import requests
from app.utils.ph_auth import get_cached_token

QUERY = {
    "query": """
    query GetFirstPosts {
      posts(first: 3) {
        nodes {
          name
          website
          productLinks {
            type
            url
          }
        }
      }
    }
    """
}

def main():
    token = get_cached_token()
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "Host": "api.producthunt.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    }

    response = requests.post(
        "https://api.producthunt.com/v2/api/graphql",
        json=QUERY,
        headers=headers
    )

    if response.status_code == 200:
        posts = response.json()["data"]["posts"]["nodes"]
        for post in posts:
            print(f"\n🔹 {post['name']}")
            print(f"🌐 Website: {post.get('website', 'N/A')}")
            print("🔗 Product Links:")
            for link in post.get("productLinks", []):
                print(f"  - {link['type']}: {link['url']}")
    else:
        print(f"❌ Failed with status {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()