---
name: google-ads-scripts
description: Expert guidance for managing Google Ads campaigns via the Python google-ads API (v23). Use this skill for ANY Google Ads task — campaign creation, performance reports, search term analysis, negative keywords, ad copy writing, bid strategy changes, budget decisions, geo targeting checks, or campaign health audits. Trigger whenever the user mentions campaigns, ads, keywords, conversions, CPA, ROAS, CTR, impressions, clicks, ad groups, RSAs, headlines, descriptions, search partners, bidding strategies, shared sets, or any Google Ads metric or entity. Also trigger for ad copy compliance, supplement advertising rules, GAQL queries, or proto-plus patterns. This is the go-to skill for anything related to Google Ads management, optimization, or reporting — even if the user doesn't explicitly say "Google Ads" but is clearly talking about paid search campaigns, ad performance, or keyword management.
---

# Google Ads Manager — Python API

This skill covers everything needed to manage Google Ads campaigns for Evolance Wellness using the Python `google-ads` library (v23). It is the single source of truth for campaign creation, ad copy, optimization, and compliance.

Before writing any script, read the account-specific gotchas below. They will save you hours of debugging.

---

## Account Reference

| Field | Value |
|---|---|
| Customer ID | `2436521562` |
| MCC (Login) | `1637378856` |
| Currency | USD |
| Timezone | America/New_York |
| Python runtime | `python3` (Python 3.9) |
| API version | google-ads v23 |
| Client import | `from utils.client import get_client, CUSTOMER_ID` |

Current campaign state and resource IDs live in `MANIFESTO.md` at the project root. Read it before every session.

---

## API v23 Known Issues

These are confirmed bugs/requirements for this account. Every script must handle them.

| Issue | Fix |
|---|---|
| `contains_eu_political_advertising` REQUIRED | Set `= 3` (`DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING`) on every `CampaignOperation.create` |
| Shared budget breaks smart bidding | Set `budget.explicitly_shared = False` on every `CampaignBudget` |
| `maximize_conversions` returns REQUIRED error | Create campaign with `manual_cpc`, then switch to Maximize Conversions in UI before enabling |
| `python` not found | Always use `python3` |
| SharedSet doesn't link to PAUSED campaigns | After creating PAUSED campaign, call `CampaignSharedSetService` manually to link |
| Debug missing field | Print `e.location.field_path_elements` from `GoogleAdsException` to find exact field |

**Proto-plus oneof pattern (no sub-fields):**
```python
campaign._pb.maximize_conversions.SetInParent()  # activates oneof without setting target CPA
```

---

## Default Campaign Settings

Apply these to every new campaign unless explicitly told otherwise.

| Setting | Value | Why |
|---|---|---|
| Campaign status | `PAUSED` | Review before going live |
| Ad status (new campaign) | `ENABLED` | Ready to serve when campaign turns on |
| Ad status (existing ENABLED campaign) | `PAUSED` | Don't go live until reviewed |
| Geo targeting | United States only (`geoTargetConstants/2840`) | We only sell in the US |
| Location options | `PRESENCE` only (not `PRESENCE_OR_INTEREST`) | Prevents ads showing to users outside US |
| Search partners | OFF (`target_search_network = False`) | Lower quality traffic |
| Display network | OFF (`target_content_network = False`) | Search only |
| AIMax / Final URL expansion | OFF | We control ad copy and landing pages |
| Target CPA | Don't add until 30+ conversions | Google needs data to optimize |

---

## Campaign Creation Workflow

Every new campaign follows this exact sequence. Each step is a separate script in `campaigns/<product>/`.

```
Step 1: Negative keywords  →  01_negative_keywords.py
Step 2: Campaign structure  →  02_create_campaign.py  (budget + campaign + ad group + keywords)
Step 3: RSA                →  03_create_rsa.py
Step 4: Link negatives     →  Manual link if campaign was PAUSED at creation
Step 5: Review & enable    →  Switch bidding in UI, then enable campaign
```

### Naming Conventions

| Entity | Pattern | Example |
|---|---|---|
| Campaign | `SR \| Product \| Theme \| Match Type` | `SR \| Calm+Rest \| Magnesium \| Broad` |
| Ad Group | `Match Type — Theme` | `Broad — Magnesium Supplements` |
| Budget | `Product Theme — $X/day` | `Calm+Rest Magnesium — $50/day` |

### UTM Convention

```
?utm_source=google&utm_medium=cpc&utm_campaign={campaign-slug}&utm_content={ad-group-slug}&utm_term={keyword}
```

See [references/campaign-creation-checklist.md](references/campaign-creation-checklist.md) for the full pre-launch checklist.

---

## Ad Copy — Compliance Rules

Evolance sells dietary supplements. All ad copy must pass FDA/FTC compliance. This is non-negotiable (Tier 0 company rule). Non-compliant copy has previously nearly gotten the ad account banned.

### Quick Reference

**Never say:** "cures", "treats", "prevents", "diagnoses", "improves sleep quality", "reduces anxiety", "anti-inflammatory", "scientifically proven" (without citation), "guaranteed results"

**Always say:** "supports", "may help", "promotes", "helps maintain", "formulated with clinically studied ingredients"

