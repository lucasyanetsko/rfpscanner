"""
Scoring and deduplication logic for RFP Scanner.

Scoring rubric (0–100):
  +up to 60  - required keyword matches
  +25        - RFP/solicitation language in the title
  +10        - RFP/solicitation language in the body (not title)
  +10        - software/platform/system language
  -instant 0 - job postings / employment signals
  -instant 0 - foreign TLD (non-US domain)
  -instant 0 - blocked domain (news, blogs, job boards, etc.)
  -instant 0 - junk URL path (/blog/, /news/, /article/, etc.)
  -instant 0 - Google result with no procurement language
"""

from typing import List, Dict
from urllib.parse import urlparse
from config import (
    REQUIRED_KEYWORDS,
    BOOST_KEYWORDS,
    NEGATIVE_KEYWORDS,
    BLOCKED_DOMAINS,
    FOREIGN_TLDS,
    JUNK_URL_PATHS,
)

# Procurement signal phrases (strong positive)
_PROCUREMENT_TITLE = [
    "request for proposal", "rfp", "solicitation", "bid", "procurement",
    "request for information", "rfi", "request for quotation", "rfq",
    "invitation to bid", "itb",
]

# Software/tech signal phrases (moderate positive)
_TECH_SIGNALS = [
    "software", "platform", "system", "application", "app", "portal",
    "saas", "cloud", "cloud-based", "web-based", "digital", "technology",
]

# Sources that are inherently procurement platforms — no need to require
# explicit procurement language in the text since every listing is a bid.
_PROCUREMENT_PLATFORMS = {"BidNet Direct", "OpenGov", "SAM.gov"}


def _is_blocked_url(url: str) -> bool:
    """Return True if the URL should be hard-blocked before scoring."""
    try:
        parsed = urlparse(url.lower())
        hostname = parsed.netloc  # e.g. "www.amazon.co.uk"
        path     = parsed.path    # e.g. "/blog/sourcing-meaning"
    except Exception:
        return False

    # Strip leading "www."
    bare = hostname.removeprefix("www.")

    # 1. Blocked domains (exact match or subdomain)
    for blocked in BLOCKED_DOMAINS:
        if bare == blocked or bare.endswith(f".{blocked}"):
            return True

    # 2. Foreign TLDs
    for tld in FOREIGN_TLDS:
        if bare.endswith(tld):
            return True

    # 3. Junk URL path patterns
    # Ensure path has trailing slash for substring matching
    path_check = path if path.endswith("/") else path + "/"
    for pattern in JUNK_URL_PATHS:
        if pattern in path_check:
            return True

    return False


def score_opportunity(opp: Dict) -> int:
    """Return a relevance score 0–100 for an opportunity."""
    title_raw = opp.get("title", "")
    desc_raw  = opp.get("description", "") or opp.get("agency", "")
    full_text = f"{title_raw} {desc_raw}".lower()
    title_lc  = title_raw.lower()
    url       = opp.get("url", "")
    source    = opp.get("source", "")

    # --- Hard block: URL-based filters ---
    if _is_blocked_url(url):
        return 0

    # --- Hard negative: job postings ---
    if any(neg in full_text for neg in NEGATIVE_KEYWORDS):
        return 0

    # --- Required keyword match ---
    required_hits = [kw for kw in REQUIRED_KEYWORDS if kw.lower() in full_text]
    if not required_hits:
        return 0

    # --- For non-platform sources (Google), require explicit procurement language ---
    # BidNet, OpenGov, and SAM.gov are procurement platforms by definition;
    # every listing there is a bid. Google results without RFP/bid language
    # are almost always news articles or vendor marketing pages.
    if source not in _PROCUREMENT_PLATFORMS:
        if not any(p in full_text for p in _PROCUREMENT_TITLE):
            return 0

    score = 0

    # More matching required keywords = higher score (caps at 60)
    score += min(len(required_hits) * 20, 60)

    # --- Procurement language ---
    if any(p in title_lc for p in _PROCUREMENT_TITLE):
        score += 25
    elif any(p in full_text for p in _PROCUREMENT_TITLE):
        score += 10

    # --- Tech/software language ---
    if any(t in full_text for t in _TECH_SIGNALS):
        score += 10

    # --- Boost keywords (minor bumps) ---
    boost_hits = sum(1 for kw in BOOST_KEYWORDS if kw.lower() in full_text)
    score += min(boost_hits * 2, 10)

    return min(score, 100)


def deduplicate(opportunities: List[Dict]) -> List[Dict]:
    """Remove duplicate opportunities, keeping the first occurrence per URL."""
    seen_urls: set = set()
    unique: List[Dict] = []

    for opp in opportunities:
        # Normalize URL: strip query string and trailing slash
        raw_url = opp.get("url", "")
        # Keep fragment-free, query-free URL for dedup key
        clean = raw_url.split("?")[0].split("#")[0].rstrip("/").lower()

        if not clean:
            continue

        if clean not in seen_urls:
            seen_urls.add(clean)
            unique.append(opp)

    return unique
