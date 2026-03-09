"""
Create the Calm+Rest Magnesium Search campaign, budget, ad group, and keywords.

Creates everything in PAUSED state. Will not run if the campaign already exists.

Usage: python campaigns/calm-rest/02_create_campaign.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.client import get_client, CUSTOMER_ID
from google.ads.googleads.errors import GoogleAdsException

CAMPAIGN_NAME = "SR | Calm+Rest | Magnesium | Broad"
AD_GROUP_NAME = "Broad — Magnesium Supplements"
BUDGET_NAME = "Calm+Rest Magnesium — $50/day"
DAILY_BUDGET_MICROS = 50_000_000  # $50
CPC_BID_MICROS = 1_000_000  # $1.00

FINAL_URL = (
    "https://www.trustedselections.org/top-5-best-magnesium-2026"
    "?utm_source=google&utm_medium=cpc"
    "&utm_campaign=calm-rest-magnesium-broad"
    "&utm_content=broad-magnesium-supplements"
    "&utm_term={keyword}"
)

KEYWORDS = [
    "best magnesium supplements",
    "best magnesium for sleep",
]


def campaign_exists(ga_service):
    """Check if the campaign already exists (non-REMOVED)."""
    query = f"""
        SELECT campaign.name, campaign.status
        FROM campaign
        WHERE campaign.status != 'REMOVED'
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query)
    for row in response:
        if row.campaign.name == CAMPAIGN_NAME:
            return True
    return False


def create_budget(client):
    """Create a campaign budget and return its resource name."""
    budget_service = client.get_service("CampaignBudgetService")
    op = client.get_type("CampaignBudgetOperation")

    budget = op.create
    budget.name = BUDGET_NAME
    budget.amount_micros = DAILY_BUDGET_MICROS
    budget.delivery_method = client.enums.BudgetDeliveryMethodEnum.STANDARD
    budget.explicitly_shared = False

    response = budget_service.mutate_campaign_budgets(
        customer_id=CUSTOMER_ID, operations=[op]
    )
    resource_name = response.results[0].resource_name
    print(f"Created budget: {resource_name}")
    return resource_name


def create_campaign(client, budget_resource_name):
    """Create the Search campaign and return its resource name."""
    campaign_service = client.get_service("CampaignService")
    op = client.get_type("CampaignOperation")

    campaign = op.create
    campaign.name = CAMPAIGN_NAME
    campaign.status = client.enums.CampaignStatusEnum.PAUSED
    campaign.advertising_channel_type = client.enums.AdvertisingChannelTypeEnum.SEARCH
    campaign.campaign_budget = budget_resource_name
    campaign.contains_eu_political_advertising = 3  # DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING

    # Bidding strategy: Manual CPC (switch to Maximize Conversions in UI after launch)
    # Note: maximize_conversions via API requires additional account config not set here.
    # Manual CPC is equivalent while PAUSED; change in UI: Settings > Bidding before enabling.
    campaign.manual_cpc.enhanced_cpc_enabled = False

    # Network settings
    campaign.network_settings.target_google_search = True
    campaign.network_settings.target_search_network = True
    campaign.network_settings.target_content_network = False

    response = campaign_service.mutate_campaigns(
        customer_id=CUSTOMER_ID, operations=[op]
    )
    resource_name = response.results[0].resource_name
    print(f"Created campaign: {resource_name}")
    return resource_name


def create_ad_group(client, campaign_resource_name):
    """Create the ad group and return its resource name."""
    ad_group_service = client.get_service("AdGroupService")
    op = client.get_type("AdGroupOperation")

    ad_group = op.create
    ad_group.name = AD_GROUP_NAME
    ad_group.status = client.enums.AdGroupStatusEnum.ENABLED
    ad_group.campaign = campaign_resource_name
    ad_group.type_ = client.enums.AdGroupTypeEnum.SEARCH_STANDARD
    ad_group.cpc_bid_micros = CPC_BID_MICROS

    response = ad_group_service.mutate_ad_groups(
        customer_id=CUSTOMER_ID, operations=[op]
    )
    resource_name = response.results[0].resource_name
    print(f"Created ad group: {resource_name}")
    return resource_name


def create_keywords(client, ad_group_resource_name):
    """Create broad-match keywords in the ad group."""
    criterion_service = client.get_service("AdGroupCriterionService")
    operations = []

    for kw_text in KEYWORDS:
        op = client.get_type("AdGroupCriterionOperation")
        criterion = op.create
        criterion.ad_group = ad_group_resource_name
        criterion.status = client.enums.AdGroupCriterionStatusEnum.ENABLED
        criterion.keyword.text = kw_text
        criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
        criterion.final_urls.append(FINAL_URL)
        operations.append(op)

    response = criterion_service.mutate_ad_group_criteria(
        customer_id=CUSTOMER_ID, operations=operations
    )

    print("Created keywords:")
    for result in response.results:
        print(f"  {result.resource_name}")

    return [r.resource_name for r in response.results]


def main():
    print(f"\n{'='*60}")
    print(f"Create Campaign: {CAMPAIGN_NAME}")
    print(f"{'='*60}\n")

    try:
        client = get_client()
        ga_service = client.get_service("GoogleAdsService")

        # Pre-flight: check if campaign already exists
        if campaign_exists(ga_service):
            print(f"ERROR: Campaign '{CAMPAIGN_NAME}' already exists. Aborting.")
            sys.exit(1)

        # Step 1: Create budget
        print("Step 1: Creating campaign budget...")
        budget_rn = create_budget(client)

        # Step 2: Create campaign
        print("\nStep 2: Creating campaign (PAUSED)...")
        campaign_rn = create_campaign(client, budget_rn)

        # Step 3: Create ad group
        print("\nStep 3: Creating ad group...")
        ad_group_rn = create_ad_group(client, campaign_rn)

        # Step 4: Create keywords
        print("\nStep 4: Creating keywords...")
        keyword_rns = create_keywords(client, ad_group_rn)

        print(f"\n{'='*60}")
        print("DONE — Campaign created successfully (PAUSED).")
        print(f"  Campaign:  {campaign_rn}")
        print(f"  Ad Group:  {ad_group_rn}")
        print(f"  Keywords:  {len(keyword_rns)}")
        print(f"{'='*60}\n")

    except GoogleAdsException as ex:
        print(f"\nGoogle Ads API error (request ID: {ex.request_id}):")
        for error in ex.failure.errors:
            print(f"  [{error.error_code}] {error.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