### Character Limits (RSA)

| Field | Max Length | Count |
|---|---|---|
| Headline | 30 characters | Up to 15 |
| Description | 90 characters | Up to 4 |
| Path 1/2 | 15 characters each | 1 each |

### Pinning Strategy
- Pin brand/keyword headline to Position 1
- Pin strongest benefit headline to Position 2
- Leave remaining headlines unpinned for Google to optimize

See [references/compliance-guardrails.md](references/compliance-guardrails.md) for the full compliance table with safe vs. prohibited language for each claim category.

---

## Performance Analysis

### Pulling Reports

```python
# Basic campaign performance (from reports/performance.py)
python3 reports/performance.py --days 7    # 7, 14, or 30
```

### Key GAQL Queries

```sql
-- Campaign performance
SELECT campaign.name, campaign.status,
       metrics.impressions, metrics.clicks, metrics.ctr,
       metrics.average_cpc, metrics.cost_micros,
       metrics.conversions, metrics.cost_per_conversion
FROM campaign
WHERE segments.date DURING LAST_7_DAYS
  AND campaign.status != 'REMOVED'
ORDER BY metrics.cost_micros DESC

-- Search terms (for mining new keywords / negatives)
SELECT search_term_view.search_term,
       campaign.name, ad_group.name,
       metrics.impressions, metrics.clicks, metrics.cost_micros,
       metrics.conversions, metrics.ctr
FROM search_term_view
WHERE segments.date DURING LAST_7_DAYS
  AND campaign.status = 'ENABLED'
ORDER BY metrics.cost_micros DESC

-- Keyword performance with quality score
SELECT ad_group_criterion.keyword.text,
       ad_group_criterion.keyword.match_type,
       ad_group_criterion.quality_info.quality_score,
       metrics.impressions, metrics.clicks, metrics.conversions,
       metrics.cost_micros, metrics.average_cpc
FROM keyword_view
WHERE campaign.status = 'ENABLED'
  AND ad_group_criterion.status = 'ENABLED'
  AND segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
```

See [references/optimization-playbook.md](references/optimization-playbook.md) for the full search term mining workflow and keyword expansion strategy.

---

## Optimization Decision Framework

### When to Act (Minimum Data Thresholds)

| Decision | Minimum Data Needed |
|---|---|
| Pause a keyword | 100+ clicks, 0 conversions |
| Add negative keyword | 3+ clicks on irrelevant search term |
| Promote search term to keyword | 2+ conversions from same term |
| Adjust bids | 30+ clicks on a keyword |
| Add target CPA | 30+ total conversions in campaign |
| Expand to new ad groups | 14+ days of data, clear theme clusters |

### Micros Conversion

| USD | Micros |
|---|---|
| $0.01 | 10,000 |
| $1 | 1,000,000 |
| $10 | 10,000,000 |
| $50 | 50,000,000 |

---

## Python API Patterns

The `google-ads` Python library uses proto-plus objects and GAQL for queries. Common patterns:

```python
# Standard script setup
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.client import get_client, CUSTOMER_ID
from google.ads.googleads.errors import GoogleAdsException

# GAQL query pattern
client = get_client()
ga_service = client.get_service("GoogleAdsService")
response = ga_service.search(customer_id=CUSTOMER_ID, query=query)

# Mutation pattern
service = client.get_service("CampaignService")
op = client.get_type("CampaignOperation")
campaign = op.create
# ... set fields ...
response = service.mutate_campaigns(customer_id=CUSTOMER_ID, operations=[op])

# Error handling
except GoogleAdsException as ex:
    for error in ex.failure.errors:
        print(f"[{error.error_code}] {error.message}")
        for fp in error.location.field_path_elements:
            print(f"  field: {fp.field_name}")
```

See [references/python-api-patterns.md](references/python-api-patterns.md) for comprehensive API patterns including batch operations, enum handling, and resource name construction.

---

## Scripts Reference

### Bundled Scripts (in this skill)

| Script | Purpose |
|---|---|
| `scripts/search_term_report.py` | Pull search terms, categorize as promote/negative/monitor |
| `scripts/campaign_health_check.py` | Audit campaign settings against defaults |

### Project Scripts

| Script | Purpose | Run |
|---|---|---|
| `reports/performance.py` | Campaign metrics | `python3 reports/performance.py --days 7` |
| `campaigns/*/01_negative_keywords.py` | SharedSet creation | Per-campaign |
| `campaigns/*/02_create_campaign.py` | Full campaign structure | Per-campaign |
| `campaigns/*/03_create_rsa.py` | RSA creation | Per-campaign |

---

## References

Load these on demand for detailed documentation:

- [references/python-api-patterns.md](references/python-api-patterns.md) — GAQL patterns, proto-plus gotchas, batch operations, enum handling
- [references/campaign-creation-checklist.md](references/campaign-creation-checklist.md) — Step-by-step pre-launch checklist for new campaigns
- [references/compliance-guardrails.md](references/compliance-guardrails.md) — Full compliance table: safe vs. prohibited language by claim category
- [references/optimization-playbook.md](references/optimization-playbook.md) — Search term mining, keyword expansion, bid optimization, budget allocation
