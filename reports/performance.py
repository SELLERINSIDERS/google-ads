"""
Pull campaign performance report: impressions, clicks, cost, conversions.
Usage: python reports/performance.py --days 7
"""

import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.client import get_client, CUSTOMER_ID

def get_performance(days: int = 7):
    client = get_client()
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            campaign.name,
            campaign.status,
            metrics.impressions,
            metrics.clicks,
            metrics.ctr,
            metrics.average_cpc,
            metrics.cost_micros,
            metrics.conversions,
            metrics.cost_per_conversion
        FROM campaign
        WHERE segments.date DURING LAST_{days}_DAYS
          AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """

    print(f"\n📊 Campaign Performance — Last {days} Days\n{'─'*60}")
    response = client.get_service("GoogleAdsService").search(
        customer_id=CUSTOMER_ID, query=query
    )

    for row in response:
        c = row.campaign
        m = row.metrics
        cost = m.cost_micros / 1_000_000
        print(f"\n{c.name} [{c.status.name}]")
        print(f"  Impressions:  {m.impressions:,}")
        print(f"  Clicks:       {m.clicks:,}  (CTR: {m.ctr:.2%})")
        print(f"  Cost:         ${cost:.2f}  (Avg CPC: ${m.average_cpc/1_000_000:.2f})")
        print(f"  Conversions:  {m.conversions:.1f}  (CPA: ${m.cost_per_conversion/1_000_000:.2f})")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=7, choices=[7, 14, 30])
    args = parser.parse_args()
    get_performance(args.days)
