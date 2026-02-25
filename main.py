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
    MIN_SCORE,
    LOOKBACK_DAYS,
)
from sources import search_google, search_bidnet, search_sam_gov, search_opengov
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
    all_raw: list = []

    # ── 1. Google Search (Serper.dev) ──────────────────────────────────────
    serper_key = os.environ.get("SERPER_API_KEY")
    if serper_key:
        print(f"[1/4] Google Search ({len(SEARCH_QUERIES)} queries via Serper.dev)…")
        for query in SEARCH_QUERIES:
            results = search_google(query, serper_key, lookback_days=LOOKBACK_DAYS)
            all_raw.extend(results)
            if results:
                print(f"      ✓ {len(results):>3} results  |  {query[:60]}")
    else:
        print("[1/4] Skipping Google Search (SERPER_API_KEY not set)")

    # ── 2. BidNet Direct ───────────────────────────────────────────────────
    print(f"\n[2/4] BidNet Direct ({len(BIDNET_KEYWORDS)} keywords)…")
    for keyword in BIDNET_KEYWORDS:
        results = search_bidnet(keyword)
        all_raw.extend(results)
        if results:
            print(f"      ✓ {len(results):>3} results  |  {keyword}")

    # ── 3. OpenGov ─────────────────────────────────────────────────────────
    print(f"\n[3/4] OpenGov Procurement…")
    og_results = search_opengov(BIDNET_KEYWORDS)
    all_raw.extend(og_results)
    print(f"      ✓ {len(og_results)} results total")

    # ── 4. SAM.gov (optional) ─────────────────────────────────────────────
    sam_key = os.environ.get("SAM_API_KEY")
    if sam_key:
        print(f"\n[4/4] SAM.gov ({len(SAM_KEYWORDS)} keywords)…")
        results = search_sam_gov(sam_key, SAM_KEYWORDS, lookback_days=LOOKBACK_DAYS)
        all_raw.extend(results)
        print(f"      ✓ {len(results)} results total")
    else:
        print("\n[4/4] Skipping SAM.gov (SAM_API_KEY not set — optional)")

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

    # ── Update seen-URL store ──────────────────────────────────────────────
    for opp in scored:
        seen_urls.add(opp["url"].split("?")[0].split("#")[0].rstrip("/").lower())
    save_seen_urls(seen_urls)

    # ── Preview top results in console ────────────────────────────────────
    if scored:
        print(f"\n  Top opportunities:")
        for opp in scored[:10]:
            print(f"    [{opp['score']:>3}] {opp['title'][:65]}")
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

    if not scored:
        print("\n  No new opportunities found — skipping email (nothing to send).")
        sys.exit(0)

    print(f"\n  Sending digest to {recipient}…")
    try:
        result = send_digest(scored, recipient, resend_key, sender)
        print(f"  Email sent! ID: {result.get('id', 'n/a')}")
    except Exception as e:
        print(f"  Email send failed: {e}")
        sys.exit(1)

    print(f"\n{'='*55}")
    print(f"  Done. {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
