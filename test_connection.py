"""
Dry-run connection test for Google Ads API.
Fetches basic account info without making any changes.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException

def test_connection():
    credentials = {
        "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
        "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
        "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
        "use_proto_plus": True,
    }

    customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID")

    print("Connecting to Google Ads API...")
    client = GoogleAdsClient.load_from_dict(credentials)

    ga_service = client.get_service("GoogleAdsService")

    query = """
        SELECT
            customer.id,
            customer.descriptive_name,
            customer.currency_code,
            customer.time_zone,
            customer.status
        FROM customer
        LIMIT 1
    """

    try:
        response = ga_service.search(customer_id=customer_id, query=query)
        for row in response:
            c = row.customer
            print("\n✅ Connection successful!")
            print(f"   Account ID:   {c.id}")
            print(f"   Account Name: {c.descriptive_name}")
            print(f"   Currency:     {c.currency_code}")
            print(f"   Timezone:     {c.time_zone}")
            print(f"   Status:       {c.status.name}")
    except GoogleAdsException as ex:
        print(f"\n❌ Google Ads API error:")
        for error in ex.failure.errors:
            print(f"   [{error.error_code}] {error.message}")

if __name__ == "__main__":
    test_connection()
