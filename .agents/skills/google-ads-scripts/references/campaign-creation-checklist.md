# Campaign Creation Checklist

Use this checklist every time you create a new campaign. Each step maps to a script in `campaigns/<product>/`.

---

## Pre-Creation

- [ ] Read `MANIFESTO.md` for current campaign state and resource IDs
- [ ] Identify product, theme, match type for the campaign
- [ ] Choose landing page URL (must be live and verified)
- [ ] Draft keywords (2-5 seed keywords for broad match)
- [ ] Draft ad copy — check against compliance guardrails
- [ ] Verify negative keyword list is current (`data/negative-keywords-master.txt`)

---

## Step 1: Negative Keywords (`01_negative_keywords.py`)

Only needed once per account (shared across campaigns). If SharedSet already exists, skip to Step 2.

- [ ] Load keywords from `data/negative-keywords-master.txt`
- [ ] Create SharedSet with name `Master Negatives — All Campaigns`
- [ ] Upload keywords in batches of 1000
- [ ] Link to all ENABLED campaigns
- [ ] **Note:** PAUSED campaigns need manual linking after creation

**Resource to record:** SharedSet resource name

---

## Step 2: Campaign Structure (`02_create_campaign.py`)

Creates budget, campaign, ad group, and keywords in one script.

### Budget
- [ ] Set `budget.name` following convention: `{Product} {Theme} — ${amount}/day`
- [ ] Set `budget.amount_micros` (remember: $50 = `50_000_000`)
- [ ] Set `budget.delivery_method = STANDARD`
- [ ] Set `budget.explicitly_shared = False` (REQUIRED for smart bidding)

### Campaign
- [ ] Set `campaign.name` following convention: `SR | {Product} | {Theme} | {Match Type}`
- [ ] Set `campaign.status = PAUSED`
- [ ] Set `campaign.advertising_channel_type = SEARCH`
- [ ] Set `campaign.campaign_budget = budget_resource_name`
- [ ] Set `campaign.contains_eu_political_advertising = 3` (REQUIRED)
- [ ] Set `campaign.manual_cpc.enhanced_cpc_enabled = False`
- [ ] Set `network_settings.target_google_search = True`
- [ ] Set `network_settings.target_search_network = False`
- [ ] Set `network_settings.target_content_network = False`
- [ ] Set `geo_target_type_setting.positive_geo_target_type = PRESENCE`
- [ ] Pre-flight check: verify campaign name doesn't already exist

### Ad Group
- [ ] Set `ad_group.name` following convention: `{Match Type} — {Theme}`
- [ ] Set `ad_group.status = ENABLED`
- [ ] Set `ad_group.type_ = SEARCH_STANDARD`
- [ ] Set `ad_group.cpc_bid_micros` (default: `1_000_000` = $1.00)

### Keywords
- [ ] Set match type (BROAD for initial launch)
- [ ] Set `final_urls` with full UTM parameters
- [ ] 2-5 seed keywords per ad group

**Resources to record:** Campaign, Budget, Ad Group resource names

---

## Step 3: RSA (`03_create_rsa.py`)

- [ ] Look up ad group resource name from Step 2
- [ ] Create 15 headlines (30 chars max each)
  - [ ] Pin Position 1: brand/keyword headline
  - [ ] Pin Position 2: strongest benefit headline
  - [ ] Leave remaining 13 unpinned
- [ ] Create 4 descriptions (90 chars max each)
- [ ] Set `final_urls` with full UTM parameters
- [ ] Set ad status:
  - New campaign (PAUSED): ad status = ENABLED
  - Existing ENABLED campaign: ad status = PAUSED
- [ ] Compliance check all copy against guardrails

---

## Step 4: Link Negatives (manual if campaign was PAUSED)

If the campaign was created as PAUSED (standard), the `01_negative_keywords.py` script won't have linked it. Link manually:

```python
css_service = client.get_service("CampaignSharedSetService")
op = client.get_type("CampaignSharedSetOperation")
op.create.campaign = campaign_resource_name
op.create.shared_set = shared_set_resource_name
css_service.mutate_campaign_shared_sets(
    customer_id=CUSTOMER_ID, operations=[op]
)
```

---

## Step 5: Review & Enable

- [ ] Verify all settings in Google Ads UI
- [ ] Switch bidding from Manual CPC to Maximize Conversions (in UI)
- [ ] Review ad preview
- [ ] Enable campaign
- [ ] Update `MANIFESTO.md` with new resource names and status

---

## Post-Launch Monitoring

| Timeframe | Action |
|---|---|
| Day 1 | Check impressions are flowing, geo targeting correct |
| Day 3 | Review search terms, add obvious negatives |
| Day 7 | `python3 reports/performance.py --days 7` — check CTR, CPC, spend |
| Day 14 | Full search term review, consider keyword expansion |
| Day 30 | Evaluate conversions, consider target CPA if 30+ conversions |

---

## Geo Targeting Setup

US-only targeting with PRESENCE:

```python
# Add US geo target to campaign
geo_service = client.get_service("CampaignCriterionService")
op = client.get_type("CampaignCriterionOperation")
criterion = op.create
criterion.campaign = campaign_resource_name
criterion.location.geo_target_constant = "geoTargetConstants/2840"  # United States
geo_service.mutate_campaign_criteria(
    customer_id=CUSTOMER_ID, operations=[op]
)
```

Note: The `PRESENCE` setting is on the campaign itself (via `geo_target_type_setting`), not on the criterion.
