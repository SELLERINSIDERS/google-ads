# Google Ads — Project Manifesto
_Last updated: 2026-03-11 | Session: Performance analysis + conversion tracking audit_

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
| Master Negatives — All Campaigns | `customers/2436521562/sharedSets/12001367914` | 1067 | SR \| Calm+Rest \| Magnesium \| Broad |

**File:** `data/negative-keywords-master.txt`

---

## Campaigns

### SR | Calm+Rest | Magnesium | Broad
| Field | Value |
|---|---|
| Campaign resource | `customers/2436521562/campaigns/23642918848` |
| Budget resource | `customers/2436521562/campaignBudgets/15425567959` ($50/day) |
| **Status** | **ENABLED** |
| **Bidding** | **Maximize Conversions** (switched 2026-03-10) |
| Network | Search only (no display, no search partners) |
| Geo targeting | United States — PRESENCE only |
| Ad Group | Broad — Magnesium Supplements (`customers/2436521562/adGroups/197903355790`) |
| Keywords | `best magnesium supplements`, `best magnesium for sleep` (Broad match) |
| RSA v1 | `customers/2436521562/adGroupAds/197903355790~799649758483` (ENABLED, strength: POOR) |
| RSA v2 | `customers/2436521562/adGroupAds/197903355790~799897145409` (PAUSED — diverse headlines, pending review) |
| Landing page | https://www.trustedselections.org/top-5-best-magnesium-2026 |
| UTM | `?utm_source=google&utm_medium=cpc&utm_campaign=calm-rest-magnesium-broad&utm_content=broad-magnesium-supplements&utm_term={keyword}` |
| Negatives | Master Negatives — All Campaigns ✓ (1077 keywords) |
| Created | 2026-03-09 |
| Script | `campaigns/calm-rest/02_create_campaign.py` |

---

## TODO — Next Actions (priority order)
- [x] ~~Switch campaign bidding to Maximize Conversions in UI~~ (done 2026-03-10)
- [x] ~~Enable campaign~~ (done 2026-03-10)
- [ ] **P0 — Fix conversion tracking:** Add gtag.js to trustedselections.org + set up cross-domain tracking to Shopify. Purchase conversion action exists but never fires (0 conversions in 124 clicks).
- [ ] **P0 — Verify geo fix:** Check March 11-12 geographic data to confirm PRESENCE-only targeting is eliminating non-US traffic (March 10 was 81% non-US)
- [x] ~~**P1 — Add negative keywords:**~~ Added 10 new negatives (perimenopause, brainmax, magvion, cramping, night shift workers) to SharedSet (done 2026-03-11)
- [x] ~~**P1 — Create improved RSA:**~~ RSA v2 created with diverse headlines (PAUSED). Review and enable in UI, then pause RSA v1 (done 2026-03-11)
- [ ] **P2 — Consider Manual CPC:** Until conversion tracking is fixed, Maximize Conversions is optimizing blind
- [ ] After 7 days live: `python3 reports/daily_analysis.py`
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
| `reports/daily_analysis.py` | Full daily analysis (6 queries) | `python3 reports/daily_analysis.py` |

---

## Session Log
| Date | Summary |
|---|---|
| 2026-03-09 | First session. Created negative keyword list (988 kws), campaign "SR \| Calm+Rest \| Magnesium \| Broad" (PAUSED), RSA (PAUSED). Fixed 3 API v23 bugs: `contains_eu_political_advertising`, `explicitly_shared`, `maximize_conversions` workaround. All files committed to GitHub. |
| 2026-03-09 | Second session. Built workflow framework: MANIFESTO.md (this file), CLAUDE.md session protocol, MEMORY.md auto-loaded API patterns, SKILL.md v23 known issues. All committed to GitHub. |
| 2026-03-10 | Third session. Analyzed day-1 performance: 589 imp, 58 clicks, $50.16 spent, 0 conversions, 9.85% CTR. Fixed geo targeting from PRESENCE_OR_INTEREST → PRESENCE only. Added 79 new negative keywords (988→1067) to block foreign geo, food intent, medical conditions, informational queries. Saved default campaign rules: US-only, PRESENCE, no search partners, no AIMax. Updated campaign creation script. |
| 2026-03-10 | Fourth session. Major skill overhaul: rewrote `google-ads-scripts` skill from JavaScript AdsApp → Python google-ads API. Deleted 7 JS files, created 4 reference docs (python-api-patterns, campaign-creation-checklist, compliance-guardrails, optimization-playbook), 2 utility scripts (search_term_report.py, campaign_health_check.py). Ran 3 evals (campaign creation, search term analysis, compliance RSA) — skill scored 100% vs 95% baseline. Key skill value: character limit enforcement, compliance documentation, consistent v23 workarounds. Optimized skill description for auto-triggering on all Google Ads tasks. |
| 2026-03-11 | Fifth session. Full performance analysis (days 1-2). Key findings: (1) **Conversion tracking broken** — Purchase action exists but 0 fires in 124 clicks. Landing page (trustedselections.org) lacks gtag + no cross-domain tracking to Shopify. Google Ads ID: `AW-17196166864`, Purchase label: `m7fUCO3BxNkaENDd4odA`. (2) **81% non-US spend on March 10** — PRESENCE fix was mid-day, most budget already consumed under old PRESENCE_OR_INTEREST. Settings now confirmed correct. (3) CTR 9.8% excellent, CPC $0.81 good. (4) QS 5-6 below target. (5) RSA strength POOR. Actions taken: created `reports/daily_analysis.py`, added 10 new negatives (1067→1077), created RSA v2 with diverse headlines (PAUSED for review). |
