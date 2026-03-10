#!/usr/bin/env python3
"""
Campaign Health Check — Audit campaign settings against defaults.

Checks all non-REMOVED campaigns for:
  - Geo targeting (should be US-only)
  - Location options (should be PRESENCE, not PRESENCE_OR_INTEREST)
  - Search partners (should be OFF)
  - Display network (should be OFF)
  - Negative keyword coverage (should have SharedSet linked)
  - Budget sanity (not $0, not unreasonably high)

Usage:
    python3 scripts/campaign_health_check.py
"""

import sys
import os

for path_offset in [
    os.path.join(os.path.dirname(__file__), "..", "..", ".."),
    os.path.dirname(os.path.dirname(__file__)),
]:
    normalized = os.path.normpath(os.path.abspath(path_offset))
    if os.path.exists(os.path.join(normalized, "utils", "client.py")):
        sys.path.insert(0, normalized)
        break

from utils.client import get_client, CUSTOMER_ID
from google.ads.googleads.errors import GoogleAdsException


def get_campaigns(ga_service):
    """Fetch all non-REMOVED campaigns with settings."""
    query = """
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.campaign_budget,
            campaign.network_settings.target_google_search,
            campaign.network_settings.target_search_network,
            campaign.network_settings.target_content_network,
            campaign.geo_target_type_setting.positive_geo_target_type
        FROM campaign
        WHERE campaign.status != 'REMOVED'
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query)
    campaigns = []
    for row in response:
        campaigns.append({
            "id": row.campaign.id,
            "name": row.campaign.name,
            "status": row.campaign.status.name,
            "budget_resource": row.campaign.campaign_budget,
            "target_google_search": row.campaign.network_settings.target_google_search,
            "target_search_network": row.campaign.network_settings.target_search_network,
            "target_content_network": row.campaign.network_settings.target_content_network,
            "geo_target_type": row.campaign.geo_target_type_setting.positive_geo_target_type.name,
        })
    return campaigns


def get_budgets(ga_service):
    """Fetch all campaign budgets."""
    query = """
        SELECT
            campaign_budget.resource_name,
            campaign_budget.amount_micros,
            campaign_budget.explicitly_shared
        FROM campaign_budget
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query)
    budgets = {}
    for row in response:
        budgets[row.campaign_budget.resource_name] = {
            "amount_micros": row.campaign_budget.amount_micros,
            "amount_usd": row.campaign_budget.amount_micros / 1_000_000,
            "explicitly_shared": row.campaign_budget.explicitly_shared,
        }
    return budgets


def get_campaign_shared_sets(ga_service):
    """Check which campaigns have negative keyword shared sets linked."""
    query = """
        SELECT
            campaign.id,
            shared_set.name,
            shared_set.type
        FROM campaign_shared_set
        WHERE shared_set.type = 'NEGATIVE_KEYWORDS'
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query)
    linked = {}
    for row in response:
        campaign_id = row.campaign.id
        if campaign_id not in linked:
            linked[campaign_id] = []
        linked[campaign_id].append(row.shared_set.name)
    return linked


def get_geo_targets(ga_service):
    """Check geo targeting for each campaign."""
    query = """
        SELECT
            campaign.id,
            campaign_criterion.location.geo_target_constant,
            campaign_criterion.negative
        FROM campaign_criterion
        WHERE campaign_criterion.type = 'LOCATION'
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query)
    geo = {}
    for row in response:
        campaign_id = row.campaign.id
        if campaign_id not in geo:
            geo[campaign_id] = {"positive": [], "negative": []}
        geo_constant = row.campaign_criterion.location.geo_target_constant
        if row.campaign_criterion.negative:
            geo[campaign_id]["negative"].append(geo_constant)
        else:
            geo[campaign_id]["positive"].append(geo_constant)
    return geo


def run_health_check():
    """Run all health checks and print results."""
    client = get_client()
    ga_service = client.get_service("GoogleAdsService")

    print(f"\n{'='*70}")
    print("CAMPAIGN HEALTH CHECK")
    print(f"{'='*70}")

    campaigns = get_campaigns(ga_service)
    budgets = get_budgets(ga_service)
    shared_sets = get_campaign_shared_sets(ga_service)
    geo_targets = get_geo_targets(ga_service)

    if not campaigns:
        print("\nNo active campaigns found.")
        return

    total_issues = 0

    for camp in campaigns:
        issues = []
        warnings = []

        # Check network settings
        if camp["target_search_network"]:
            issues.append("Search partners is ON (should be OFF)")
        if camp["target_content_network"]:
            issues.append("Display network is ON (should be OFF)")

        # Check geo target type
        if camp["geo_target_type"] != "PRESENCE":
            issues.append(f"Geo target type is {camp['geo_target_type']} (should be PRESENCE)")

        # Check geo targeting
        geo = geo_targets.get(camp["id"], {"positive": [], "negative": []})
        us_targeted = any("2840" in g for g in geo["positive"])
        if not geo["positive"]:
            warnings.append("No geo targeting set (should target US)")
        elif not us_targeted:
            issues.append("US (2840) is not in positive geo targets")
        if len(geo["positive"]) > 1:
            warnings.append(f"Multiple geo targets ({len(geo['positive'])} locations)")

        # Check negative keyword coverage
        if camp["id"] not in shared_sets:
            issues.append("No negative keyword shared set linked")

        # Check budget
        budget = budgets.get(camp["budget_resource"])
        if budget:
            if budget["amount_micros"] == 0:
                issues.append("Budget is $0")
            elif budget["amount_usd"] > 500:
                warnings.append(f"Budget is ${budget['amount_usd']:.0f}/day (unusually high)")
            if budget["explicitly_shared"]:
                warnings.append("Budget is explicitly shared (may break smart bidding)")

        # Print results for this campaign
        status_icon = "PASS" if not issues else "FAIL"
        print(f"\n[{status_icon}] {camp['name']} [{camp['status']}]")

        if budget:
            print(f"      Budget: ${budget['amount_usd']:.0f}/day")

        neg_sets = shared_sets.get(camp["id"], [])
        if neg_sets:
            print(f"      Negatives: {', '.join(neg_sets)}")

        for issue in issues:
            print(f"      ISSUE: {issue}")
            total_issues += 1

        for warning in warnings:
            print(f"      WARN:  {warning}")

    # Summary
    print(f"\n{'='*70}")
    print(f"Campaigns checked: {len(campaigns)}")
    print(f"Issues found: {total_issues}")
    if total_issues == 0:
        print("All campaigns pass health check.")
    else:
        print("Fix the issues above to align with default campaign settings.")
    print(f"{'='*70}\n")


def main():
    try:
        run_health_check()
    except GoogleAdsException as ex:
        print(f"\nGoogle Ads API error (request ID: {ex.request_id}):")
        for error in ex.failure.errors:
            print(f"  [{error.error_code}] {error.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
