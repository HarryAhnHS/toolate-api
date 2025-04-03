import json
import requests
import os
from app.utils.ph_auth import get_cached_token

SCHEMA_PATH = "app/data/scrapes/ph_schema.json"

INTROSPECTION_QUERY = {
    "query": """
    query IntrospectionQuery {
      __schema {
        types {
          kind
          name
          fields {
            name
            type {
              name
              kind
              ofType {
                name
                kind
              }
            }
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
        json=INTROSPECTION_QUERY,
        headers=headers
    )

    if response.status_code == 200:
        # Ensure the directory exists
        os.makedirs(os.path.dirname(SCHEMA_PATH), exist_ok=True)
        
        with open(SCHEMA_PATH, "w") as f:
            json.dump(response.json(), f, indent=2)
        print(f"✅ Schema downloaded to {SCHEMA_PATH}")
    else:
        print(f"❌ Failed with status {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    main()