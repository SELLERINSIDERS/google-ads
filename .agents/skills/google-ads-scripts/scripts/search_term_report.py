#!/usr/bin/env python3
"""
Search Term Report — Pull search terms and categorize them.

Pulls search terms from the last N days and categorizes each as:
  - PROMOTE: 2+ conversions, relevant → add as exact-match keyword
  - NEGATIVE: 3+ clicks, irrelevant → add to negative keyword list
  - MONITOR: insufficient data or ambiguous intent

Usage:
    python3 scripts/search_term_report.py --days 7
    python3 scripts/search_term_report.py --days 14 --min-clicks 5
"""

import argparse
import sys
import os

# Allow running from skill directory or project root
for path_offset in [
    os.path.join(os.path.dirname(__file__), "..", "..", ".."),  # from skill scripts/
    os.path.dirname(os.path.dirname(__file__)),  # fallback
]:
    normalized = os.path.normpath(os.path.abspath(path_offset))
    if os.path.exists(os.path.join(normalized, "utils", "client.py")):
        sys.path.insert(0, normalized)
        break

from utils.client import get_client, CUSTOMER_ID
from google.ads.googleads.errors import GoogleAdsException


# Negative keyword signals — search terms containing these patterns are likely irrelevant
NEGATIVE_SIGNALS = [
    # Food/recipe intent
    "foods with", "food high in", "rich foods", "recipe", "cooking",
    # Medical/clinical
    "dosage for", "side effects", "interactions", "overdose", "deficiency symptoms",
    "doctor", "prescription", "medication",
    # DIY/informational
    "how to make", "what is", "wiki", "definition", "vs ",
    # Wrong product
    "cream", "lotion", "spray", "powder bulk", "liquid",
    # Price sensitivity (often low-intent)
    "free sample", "coupon code", "discount code",
    # Geo leakage
    "uk", "canada", "australia", "india",
]


def pull_search_terms(days: int):
    """Pull search terms via GAQL."""
    client = get_client()
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            search_term_view.search_term,
            campaign.name,
            ad_group.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr
        FROM search_term_view
        WHERE segments.date DURING LAST_{days}_DAYS
          AND campaign.status = 'ENABLED'
        ORDER BY metrics.cost_micros DESC
    """

    response = ga_service.search(customer_id=CUSTOMER_ID, query=query)

    terms = []
    for row in response:
        terms.append({
            "term": row.search_term_view.search_term,
            "campaign": row.campaign.name,
            "ad_group": row.ad_group.name,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "cost": row.metrics.cost_micros / 1_000_000,
            "conversions": row.metrics.conversions,
            "ctr": row.metrics.ctr,
        })

    return terms


def has_negative_signal(term: str) -> bool:
    """Check if a search term matches known irrelevant patterns."""
    term_lower = term.lower()
    return any(signal in term_lower for signal in NEGATIVE_SIGNALS)


def categorize_terms(terms: list, min_clicks_negative: int = 3, min_conversions_promote: int = 2):
    """Categorize terms into promote, negative, and monitor buckets."""
    promote = []
    negative = []
    monitor = []

    for t in terms:
        if t["conversions"] >= min_conversions_promote:
            promote.append(t)
        elif t["clicks"] >= min_clicks_negative and has_negative_signal(t["term"]):
            negative.append(t)
        elif t["clicks"] >= min_clicks_negative and t["conversions"] == 0:
            # High clicks, zero conversions — flag for manual review
            negative.append(t)
        else:
            monitor.append(t)

    return promote, negative, monitor


def print_report(promote, negative, monitor):
    """Print categorized search term report."""
    print(f"\n{'='*70}")
    print("SEARCH TERM ANALYSIS")
    print(f"{'='*70}")

    if promote:
        print(f"\n--- PROMOTE TO EXACT MATCH ({len(promote)} terms) ---")
        print(f"{'Term':<45} {'Clicks':>6} {'Conv':>5} {'Cost':>8}")
        print("-" * 70)
        for t in sorted(promote, key=lambda x: x["conversions"], reverse=True):
            print(f"{t['term']:<45} {t['clicks']:>6} {t['conversions']:>5.0f} ${t['cost']:>7.2f}")

    if negative:
        print(f"\n--- ADD AS NEGATIVE ({len(negative)} terms) ---")
        print(f"{'Term':<45} {'Clicks':>6} {'Conv':>5} {'Cost':>8} {'Signal'}")
        print("-" * 70)
        for t in sorted(negative, key=lambda x: x["cost"], reverse=True):
            signal = "pattern" if has_negative_signal(t["term"]) else "no-conv"
            print(f"{t['term']:<45} {t['clicks']:>6} {t['conversions']:>5.0f} ${t['cost']:>7.2f}  {signal}")

    if monitor:
        print(f"\n--- MONITOR ({len(monitor)} terms) ---")
        print(f"{'Term':<45} {'Clicks':>6} {'Conv':>5} {'Cost':>8}")
        print("-" * 70)
        for t in sorted(monitor, key=lambda x: x["clicks"], reverse=True)[:20]:
            print(f"{t['term']:<45} {t['clicks']:>6} {t['conversions']:>5.0f} ${t['cost']:>7.2f}")
        if len(monitor) > 20:
            print(f"  ... and {len(monitor) - 20} more")

    # Summary
    total_cost = sum(t["cost"] for t in promote + negative + monitor)
    negative_cost = sum(t["cost"] for t in negative)
    print(f"\n{'='*70}")
    print(f"Total terms: {len(promote) + len(negative) + len(monitor)}")
    print(f"Total spend: ${total_cost:.2f}")
    print(f"Wasted spend (negative terms): ${negative_cost:.2f} ({negative_cost/total_cost*100:.1f}%)" if total_cost > 0 else "")
    print(f"{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(description="Search Term Analysis Report")
    parser.add_argument("--days", type=int, default=7, choices=[7, 14, 30],
                        help="Number of days to analyze (default: 7)")
    parser.add_argument("--min-clicks", type=int, default=3,
                        help="Minimum clicks to flag as negative (default: 3)")
    parser.add_argument("--min-conversions", type=int, default=2,
                        help="Minimum conversions to promote (default: 2)")
    args = parser.parse_args()

    try:
        print(f"Pulling search terms for last {args.days} days...")
        terms = pull_search_terms(args.days)

        if not terms:
            print("No search terms found for this period.")
            sys.exit(0)

        promote, negative, monitor = categorize_terms(
            terms,
            min_clicks_negative=args.min_clicks,
            min_conversions_promote=args.min_conversions,
        )

        print_report(promote, negative, monitor)

    except GoogleAdsException as ex:
        print(f"\nGoogle Ads API error (request ID: {ex.request_id}):")
        for error in ex.failure.errors:
            print(f"  [{error.error_code}] {error.message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
