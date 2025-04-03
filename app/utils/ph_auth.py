import requests
import os, json
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

CACHE_PATH = ".cache/ph_token.json"

# Call access token endpoint to get access token
def get_ph_token():
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
    try:
        token = response.json()["access_token"]
    except ValueError:
        raise SystemExit("Aborting due to invalid JSON response.")
    response.raise_for_status()

    # Cache the token as json file
    os.makedirs(".cache", exist_ok=True)
    with open(CACHE_PATH, "w") as f:
        json.dump({
            "access_token": token,
            "fetched_at": datetime.now(timezone.utc).isoformat()
        }, f)

    return token


# Get cached token if it exists and is less than max_age_hours old
# else get a new token
def get_cached_token(max_age_hours=24) -> str:
    if os.path.exists(CACHE_PATH):
        with open(CACHE_PATH, "r") as f:
            data = json.load(f)
        fetched_at = datetime.fromisoformat(data["fetched_at"])
        if datetime.now(timezone.utc) - fetched_at < timedelta(hours=max_age_hours):
            return data["access_token"]
    return get_ph_token()  # fallback - get a new token