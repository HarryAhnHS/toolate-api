import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Call access token endpoint to get access token
def get_ph_access_token():
    url = "https://api.producthunt.com/v2/oauth/token"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    }
    data = {
        "client_id": os.getenv("PH_CLIENT_ID"),
        "client_secret": os.getenv("PH_CLIENT_SECRET"),
        "grant_type": "client_credentials"
    }

    response = requests.post(url, json=data, headers=headers)
    
    # print("\nResponse Status Code:", response.status_code)
    # print("Response Headers:", dict(response.headers))
    
    try:
        json_data = response.json()
    except ValueError:
        print("Got HTML instead of JSON. Likely blocked by Cloudflare.")
        print("Raw body:", response.text[:500])
        raise SystemExit("Aborting due to invalid JSON response.")
    response.raise_for_status()

    print("Successfully got access token")
    return json_data["access_token"]