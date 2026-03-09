"""
Upload a master negative keyword list to Google Ads and link it to all active campaigns.

Reads keywords from data/negative-keywords-master.txt (one per line),
creates a Shared Negative Keyword List, and attaches it to every ENABLED campaign.

Usage: python campaigns/calm-rest/01_negative_keywords.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.client import get_client, CUSTOMER_ID
from google.ads.googleads.errors import GoogleAdsException

SHARED_SET_NAME = "Master Negatives — All Campaigns"
KEYWORDS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data", "negative-keywords-master.txt"
)
BATCH_SIZE = 1000


def load_keywords(filepath):
    """Read keywords from file, one per line, skip blanks and comments."""
    if not os.path.exists(filepath):
        print(f"ERROR: Keywords file not found: {filepath}")
        sys.exit(1)

    keywords = []
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                keywords.append(line)

    if not keywords:
        print("ERROR: No keywords found in file.")
        sys.exit(1)

    print(f"Loaded {len(keywords)} negative keywords from file.")
    return keywords


def shared_set_exists(ga_service):
    """Check if a SharedSet with our name already exists."""
    query = f"""
        SELECT shared_set.id, shared_set.name, shared_set.status
        FROM shared_set
        WHERE shared_set.name = '{SHARED_SET_NAME}'
          AND shared_set.status = 'ENABLED'
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query)
    for row in response:
        return True
    return False


def create_shared_set(client):
    """Create the SharedSet and return its resource name."""
    shared_set_service = client.get_service("SharedSetService")
    shared_set_op = client.get_type("SharedSetOperation")

    shared_set = shared_set_op.create
    shared_set.name = SHARED_SET_NAME
    shared_set.type_ = client.enums.SharedSetTypeEnum.NEGATIVE_KEYWORDS

    response = shared_set_service.mutate_shared_sets(
        customer_id=CUSTOMER_ID, operations=[shared_set_op]
    )
    resource_name = response.results[0].resource_name
    print(f"Created SharedSet: {resource_name}")
    return resource_name


def upload_keywords(client, shared_set_resource_name, keywords):
    """Upload keywords as SharedCriterion objects in batches."""
    shared_criterion_service = client.get_service("SharedCriterionService")
    total = len(keywords)
    uploaded = 0

    for i in range(0, total, BATCH_SIZE):
        batch = keywords[i:i + BATCH_SIZE]
        operations = []

        for kw in batch:
            op = client.get_type("SharedCriterionOperation")
            criterion = op.create
            criterion.shared_set = shared_set_resource_name
            criterion.keyword.text = kw
            criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
            operations.append(op)

        shared_criterion_service.mutate_shared_criteria(
            customer_id=CUSTOMER_ID, operations=operations
        )
        uploaded += len(batch)
        print(f"  Uploaded {uploaded}/{total} keywords...")

    print(f"All {total} keywords uploaded.")


def get_active_campaigns(ga_service):
    """Fetch all ENABLED campaigns."""
    query = """
        SELECT campaign.id, campaign.name, campaign.resource_name, campaign.status
        FROM campaign
        WHERE campaign.status = 'ENABLED'
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query)
    campaigns = []
    for row in response:
        campaigns.append({
            "id": row.campaign.id,
            "name": row.campaign.name,
            "resource_name": row.campaign.resource_name,
        })
    return campaigns


def link_to_campaigns(client, shared_set_resource_name, campaigns):
    """Link the SharedSet to each active campaign."""
    campaign_shared_set_service = client.get_service("CampaignSharedSetService")

    for camp in campaigns:
        op = client.get_type("CampaignSharedSetOperation")
        css = op.create
        css.campaign = camp["resource_name"]
        css.shared_set = shared_set_resource_name

        campaign_shared_set_service.mutate_campaign_shared_sets(
            customer_id=CUSTOMER_ID, operations=[op]
        )
        print(f"  Linked to: {camp['name']}")

    print(f"SharedSet linked to {len(campaigns)} active campaign(s).")


def main():
    print(f"\n{'='*60}")
    print("Negative Keyword List Upload")
    print(f"{'='*60}\n")

    # Step 1: Load keywords from file
    keywords = load_keywords(KEYWORDS_FILE)

    try:
        client = get_client()
        ga_service = client.get_service("GoogleAdsService")

        # Step 2: Check if SharedSet already exists
        if shared_set_exists(ga_service):
            print(f"ERROR: SharedSet '{SHARED_SET_NAME}' already exists. Aborting.")
            sys.exit(1)

        # Step 3: Create SharedSet
        shared_set_rn = create_shared_set(client)

        # Step 4: Upload keywords in batches
        print(f"\nUploading {len(keywords)} keywords...")
        upload_keywords(client, shared_set_rn, keywords)

        # Step 5: Get active campaigns
        campaigns = get_active_campaigns(ga_service)
        if not campaigns:
            print("\nNo active campaigns found. SharedSet created but not linked.")
        else:
            # Step 6: Link to campaigns
            print(f"\nLinking to {len(campaigns)} active campaign(s)...")
            link_to_campaigns(client, shared_set_rn, campaigns)

        print(f"\n{'='*60}")
        print("DONE — Negative keyword list created and linked.")
        print(f"{'='*60}\n")

    except GoogleAdsException as ex:
        print(f"\nGoogle Ads API error (request ID: {ex.request_id}):")
        for error in ex.failure.errors:
            print(f"  [{error.error_code}] {error.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
