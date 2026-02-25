#!/usr/bin/env python3
"""
RFP Scanner — main entry point.

Run manually:
  python main.py

Or via GitHub Actions (see .github/workflows/daily_scan.yml).

Required environment variables (set as GitHub Actions secrets):
  RESEND_API_KEY    — Resend API key (https://resend.com)
  RECIPIENT_EMAIL   — Where to send the daily digest
  SERPER_API_KEY    — Serper.dev API key (https://serper.dev), free 2500/mo

Optional:
  SENDER_EMAIL      — From address (default: onboarding@resend.dev for testing)
  SAM_API_KEY       — SAM.gov API key for federal opportunities
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

from config import (
    REQUIRED_KEYWORDS,
    SEARCH_QUERIES,
    BIDNET_KEYWORDS,
    SAM_KEYWORDS,
    USASPENDING_KEYWORDS,
    INFOR_PORTALS,
    MIN_SCORE,
    LOOKBACK_DAYS,
)
from sources import (
    search_google,
    search_bidnet,
    search_sam_gov,
    search_opengov,
    search_tennessee,
    search_infor_portal,
    search_usaspending,
)
from filters import score_opportunity, deduplicate
from email_digest import send_digest

SEEN_FILE = Path("data/seen_urls.json")


# ---------------------------------------------------------------------------
# Seen-URL persistence (prevents re-sending the same opportunity twice)
# ---------------------------------------------------------------------------
def load_seen_urls() -> set:
    if SEEN_FILE.exists():
        try:
            with open(SEEN_FILE) as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_seen_urls(urls: set) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(urls), f, indent=2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print(f"\n{'='*55}")
    print(f"  RFP Scanner — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}\n")

    seen_urls    = load_seen_urls()
    all_raw: list  = []   # standard RFP results — go through scorer
    pre_scored: list = [] # results with score already set (e.g. USASpending)

    # ── 1. Google Search (Serper.dev) ──────────────────────────────────────
    serper_key = os.environ.get("SERPER_API_KEY")
    if serper_key:
        print(f"[1/7] Google Search ({len(SEARCH_QUERIES)} queries via Serper.dev)…")
        for query in SEARCH_QUERIES:
            results = search_google(query, serper_key, lookback_days=LOOKBACK_DAYS)
            all_raw.extend(results)
            if results:
                print(f"      ✓ {len(results):>3} results  |  {query[:60]}")
    else:
        print("[1/7] Skipping Google Search (SERPER_API_KEY not set)")

    # ── 2. BidNet Direct ───────────────────────────────────────────────────
    print(f"\n[2/7] BidNet Direct ({len(BIDNET_KEYWORDS)} keywords)…")
    for keyword in BIDNET_KEYWORDS:
        results = search_bidnet(keyword)
        all_raw.extend(results)
        if results:
            print(f"      ✓ {len(results):>3} results  |  {keyword}")

    # ── 3. OpenGov ─────────────────────────────────────────────────────────
    print(f"\n[3/7] OpenGov Procurement…")
    og_results = search_opengov(BIDNET_KEYWORDS)
    all_raw.extend(og_results)
    print(f"      ✓ {len(og_results)} results total")

    # ── 4. SAM.gov (optional) ─────────────────────────────────────────────
    sam_key = os.environ.get("SAM_API_KEY")
    if sam_key:
        print(f"\n[4/7] SAM.gov ({len(SAM_KEYWORDS)} keywords)…")
        results = search_sam_gov(sam_key, SAM_KEYWORDS, lookback_days=LOOKBACK_DAYS)
        all_raw.extend(results)
        print(f"      ✓ {len(results)} results total")
    else:
        print("\n[4/7] Skipping SAM.gov (SAM_API_KEY not set — optional)")

    # ── 5. Tennessee Procurement (static HTML table) ───────────────────────
    print(f"\n[5/7] Tennessee Procurement…")
    tn_results = search_tennessee(REQUIRED_KEYWORDS)
    all_raw.extend(tn_results)
    print(f"      ✓ {len(tn_results)} results total")

    # ── 6. Infor/BuySpeed State Portals ───────────────────────────────────
    print(f"\n[6/7] Infor State Portals ({len(INFOR_PORTALS)} states)…")
    for state_name, base_url in INFOR_PORTALS.items():
        results = search_infor_portal(base_url, state_name, REQUIRED_KEYWORDS)
        all_raw.extend(results)
        if results:
            print(f"      ✓ {len(results):>3} results  |  {state_name}")

    # ── 7. USASpending.gov — Expiring Federal Contracts ───────────────────
    print(f"\n[7/7] USASpending.gov ({len(USASPENDING_KEYWORDS)} keywords)…")
    us_results = search_usaspending(USASPENDING_KEYWORDS)
    # Filter out already-seen contracts
    for opp in us_results:
        url_key = opp["url"].split("?")[0].split("#")[0].rstrip("/").lower()
        if url_key not in seen_urls:
            pre_scored.append(opp)
    print(f"      ✓ {len(pre_scored)} new expiring contracts found")

    # ── Deduplicate ────────────────────────────────────────────────────────
    print(f"\n  Raw results   : {len(all_raw)}")
    deduped = deduplicate(all_raw)
    print(f"  After dedup   : {len(deduped)}")

    # ── Score & filter ─────────────────────────────────────────────────────
    scored = []
    for opp in deduped:
        opp["score"] = score_opportunity(opp)
        url_key = opp["url"].split("?")[0].split("#")[0].rstrip("/").lower()

        if opp["score"] >= MIN_SCORE and url_key not in seen_urls:
            scored.append(opp)

    scored.sort(key=lambda x: x["score"], reverse=True)
    print(f"  New & relevant: {len(scored)}")
    print(f"  Expiring contracts: {len(pre_scored)}")

    # ── Update seen-URL store ──────────────────────────────────────────────
    for opp in scored + pre_scored:
        seen_urls.add(opp["url"].split("?")[0].split("#")[0].rstrip("/").lower())
    save_seen_urls(seen_urls)

    # ── Preview top results in console ────────────────────────────────────
    if scored:
        print(f"\n  Top opportunities:")
        for opp in scored[:10]:
            print(f"    [{opp['score']:>3}] {opp['title'][:65]}")
            print(f"          {opp['url'][:80]}")

    if pre_scored:
        print(f"\n  Expiring federal contracts:")
        for opp in pre_scored[:5]:
            print(f"    [exp] {opp['title'][:65]}")
            print(f"          {opp['url'][:80]}")

    # ── Send email ─────────────────────────────────────────────────────────
    resend_key = os.environ.get("RESEND_API_KEY")
    recipient  = os.environ.get("RECIPIENT_EMAIL")
    sender     = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")

    if not resend_key:
        print("\n  RESEND_API_KEY not set — skipping email.")
        sys.exit(0)

    if not recipient:
        print("\n  RECIPIENT_EMAIL not set — skipping email.")
        sys.exit(0)

    if not scored and not pre_scored:
        print("\n  No new opportunities found — skipping email (nothing to send).")
        sys.exit(0)

    print(f"\n  Sending digest to {recipient}…")
    try:
        result = send_digest(scored, pre_scored, recipient, resend_key, sender)
        print(f"  Email sent! ID: {result.get('id', 'n/a')}")
    except Exception as e:
        print(f"  Email send failed: {e}")
        sys.exit(1)

    print(f"\n{'='*55}")
    print(f"  Done. {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
