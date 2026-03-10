# Optimization Playbook

Strategies for improving campaign performance over time. Follow these in order of priority — search term mining first, then keyword expansion, then bid/budget optimization.

---

## 1. Search Term Mining

The single highest-ROI optimization activity. Pull search terms weekly.

### Workflow

1. **Pull the report** using `scripts/search_term_report.py` or GAQL:
   ```sql
   SELECT search_term_view.search_term,
          campaign.name, ad_group.name,
          metrics.impressions, metrics.clicks,
          metrics.cost_micros, metrics.conversions, metrics.ctr
   FROM search_term_view
   WHERE segments.date DURING LAST_7_DAYS
     AND campaign.status = 'ENABLED'
   ORDER BY metrics.cost_micros DESC
   ```

2. **Categorize each term** into one of three buckets:

   | Category | Criteria | Action |
   |---|---|---|
   | **Promote** | 2+ conversions, relevant intent | Add as exact-match keyword in targeted ad group |
   | **Negative** | 3+ clicks, irrelevant or non-commercial intent | Add to `data/negative-keywords-master.txt` and SharedSet |
   | **Monitor** | Too little data to decide, or ambiguous intent | Review next week |

3. **Common negative keyword categories** for supplement campaigns:
   - **Geo leakage:** country names, foreign languages, "near me" + non-US
   - **Food/recipe intent:** "foods with magnesium", "magnesium rich foods"
   - **Medical/clinical intent:** "magnesium dosage for [condition]", "doctor recommended"
   - **DIY/informational:** "how to make", "what is", "side effects of"
   - **Wrong product:** other brands, unrelated supplements
   - **Price sensitivity:** "free", "cheap", "coupon", "discount"

4. **After adding negatives:**
   - Update `data/negative-keywords-master.txt`
   - Upload to SharedSet via API or run script

---

## 2. Keyword Expansion

After 14+ days of broad match data, you'll see clear theme clusters. Expand into exact and phrase match ad groups.

### Strategy

```
Campaign: SR | Calm+Rest | Magnesium | Broad
  └── Ad Group: Broad — Magnesium Supplements
       Keywords: best magnesium supplements (broad)

Campaign: SR | Calm+Rest | Magnesium | Exact  (new)
  └── Ad Group: Exact — Top Performers
       Keywords: [best magnesium for sleep] (exact)
                 [magnesium supplement for anxiety] (exact)  ← from search terms
```

### When to Expand

| Signal | Action |
|---|---|
| Search term has 2+ conversions | Promote to exact match in dedicated ad group |
| Clear theme cluster (5+ related terms) | Create new ad group with theme-specific keywords |
| Broad match is spending on too many irrelevant terms | Tighten with phrase match ad group |

### Exact Match Ad Group Creation

Same campaign creation flow, but:
- Ad group name: `Exact — {Theme}`
- Keywords: exact match (`KeywordMatchTypeEnum.EXACT`)
- Higher CPC bid (exact match = higher intent = worth more)
- Tailored RSA headlines matching the exact queries

---

## 3. Bid Optimization

Only meaningful after sufficient data. Don't touch bids in the first 7 days.

### Decision Thresholds

| Situation | Threshold | Action |
|---|---|---|
| Keyword has clicks but no conversions | 100+ clicks, $0 conversions | Pause keyword |
| Keyword converting well | CPA below target | Increase bid 10% |
| Keyword converting poorly | CPA 2x+ above target | Decrease bid 15% |
| Quality score below 5 | QS < 5, high spend | Review landing page relevance, ad copy match |

### Bidding Strategy Progression

```
Launch:       Manual CPC (API limitation workaround)
Day 0-1:      Switch to Maximize Conversions in UI
Day 30+:      If 30+ conversions, consider adding Target CPA
Day 60+:      If stable ROAS, consider Target ROAS
```

Important: Never add Target CPA or Target ROAS before 30 conversions. Google needs historical data to optimize.

---

## 4. Budget Optimization

### Daily Budget Signals

| Signal | Action |
|---|---|
| Campaign limited by budget + good ROAS | Increase daily budget 20% |
| Campaign spending full budget, poor ROAS | Reduce budget 20% or pause |
| Campaign not spending budget | Check impression share, keywords may need expansion |

### Budget Reallocation

If running multiple campaigns, shift budget toward the best performer:

```
Before:  Campaign A: $50/day (ROAS 1.5)  |  Campaign B: $50/day (ROAS 4.0)
After:   Campaign A: $30/day             |  Campaign B: $70/day
```

---

## 5. Ad Copy Testing

### When to Test

- After 1000+ impressions on current RSA
- When CTR is below 5% for supplement keywords
- When ad strength is "Average" or below

### A/B Testing Approach

1. Create a second RSA in the same ad group (PAUSED)
2. Differentiate the test:
   - Different value proposition in pinned headlines
   - Different CTA in descriptions
   - Different social proof angle
3. Pause the current RSA, enable the test RSA
4. Run for 14 days minimum (or 1000+ impressions)
5. Compare CTR and conversion rate
6. Keep the winner, iterate on the loser's approach

### Headlines to Test (Calm+Rest)

| Angle | Example Headlines |
|---|---|
| Ingredient-led | "Affron Saffron + Magnesium" |
| Benefit-led | "Calm Days, Restful Nights" |
| Social proof | "#1 Rated Sleep Formula 2026" |
| Price/value | "Replaces 3 Supplements" |
| Risk reversal | "90-Day Money-Back Guarantee" |
| Differentiator | "Melatonin-Free Sleep Support" |

---

## 6. Weekly Optimization Routine

A consistent weekly rhythm prevents small problems from becoming expensive ones.

### Monday: Search Term Review
- Pull last 7 days of search terms
- Add negatives, promote winners
- Update `data/negative-keywords-master.txt`

### Wednesday: Performance Check
- Run `python3 reports/performance.py --days 7`
- Check: impressions trending, CPC stable, conversions happening
- Flag any anomalies (sudden spend spike, CTR drop)

### Friday: Strategic Review
- Compare week-over-week metrics
- Decide on any bid/budget changes for next week
- Plan keyword expansion if data supports it
- Update `MANIFESTO.md` with any changes

---

## 7. Geographic Performance Audit

Run monthly to catch geo leakage:

```sql
SELECT geographic_view.country_criterion_id,
       geographic_view.location_type,
       metrics.clicks, metrics.impressions,
       metrics.cost_micros, metrics.conversions
FROM geographic_view
WHERE segments.date DURING LAST_30_DAYS
  AND campaign.status = 'ENABLED'
ORDER BY metrics.cost_micros DESC
```

If you see clicks from outside the US (country_criterion_id != 2840), verify:
1. Campaign geo targeting is US-only
2. Location options are PRESENCE (not PRESENCE_OR_INTEREST)
3. Add geo-specific negative keywords if needed

---

## Metrics Reference

| Metric | Good Range (Supplements) | Action if Below |
|---|---|---|
| CTR | 5-12% | Review ad copy relevance, keyword match |
| CPC | $0.50-$3.00 | Normal for supplement keywords |
| Conversion Rate | 2-5% | Review landing page, offer |
| Quality Score | 7+ | Improve ad relevance, landing page |
| Impression Share | 50%+ | Increase budget or bids |
| CPA | Varies by product | Add Target CPA after 30 conversions |
