# Google Ads — Project Manifesto
_Last updated: 2026-03-09 | Session: Initial campaign setup — Calm+Rest Magnesium_

---

## Account
| Field | Value |
|---|---|
| Customer ID | `2436521562` |
| MCC (Login) | `1637378856` |
| Currency | USD |
| Timezone | America/New_York |
| Conversion actions | 14 active (Purchase, Shopping Cart, Contact Info, etc.) |

---

## API Runtime Notes
> Read this before writing any script. These are confirmed facts for this account.

- **Runtime:** `python3` (not `python`) — Python 3.9 at `~/Library/Python/3.9`
- **API version:** google-ads v23
- **Campaign creation:** `contains_eu_political_advertising = 3` is REQUIRED on every new campaign (`3` = `DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING`)
- **Budgets:** Always set `explicitly_shared = False` on non-shared campaign budgets (required for smart bidding compatibility)
- **Bidding — `maximize_conversions`:** Broken via API on this account (returns `REQUIRED` field error). Workaround: create campaign with `manual_cpc`, then switch to Maximize Conversions in the UI before enabling
- **Negative keyword linking:** Script 01 only links SharedSets to `ENABLED` campaigns. After creating a PAUSED campaign, link the SharedSet manually using `CampaignSharedSetService`
- **Debugging required fields:** Use `e.location.field_path_elements` to print the exact missing field path
- **Proto-plus pattern (oneof):** To set a oneof field without sub-fields: `campaign._pb.maximize_conversions.SetInParent()`
- **Micros:** $1 = `1_000_000` micros | $50 = `50_000_000` micros

---

## Shared Resources
| Name | Resource Name | Keywords | Linked Campaigns |
|---|---|---|---|
| Master Negatives — All Campaigns | `customers/2436521562/sharedSets/12001367914` | 988 | SR \| Calm+Rest \| Magnesium \| Broad |

**File:** `data/negative-keywords-master.txt`

---

## Campaigns

### SR | Calm+Rest | Magnesium | Broad
| Field | Value |
|---|---|
| Campaign resource | `customers/2436521562/campaigns/23642918848` |
| Budget resource | `customers/2436521562/campaignBudgets/15425567959` ($50/day) |
| **Status** | **PAUSED** |
| **Bidding** | **⚠️ Manual CPC — MUST switch to Maximize Conversions in UI before enabling** |
| Network | Search only (no display) |
| Ad Group | Broad — Magnesium Supplements (`customers/2436521562/adGroups/197903355790`) |
| Keywords | `best magnesium supplements`, `best magnesium for sleep` (Broad match) |
| RSA | `customers/2436521562/adGroupAds/197903355790~799649758483` (PAUSED) |
| Landing page | https://www.trustedselections.org/top-5-best-magnesium-2026 |
| UTM | `?utm_source=google&utm_medium=cpc&utm_campaign=calm-rest-magnesium-broad&utm_content=broad-magnesium-supplements&utm_term={keyword}` |
| Negatives | Master Negatives — All Campaigns ✓ |
| Created | 2026-03-09 |
| Script | `campaigns/calm-rest/02_create_campaign.py` |

---

## TODO — Next Actions (priority order)
- [ ] **BLOCKING:** Switch campaign bidding to Maximize Conversions in UI (Settings > Bidding)
- [ ] Enable campaign once bidding is switched
- [ ] After 7 days live: `python3 reports/performance.py --days 7`
- [ ] Pull search terms report → promote top queries to exact-match keywords
- [ ] Once 30+ conversions: consider adding target CPA
- [ ] Expand ad groups (exact match, phrase match) once broad data settles

---

## Scripts Reference
| Script | Purpose | Run |
|---|---|---|
| `test_connection.py` | Verify API credentials | `python3 test_connection.py` |
| `reports/performance.py` | Campaign metrics (7/14/30 days) | `python3 reports/performance.py --days 7` |
| `campaigns/calm-rest/01_negative_keywords.py` | Create + upload SharedSet | `python3 campaigns/calm-rest/01_negative_keywords.py` |
| `campaigns/calm-rest/02_create_campaign.py` | Create campaign structure | `python3 campaigns/calm-rest/02_create_campaign.py` |
| `campaigns/calm-rest/03_create_rsa.py` | Create RSA | `python3 campaigns/calm-rest/03_create_rsa.py` |

---

## Session Log
| Date | Summary |
|---|---|
| 2026-03-09 | First session. Created negative keyword list (988 kws), campaign "SR \| Calm+Rest \| Magnesium \| Broad" (PAUSED), RSA (PAUSED). Fixed 3 API v23 bugs: `contains_eu_political_advertising`, `explicitly_shared`, `maximize_conversions` workaround. All files committed to GitHub. |
