"""
Comprehensive daily analysis: performance breakdown, conversion audit,
search terms, keyword quality, ad performance, and geo check.

Usage: python3 reports/daily_analysis.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.client import get_client, CUSTOMER_ID
from google.ads.googleads.errors import GoogleAdsException


def run_analysis():
    client = get_client()
    ga_service = client.get_service("GoogleAdsService")

    # ── Query 1: Daily Campaign Performance ──────────────────────────
    print(f"\n{'='*70}")
    print("1. DAILY CAMPAIGN PERFORMANCE (March 9-11)")
    print(f"{'='*70}")

    query1 = """
        SELECT
            campaign.name, campaign.status, segments.date,
            metrics.impressions, metrics.clicks, metrics.ctr,
            metrics.average_cpc, metrics.cost_micros,
            metrics.conversions, metrics.all_conversions,
            metrics.cost_per_conversion
        FROM campaign
        WHERE segments.date BETWEEN '2026-03-09' AND '2026-03-11'
          AND campaign.status != 'REMOVED'
        ORDER BY segments.date DESC
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query1)
    print(f"\n{'Date':<12} {'Campaign':<45} {'Imp':>6} {'Clicks':>6} {'CTR':>7} {'CPC':>6} {'Cost':>8} {'Conv':>5} {'AllConv':>7}")
    print("-" * 110)
    for row in response:
        c = row.campaign
        m = row.metrics
        cost = m.cost_micros / 1_000_000
        cpc = m.average_cpc / 1_000_000
        print(f"{row.segments.date:<12} {c.name:<45} {m.impressions:>6} {m.clicks:>6} {m.ctr:>6.2%} ${cpc:>5.2f} ${cost:>7.2f} {m.conversions:>5.1f} {m.all_conversions:>7.1f}")

    # ── Query 2a: Conversion Action Setup ────────────────────────────
    print(f"\n{'='*70}")
    print("2. CONVERSION ACTION AUDIT")
    print(f"{'='*70}")

    query2a = """
        SELECT
            conversion_action.id,
            conversion_action.name,
            conversion_action.status,
            conversion_action.type,
            conversion_action.category,
            conversion_action.counting_type
        FROM conversion_action
        WHERE conversion_action.status != 'REMOVED'
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query2a)
    print(f"\n{'Name':<40} {'Status':<10} {'Type':<25} {'Category':<20} {'Counting'}")
    print("-" * 120)
    for row in response:
        ca = row.conversion_action
        print(f"{ca.name:<40} {ca.status.name:<10} {ca.type.name:<25} {ca.category.name:<20} {ca.counting_type.name}")

    # ── Query 2b: Conversion Actions with Recent Data ────────────────
    print(f"\n--- Conversion Actions with Data (Last 7 Days) ---")
    query2b = """
        SELECT
            conversion_action.name,
            metrics.all_conversions
        FROM conversion_action
        WHERE segments.date DURING LAST_7_DAYS
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query2b)
    print(f"{'Name':<40} {'All Conv':>10}")
    print("-" * 55)
    has_data = False
    for row in response:
        has_data = True
        ca = row.conversion_action
        m = row.metrics
        if m.all_conversions > 0:
            print(f"{ca.name:<40} {m.all_conversions:>10.1f}")
    if not has_data:
        print("  ** NO conversion data recorded in last 7 days **")

    # ── Query 3: Search Terms ────────────────────────────────────────
    print(f"\n{'='*70}")
    print("3. SEARCH TERMS (Last 7 Days)")
    print(f"{'='*70}")

    query3 = """
        SELECT
            search_term_view.search_term,
            campaign.name, ad_group.name,
            metrics.impressions, metrics.clicks,
            metrics.cost_micros, metrics.conversions, metrics.ctr
        FROM search_term_view
        WHERE segments.date DURING LAST_7_DAYS
          AND campaign.status = 'ENABLED'
        ORDER BY metrics.cost_micros DESC
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query3)

    NEGATIVE_SIGNALS = [
        "foods with", "food high in", "rich foods", "recipe", "cooking",
        "dosage for", "side effects", "interactions", "overdose", "deficiency symptoms",
        "doctor", "prescription", "medication",
        "how to make", "what is", "wiki", "definition", "vs ",
        "cream", "lotion", "spray", "powder bulk", "liquid",
        "free sample", "coupon code", "discount code",
        "uk", "canada", "australia", "india",
    ]

    terms = []
    for row in response:
        terms.append({
            "term": row.search_term_view.search_term,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "cost": row.metrics.cost_micros / 1_000_000,
            "conversions": row.metrics.conversions,
            "ctr": row.metrics.ctr,
        })

    # Categorize
    promote, negative, monitor = [], [], []
    for t in terms:
        term_lower = t["term"].lower()
        has_signal = any(s in term_lower for s in NEGATIVE_SIGNALS)
        if t["conversions"] >= 2:
            promote.append(t)
        elif t["clicks"] >= 3 and (has_signal or t["conversions"] == 0):
            negative.append(t)
        else:
            monitor.append(t)

    if promote:
        print(f"\n--- PROMOTE TO EXACT MATCH ({len(promote)}) ---")
        for t in sorted(promote, key=lambda x: x["conversions"], reverse=True):
            print(f"  {t['term']:<45} clicks={t['clicks']}  conv={t['conversions']:.0f}  cost=${t['cost']:.2f}")

    if negative:
        print(f"\n--- FLAG AS NEGATIVE ({len(negative)}) ---")
        for t in sorted(negative, key=lambda x: x["cost"], reverse=True):
            print(f"  {t['term']:<45} clicks={t['clicks']}  conv={t['conversions']:.0f}  cost=${t['cost']:.2f}")

    print(f"\n--- MONITOR ({len(monitor)}) ---")
    for t in sorted(monitor, key=lambda x: x["clicks"], reverse=True)[:25]:
        print(f"  {t['term']:<45} clicks={t['clicks']}  conv={t['conversions']:.0f}  cost=${t['cost']:.2f}")
    if len(monitor) > 25:
        print(f"  ... and {len(monitor) - 25} more")

    total_cost = sum(t["cost"] for t in terms)
    neg_cost = sum(t["cost"] for t in negative)
    print(f"\nTotal terms: {len(terms)} | Total spend: ${total_cost:.2f} | Wasted (negatives): ${neg_cost:.2f}")

    # ── Query 4: Keyword Performance + Quality Score ─────────────────
    print(f"\n{'='*70}")
    print("4. KEYWORD PERFORMANCE + QUALITY SCORE")
    print(f"{'='*70}")

    query4 = """
        SELECT
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.quality_info.quality_score,
            metrics.impressions, metrics.clicks,
            metrics.cost_micros, metrics.conversions,
            metrics.average_cpc
        FROM keyword_view
        WHERE campaign.status = 'ENABLED'
          AND segments.date DURING LAST_7_DAYS
        ORDER BY metrics.cost_micros DESC
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query4)
    print(f"\n{'Keyword':<40} {'Match':<8} {'QS':>3} {'Imp':>6} {'Clicks':>6} {'CPC':>6} {'Cost':>8} {'Conv':>5}")
    print("-" * 90)
    for row in response:
        kw = row.ad_group_criterion
        m = row.metrics
        qs = kw.quality_info.quality_score if kw.quality_info.quality_score else 0
        print(f"{kw.keyword.text:<40} {kw.keyword.match_type.name:<8} {qs:>3} {m.impressions:>6} {m.clicks:>6} ${m.average_cpc/1_000_000:>5.2f} ${m.cost_micros/1_000_000:>7.2f} {m.conversions:>5.1f}")

    # ── Query 5: Ad (RSA) Performance ────────────────────────────────
    print(f"\n{'='*70}")
    print("5. AD (RSA) PERFORMANCE")
    print(f"{'='*70}")

    query5 = """
        SELECT
            ad_group_ad.ad.id,
            ad_group_ad.ad.responsive_search_ad.headlines,
            ad_group_ad.ad.responsive_search_ad.descriptions,
            ad_group_ad.ad_strength,
            metrics.impressions, metrics.clicks,
            metrics.conversions, metrics.cost_micros
        FROM ad_group_ad
        WHERE campaign.status = 'ENABLED'
          AND segments.date DURING LAST_7_DAYS
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query5)
    for row in response:
        ad = row.ad_group_ad
        m = row.metrics
        cost = m.cost_micros / 1_000_000
        print(f"\nAd ID: {ad.ad.id} | Strength: {ad.ad_strength.name}")
        print(f"  Impressions: {m.impressions:,} | Clicks: {m.clicks:,} | Cost: ${cost:.2f} | Conv: {m.conversions:.1f}")
        if ad.ad.responsive_search_ad.headlines:
            print("  Headlines:")
            for h in ad.ad.responsive_search_ad.headlines:
                pinned = f" [pinned:{h.pinned_field.name}]" if h.pinned_field and h.pinned_field.name != "UNSPECIFIED" else ""
                print(f"    - {h.text}{pinned}")
        if ad.ad.responsive_search_ad.descriptions:
            print("  Descriptions:")
            for d in ad.ad.responsive_search_ad.descriptions:
                print(f"    - {d.text}")

    # ── Query 6: Geographic Performance ──────────────────────────────
    print(f"\n{'='*70}")
    print("6. GEOGRAPHIC PERFORMANCE (Last 7 Days)")
    print(f"{'='*70}")

    query6 = """
        SELECT
            campaign.status,
            geographic_view.country_criterion_id,
            geographic_view.location_type,
            metrics.clicks, metrics.impressions,
            metrics.cost_micros, metrics.conversions
        FROM geographic_view
        WHERE segments.date DURING LAST_7_DAYS
          AND campaign.status = 'ENABLED'
        ORDER BY metrics.cost_micros DESC
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query6)
    print(f"\n{'Country ID':<15} {'Location Type':<25} {'Imp':>6} {'Clicks':>6} {'Cost':>8} {'Conv':>5}")
    print("-" * 70)
    for row in response:
        geo = row.geographic_view
        m = row.metrics
        us_flag = " (US)" if geo.country_criterion_id == 2840 else " ** NON-US **"
        print(f"{geo.country_criterion_id:<15} {geo.location_type.name:<25} {m.impressions:>6} {m.clicks:>6} ${m.cost_micros/1_000_000:>7.2f} {m.conversions:>5.1f}{us_flag}")


if __name__ == "__main__":
    try:
        run_analysis()
    except GoogleAdsException as ex:
        print(f"\nGoogle Ads API error (request ID: {ex.request_id}):")
        for error in ex.failure.errors:
            print(f"  [{error.error_code}] {error.message}")
        sys.exit(1)
