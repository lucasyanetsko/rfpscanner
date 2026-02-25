"""
Scoring and deduplication logic for RFP Scanner.

Scoring rubric (0–100):
  +up to 60  - required keyword matches
  +25        - RFP/solicitation language in the title
  +10        - RFP/solicitation language in the body (not title)
  +10        - software/platform/system language
  -30        - job posting / employment signals
"""

from typing import List, Dict
from config import REQUIRED_KEYWORDS, BOOST_KEYWORDS, NEGATIVE_KEYWORDS

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


def score_opportunity(opp: Dict) -> int:
    """Return a relevance score 0–100 for an opportunity."""
    title_raw = opp.get("title", "")
    desc_raw  = opp.get("description", "") or opp.get("agency", "")
    full_text = f"{title_raw} {desc_raw}".lower()
    title_lc  = title_raw.lower()

    # --- Hard negative: job postings ---
    if any(neg in full_text for neg in NEGATIVE_KEYWORDS):
        return 0

    # --- Required keyword match ---
    required_hits = [kw for kw in REQUIRED_KEYWORDS if kw.lower() in full_text]
    if not required_hits:
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
