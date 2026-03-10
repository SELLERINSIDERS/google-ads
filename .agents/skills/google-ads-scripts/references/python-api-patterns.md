# Python Google Ads API Patterns

Reference for the `google-ads` Python library (v23) used in this project.

## Table of Contents
1. [Client Setup](#client-setup)
2. [GAQL Query Patterns](#gaql-query-patterns)
3. [Mutation Patterns](#mutation-patterns)
4. [Proto-plus Gotchas](#proto-plus-gotchas)
5. [Batch Operations](#batch-operations)
6. [Error Handling](#error-handling)
7. [Enum Reference](#enum-reference)
8. [Resource Name Construction](#resource-name-construction)

---

## Client Setup

Every script starts with:

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.client import get_client, CUSTOMER_ID
from google.ads.googleads.errors import GoogleAdsException
```

The client is built from `.env` via `python-dotenv` inside `utils/client.py`.

---

## GAQL Query Patterns

### Basic Query

```python
client = get_client()
ga_service = client.get_service("GoogleAdsService")

query = """
    SELECT campaign.name, campaign.status, metrics.clicks
    FROM campaign
    WHERE campaign.status != 'REMOVED'
"""
response = ga_service.search(customer_id=CUSTOMER_ID, query=query)

for row in response:
    print(f"{row.campaign.name}: {row.metrics.clicks} clicks")
```

### Date Filtering

```sql
-- Predefined ranges
WHERE segments.date DURING LAST_7_DAYS
WHERE segments.date DURING LAST_14_DAYS
WHERE segments.date DURING LAST_30_DAYS
WHERE segments.date DURING TODAY
WHERE segments.date DURING YESTERDAY

-- Custom range
WHERE segments.date BETWEEN '2026-01-01' AND '2026-01-31'
```

### Common Queries

**Campaign performance:**
```sql
SELECT campaign.name, campaign.status,
       metrics.impressions, metrics.clicks, metrics.ctr,
       metrics.average_cpc, metrics.cost_micros,
       metrics.conversions, metrics.cost_per_conversion
FROM campaign
WHERE segments.date DURING LAST_7_DAYS
  AND campaign.status != 'REMOVED'
ORDER BY metrics.cost_micros DESC
```

**Search terms:**
```sql
SELECT search_term_view.search_term,
       campaign.name, ad_group.name,
       metrics.impressions, metrics.clicks, metrics.cost_micros,
       metrics.conversions, metrics.ctr
FROM search_term_view
WHERE segments.date DURING LAST_7_DAYS
  AND campaign.status = 'ENABLED'
ORDER BY metrics.cost_micros DESC
```

**Keyword quality scores:**
```sql
SELECT ad_group_criterion.keyword.text,
       ad_group_criterion.keyword.match_type,
       ad_group_criterion.quality_info.quality_score,
       metrics.impressions, metrics.clicks, metrics.conversions,
       metrics.cost_micros
FROM keyword_view
WHERE campaign.status = 'ENABLED'
  AND ad_group_criterion.status = 'ENABLED'
  AND segments.date DURING LAST_30_DAYS
```

**Ad performance (RSA):**
```sql
SELECT ad_group_ad.ad.responsive_search_ad.headlines,
       ad_group_ad.ad.responsive_search_ad.descriptions,
       ad_group_ad.ad.final_urls,
       metrics.impressions, metrics.clicks, metrics.conversions
FROM ad_group_ad
WHERE campaign.status = 'ENABLED'
  AND ad_group_ad.status = 'ENABLED'
  AND segments.date DURING LAST_30_DAYS
```

**Geo performance (detect leakage):**
```sql
SELECT geographic_view.country_criterion_id,
       geographic_view.location_type,
       metrics.clicks, metrics.impressions, metrics.cost_micros
FROM geographic_view
WHERE segments.date DURING LAST_7_DAYS
  AND campaign.status = 'ENABLED'
ORDER BY metrics.cost_micros DESC
```

---

## Mutation Patterns

### Create a Single Entity

```python
service = client.get_service("CampaignService")
op = client.get_type("CampaignOperation")
campaign = op.create

campaign.name = "My Campaign"
campaign.status = client.enums.CampaignStatusEnum.PAUSED
# ... set other fields ...

response = service.mutate_campaigns(
    customer_id=CUSTOMER_ID, operations=[op]
)
resource_name = response.results[0].resource_name
```

### Update an Existing Entity

```python
from google.api_core import protobuf_helpers

op = client.get_type("CampaignOperation")
campaign = op.update
campaign.resource_name = "customers/2436521562/campaigns/12345"
campaign.status = client.enums.CampaignStatusEnum.PAUSED

# Tell the API which fields you're changing
client.copy_from(
    op.update_mask,
    protobuf_helpers.field_mask(None, campaign._pb)
)

response = service.mutate_campaigns(
    customer_id=CUSTOMER_ID, operations=[op]
)
```

### Create Multiple Entities (batch)

```python
operations = []
for kw_text in keywords:
    op = client.get_type("AdGroupCriterionOperation")
    criterion = op.create
    criterion.ad_group = ad_group_resource_name
    criterion.keyword.text = kw_text
    criterion.keyword.match_type = client.enums.KeywordMatchTypeEnum.BROAD
    operations.append(op)

# Send all at once
response = criterion_service.mutate_ad_group_criteria(
    customer_id=CUSTOMER_ID, operations=operations
)
```

For large batches (1000+ items), chunk into groups of 1000:

```python
BATCH_SIZE = 1000
for i in range(0, len(operations), BATCH_SIZE):
    batch = operations[i:i + BATCH_SIZE]
    service.mutate_shared_criteria(
        customer_id=CUSTOMER_ID, operations=batch
    )
```

---

## Proto-plus Gotchas

### Setting a oneof field with no sub-fields

```python
# maximize_conversions without a target CPA
campaign._pb.maximize_conversions.SetInParent()
```

### Accessing enum values

```python
# By name
status = client.enums.CampaignStatusEnum.PAUSED

# Debug: list all values for a field
field = type(campaign._pb).DESCRIPTOR.fields_by_name['contains_eu_political_advertising']
for v in field.enum_type.values:
    print(v.name, v.number)
```

### Appending to repeated fields

```python
# URLs
ad.final_urls.append("https://example.com")

# RSA headlines
headline = client.get_type("AdTextAsset")
headline.text = "My Headline"
rsa.headlines.append(headline)
```

### Pinning RSA headlines

```python
headline = client.get_type("AdTextAsset")
headline.text = "Best Magnesium of 2026"
headline.pinned_field = client.enums.ServedAssetFieldTypeEnum.HEADLINE_1
rsa.headlines.append(headline)
```

---

## Error Handling

### Standard Pattern

```python
try:
    response = service.mutate_campaigns(
        customer_id=CUSTOMER_ID, operations=[op]
    )
except GoogleAdsException as ex:
    print(f"Google Ads API error (request ID: {ex.request_id}):")
    for error in ex.failure.errors:
        print(f"  [{error.error_code}] {error.message}")
    sys.exit(1)
```

### Debugging Required Fields

When you get a `REQUIRED` field error, print the field path:

```python
except GoogleAdsException as ex:
    for error in ex.failure.errors:
        print(f"Error: {error.message}")
        for fp in error.location.field_path_elements:
            print(f"  field: {fp.field_name}")
```

### Pre-flight Checks

Always check if an entity exists before creating:

```python
def campaign_exists(ga_service, campaign_name):
    query = f"""
        SELECT campaign.name
        FROM campaign
        WHERE campaign.status != 'REMOVED'
    """
    response = ga_service.search(customer_id=CUSTOMER_ID, query=query)
    for row in response:
        if row.campaign.name == campaign_name:
            return True
    return False
```

---

## Enum Reference

### Campaign Status
```python
client.enums.CampaignStatusEnum.ENABLED
client.enums.CampaignStatusEnum.PAUSED
client.enums.CampaignStatusEnum.REMOVED
```

### Ad Group Status
```python
client.enums.AdGroupStatusEnum.ENABLED
client.enums.AdGroupStatusEnum.PAUSED
```

### Keyword Match Type
```python
client.enums.KeywordMatchTypeEnum.BROAD
client.enums.KeywordMatchTypeEnum.PHRASE
client.enums.KeywordMatchTypeEnum.EXACT
```

### Ad Status
```python
client.enums.AdGroupAdStatusEnum.ENABLED
client.enums.AdGroupAdStatusEnum.PAUSED
```

### Budget Delivery
```python
client.enums.BudgetDeliveryMethodEnum.STANDARD
```

### Geo Target Type
```python
client.enums.PositiveGeoTargetTypeEnum.PRESENCE
client.enums.PositiveGeoTargetTypeEnum.PRESENCE_OR_INTEREST  # DON'T use this
```

### Channel Type
```python
client.enums.AdvertisingChannelTypeEnum.SEARCH
```

---

## Resource Name Construction

Resource names follow a consistent pattern:

```
customers/{customer_id}/campaigns/{campaign_id}
customers/{customer_id}/campaignBudgets/{budget_id}
customers/{customer_id}/adGroups/{ad_group_id}
customers/{customer_id}/adGroupAds/{ad_group_id}~{ad_id}
customers/{customer_id}/sharedSets/{shared_set_id}
geoTargetConstants/{geo_id}          # 2840 = United States
```

Use the service helper to construct them:

```python
campaign_service = client.get_service("CampaignService")
resource_name = campaign_service.campaign_path(CUSTOMER_ID, campaign_id)
```

---

## Services Reference

| Service | Use For |
|---|---|
| `GoogleAdsService` | GAQL queries (read-only) |
| `CampaignBudgetService` | Create/update budgets |
| `CampaignService` | Create/update campaigns |
| `AdGroupService` | Create/update ad groups |
| `AdGroupCriterionService` | Keywords (positive) |
| `AdGroupAdService` | Create/update ads (RSA) |
| `SharedSetService` | Negative keyword lists |
| `SharedCriterionService` | Keywords in shared sets |
| `CampaignSharedSetService` | Link shared sets to campaigns |
| `CampaignCriterionService` | Campaign-level targeting (geo, etc.) |
