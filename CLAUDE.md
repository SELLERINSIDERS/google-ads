# Google Ads Project — Claude Instructions

## Account
- **Client:** Evolance Wellness Inc
- **Customer ID:** `2436521562` (child account)
- **Manager (MCC):** `1637378856` (Evolance)
- **Currency:** USD | **Timezone:** America/New_York

## Environment
- Credentials live in `.env` — never commit, never log, never expose
- Always `load_dotenv()` before building the API client
- Python 3.9 is installed; upgrade warnings are non-blocking
- Library: `google-ads` (Python), installed at `~/Library/Python/3.9`

## API Rules
- **Read before write** — fetch current state before making any changes
- **Dry-run first** — validate logic with read-only queries before mutations
- **Never delete** — pause campaigns/ad groups/ads instead of removing
- Use `GAQL` (Google Ads Query Language) for all data fetching
- Always scope queries to `GOOGLE_ADS_CUSTOMER_ID` unless explicitly told otherwise

## Shared Knowledge
- Company rules, brand, and product context live in `shared/` (git submodule → `SELLERINSIDERS/shared-company-brain`)
- Read `shared/COMPANY-RULES.md`, `shared/KNOWLEDGE-BASE.md`, and `shared/USER.md` before making decisions
- To update: `git submodule update --remote shared && git add shared && git commit -m "Update shared brain"`

## File Structure
```
Google Ads/
├── .env                  # Credentials (gitignored)
├── .gitignore
├── .gitmodules
├── CLAUDE.md
├── test_connection.py    # Dry-run connection test
└── shared/               # Submodule: shared-company-brain
```

## Workflow
1. Read `.env` via `python-dotenv`
2. Build client with `GoogleAdsClient.load_from_dict()`
3. Test with `test_connection.py` after any credential change
4. Commit only non-sensitive files to `SELLERINSIDERS/google-ads`
