"""
Create a Responsive Search Ad (RSA) for the Calm+Rest Magnesium campaign.

Looks up the ad group in the existing campaign and creates a PAUSED RSA
with 15 headlines and 4 descriptions. Headlines 1 and 2 are pinned.

Usage: python campaigns/calm-rest/03_create_rsa.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from utils.client import get_client, CUSTOMER_ID
from google.ads.googleads.errors import GoogleAdsException

CAMPAIGN_NAME = "SR | Calm+Rest | Magnesium | Broad"

FINAL_URL = (
    "https://www.trustedselections.org/top-5-best-magnesium-2026"
    "?utm_source=google&utm_medium=cpc"
    "&utm_campaign=calm-rest-magnesium-broad"
    "&utm_content=broad-magnesium-supplements"
    "&utm_term={keyword}"
)

# (text, pinned_position or None)
# pinned_position: HEADLINE_1, HEADLINE_2, etc.
HEADLINES = [
    ("Best Magnesium of 2026", "HEADLINE_1"),
    ("Top Magnesium for Calm & Sleep", "HEADLINE_2"),
    ("See Top 5 Magnesium Picks 2026", None),
    ("Melatonin-Free Magnesium Blend", None),
    ("Chelamax\u00ae Magnesium + More", None),
    ("Expert Magnesium Reviews 2026", None),
    ("#1 Magnesium for Sleep Support", None),
    ("Best Magnesium Supplement 2026", None),
    ("Compare Top Magnesium Brands", None),
    ("Clinical-Dose Magnesium Blend", None),
    ("USA Made \u00b7 GMP Certified", None),
    ("Magnesium Without Melatonin", None),
    ("Top-Rated Magnesium Formula", None),
    ("90-Day Money-Back Guarantee", None),
    ("Best Magnesium for Stress+Rest", None),
]

DESCRIPTIONS = [
    "See our 2026 ranking of the best magnesium supplements for stress support & restful sleep.",
    "Compare top picks featuring Chelamax\u00ae bioavailable magnesium, L-Theanine & clinical doses.",
    "Non-habit-forming magnesium that supports calm, relaxation & a healthy stress response.",
    "USA-made. GMP certified. 90-day guarantee. Find your top-rated magnesium supplement now.",
]


def find_ad_group(ga_service):
    """Find the ad group resource name for our campaign."""
    query = f"""
        SELECT ad_group.id, ad_group.name, ad_group.resource_name
        FROM ad_group
        WHERE campaign.name = '{CAMPAIGN_NAME}'
          AND ad_group.status != 'REMOVED'
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query)
    for row in response:
        print(f"Found ad group: {row.ad_group.name} ({row.ad_group.resource_name})")
        return row.ad_group.resource_name

    print(f"ERROR: No ad group found for campaign '{CAMPAIGN_NAME}'.")
    print("Run 02_create_campaign.py first.")
    sys.exit(1)


def create_rsa(client, ad_group_resource_name):
    """Create the Responsive Search Ad."""
    ad_group_ad_service = client.get_service("AdGroupAdService")
    op = client.get_type("AdGroupAdOperation")

    ad_group_ad = op.create
    ad_group_ad.ad_group = ad_group_resource_name
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED

    ad = ad_group_ad.ad
    ad.final_urls.append(FINAL_URL)

    rsa = ad.responsive_search_ad

    # Build headlines
    for text, pin in HEADLINES:
        headline = client.get_type("AdTextAsset")
        headline.text = text
        if pin is not None:
            headline.pinned_field = client.enums.ServedAssetFieldTypeEnum[pin]
        rsa.headlines.append(headline)

    # Build descriptions
    for text in DESCRIPTIONS:
        desc = client.get_type("AdTextAsset")
        desc.text = text
        rsa.descriptions.append(desc)

    response = ad_group_ad_service.mutate_ad_group_ads(
        customer_id=CUSTOMER_ID, operations=[op]
    )
    resource_name = response.results[0].resource_name
    print(f"Created RSA: {resource_name}")
    return resource_name


def main():
    print(f"\n{'='*60}")
    print("Create Responsive Search Ad — Calm+Rest Magnesium")
    print(f"{'='*60}\n")

    try:
        client = get_client()
        ga_service = client.get_service("GoogleAdsService")

        # Step 1: Find the ad group
        print("Step 1: Looking up ad group...")
        ad_group_rn = find_ad_group(ga_service)

        # Step 2: Create the RSA
        print(f"\nStep 2: Creating RSA (PAUSED) with {len(HEADLINES)} headlines, {len(DESCRIPTIONS)} descriptions...")
        rsa_rn = create_rsa(client, ad_group_rn)

        print(f"\n{'='*60}")
        print("DONE — RSA created successfully (PAUSED).")
        print(f"  Ad Group Ad: {rsa_rn}")
        print(f"  Headlines:   {len(HEADLINES)}")
        print(f"  Descriptions: {len(DESCRIPTIONS)}")
        print(f"{'='*60}\n")

    except GoogleAdsException as ex:
        print(f"\nGoogle Ads API error (request ID: {ex.request_id}):")
        for error in ex.failure.errors:
            print(f"  [{error.error_code}] {error.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
