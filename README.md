# RFP Scout

Automated daily scanner for government and nonprofit software RFPs related to:

- Case management systems
- Licensing & certification platforms
- Permitting systems
- Workflow management / form processing
- Constituent/citizen portals
- Benefits administration
- Grants management

Runs every morning via GitHub Actions and emails you a digest of new opportunities via Resend.

---

## How It Works

```
Every morning at 7 AM ET
        │
        ├── Google Search (Serper.dev) ── 20 targeted queries
        ├── BidNet Direct ────────────── state/local government procurement
        ├── OpenGov Procurement ──────── municipal/county agencies
        └── SAM.gov (optional) ───────── federal opportunities
                │
                ▼
        Score each result (0–100)
        Drop anything below MIN_SCORE
        Remove already-seen opportunities
                │
                ▼
        Send HTML email digest via Resend
        Save seen URLs → commit back to repo
```

---

## Setup (one-time, ~15 minutes)

### Step 1 — Get API keys

**Serper.dev** (Google search — free, 2500 searches/month)
1. Go to [serper.dev](https://serper.dev)
2. Sign up → copy your API key from the dashboard

**Resend** (email sending)
1. You said you already have a key — keep it handy
2. You also need a verified sender email/domain in Resend
   - Easiest: verify a domain in your Resend dashboard
   - For quick testing: use `onboarding@resend.dev` as sender (Resend's test address)

**SAM.gov** (optional — federal opportunities)
1. Create an account at [sam.gov](https://sam.gov)
2. Go to your profile → Request API key
3. Free, but approval can take a day or two

---

### Step 2 — Push this repo to GitHub

```bash
cd ~/rfp-scanner
git init
git add .
git commit -m "Initial commit"
# Create a new PRIVATE repo on GitHub, then:
git remote add origin https://github.com/YOUR_USERNAME/rfp-scanner.git
git push -u origin main
```

> Make the repo **private** — your seen_urls.json will be committed there.

---

### Step 3 — Add GitHub Actions Secrets

Go to your repo on GitHub → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these secrets:

| Secret name       | Value                              | Required? |
|-------------------|------------------------------------|-----------|
| `SERPER_API_KEY`  | Your Serper.dev API key            | Yes       |
| `RESEND_API_KEY`  | Your Resend API key                | Yes       |
| `RECIPIENT_EMAIL` | Email to receive the daily digest  | Yes       |
| `SENDER_EMAIL`    | e.g. `RFP Scout <you@yourdomain.com>` | Yes (or use `onboarding@resend.dev`) |
| `SAM_API_KEY`     | SAM.gov API key                    | No        |

---

### Step 4 — Test it

Trigger a manual run:
1. Go to your repo → **Actions** tab
2. Click **Daily RFP Scan** in the left sidebar
3. Click **Run workflow** → **Run workflow**
4. Watch the logs — you should see results and receive an email

---

## Tuning

All keyword and query configuration is in **`config.py`**.

### Add keywords

Edit `REQUIRED_KEYWORDS` to add more domain phrases. An opportunity must match at least one.

```python
REQUIRED_KEYWORDS = [
    "case management",
    "your new phrase here",  # <-- add here
    ...
]
```

### Add search queries

Edit `SEARCH_QUERIES` to add more Google search queries. Use Google search syntax — quotes, `site:`, `OR`, etc.

```python
SEARCH_QUERIES = [
    '"request for proposal" "case management" software',
    '"request for proposal" "your domain" software',  # <-- add here
]
```

### Change the schedule

Edit `.github/workflows/daily_scan.yml`:

```yaml
schedule:
  - cron: "0 12 * * *"   # 12:00 UTC = 7 AM ET
  # Change to: "0 14 * * *" for 9 AM ET, "0 13 * * *" for 8 AM ET, etc.
```

### Change the minimum relevance score

Edit `MIN_SCORE` in `config.py` (default: 35).
- Higher = fewer, more relevant results
- Lower = more results, more noise

---

## Project Structure

```
rfp-scanner/
├── main.py            — Entry point, orchestrates everything
├── config.py          — Keywords, queries, and thresholds (edit this!)
├── sources.py         — Data source scrapers (Serper, BidNet, SAM.gov, OpenGov)
├── filters.py         — Relevance scoring and deduplication
├── email_digest.py    — HTML email builder and Resend sender
├── requirements.txt   — Python dependencies
├── data/
│   └── seen_urls.json — Tracks seen opportunities (auto-managed)
└── .github/
    └── workflows/
        └── daily_scan.yml — GitHub Actions schedule
```

---

## Sources Covered

| Source | Coverage | Key |
|--------|----------|-----|
| **Google Search** (via Serper) | Everything Google indexes — state sites, PDFs, news, agency portals | Serper API key |
| **BidNet Direct** | Used by hundreds of state/local government agencies | None (public) |
| **OpenGov** | Municipal and county procurement | None (public) |
| **SAM.gov** | Federal opportunities (DoD, HHS, VA, etc.) | SAM API key (optional) |

---

## Running Locally

```bash
cd ~/rfp-scanner
pip install -r requirements.txt

export SERPER_API_KEY=your_key_here
export RESEND_API_KEY=your_key_here
export RECIPIENT_EMAIL=you@example.com
export SENDER_EMAIL="RFP Scout <you@yourdomain.com>"

python main.py
```
