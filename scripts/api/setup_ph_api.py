# Script to setup access token for the Product Hunt API
from app.utils.ph_auth import get_ph_access_token

def main():
    print("🔐 Testing Product Hunt API auth...")
    try:
        token = get_ph_access_token()
        print(f"\n✅ Success! Access token:\n{token[:8]}...{token[-8:]}")
    except Exception as e:
        print(f"\n❌ Failed to get token: {e}")

if __name__ == "__main__":
    main()
