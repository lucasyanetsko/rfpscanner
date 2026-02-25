"""
Data source scrapers for RFP Scanner.

Sources:
  - Google Search via Serper.dev API  (requires SERPER_API_KEY)
  - BidNet Direct public solicitations (no key needed)
  - SAM.gov Opportunities API          (requires SAM_API_KEY, optional)
"""

import time
import httpx
from datetime import datetime, timedelta
from typing import List, Dict
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Shared HTTP client with reasonable timeouts
# ---------------------------------------------------------------------------
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}


# ---------------------------------------------------------------------------
# Google Search via Serper.dev
# ---------------------------------------------------------------------------
def search_google(query: str, api_key: str, lookback_days: int = 2) -> List[Dict]:
    """Search Google via Serper.dev and return raw results."""
    try:
        resp = httpx.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={
                "q": query,
                "num": 20,
                "tbs": f"qdr:d{lookback_days}",  # restrict to last N days
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data.get("organic", []):
            results.append({
                "title":       item.get("title", "").strip(),
                "url":         item.get("link", "").strip(),
                "description": item.get("snippet", "").strip(),
                "source":      "Google / Serper",
                "posted_date": item.get("date", ""),
                "agency":      "",
                "query":       query,
            })

        # Brief pause to be a good API citizen
        time.sleep(0.3)
        return results

    except httpx.HTTPStatusError as e:
        print(f"    [Serper] HTTP {e.response.status_code} for query: {query[:50]}")
        return []
    except Exception as e:
        print(f"    [Serper] Error: {e}")
        return []


# ---------------------------------------------------------------------------
# BidNet Direct
# ---------------------------------------------------------------------------
def search_bidnet(keyword: str) -> List[Dict]:
    """Scrape BidNet Direct public solicitations for a keyword."""
    base_url = "https://www.bidnetdirect.com/public/solicitations/open"
    try:
        resp = httpx.get(
            base_url,
            params={"keyword": keyword},
            headers=_HEADERS,
            timeout=30,
            follow_redirects=True,
        )
        if resp.status_code != 200:
            print(f"    [BidNet] HTTP {resp.status_code} for keyword: {keyword}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        results = []

        # BidNet renders solicitations in a table; selectors may need updating
        # if BidNet redesigns their site.
        for row in soup.select("table tbody tr, .solicitation-item, .bid-listing"):
            cells = row.find_all("td")
            if not cells:
                continue

            # Try to find the title link
            link_el = row.find("a", href=True)
            if not link_el:
                continue

            title = link_el.get_text(strip=True)
            href = link_el["href"]
            if not href.startswith("http"):
                href = f"https://www.bidnetdirect.com{href}"

            # Grab as much metadata as possible from remaining cells
            cell_texts = [c.get_text(strip=True) for c in cells]
            description = " | ".join(t for t in cell_texts if t and t != title)

            if title and href:
                results.append({
                    "title":       title,
                    "url":         href,
                    "description": description[:300],
                    "source":      "BidNet Direct",
                    "posted_date": "",
                    "agency":      "",
                })

        time.sleep(0.5)
        return results

    except Exception as e:
        print(f"    [BidNet] Error for '{keyword}': {e}")
        return []


# ---------------------------------------------------------------------------
# SAM.gov (Federal Opportunities API)
# ---------------------------------------------------------------------------
def search_sam_gov(api_key: str, keywords: List[str], lookback_days: int = 2) -> List[Dict]:
    """Search SAM.gov for federal software procurement opportunities."""
    posted_from = (datetime.now() - timedelta(days=lookback_days)).strftime("%m/%d/%Y")
    base_url = "https://api.sam.gov/opportunities/v2/search"
    results = []

    for kw in keywords:
        try:
            resp = httpx.get(
                base_url,
                params={
                    "api_key":    api_key,
                    "keywords":   kw,
                    "postedFrom": posted_from,
                    "limit":      25,
                    "ptype":      "o",   # only presolicitations/solicitations
                },
                timeout=30,
            )
            if resp.status_code != 200:
                print(f"    [SAM.gov] HTTP {resp.status_code} for: {kw}")
                continue

            data = resp.json()
            for opp in data.get("opportunitiesData", []):
                notice_id = opp.get("noticeId", "")
                results.append({
                    "title":       opp.get("title", "").strip(),
                    "url":         f"https://sam.gov/opp/{notice_id}/view",
                    "description": opp.get("description", "")[:300].strip(),
                    "source":      "SAM.gov",
                    "posted_date": opp.get("postedDate", ""),
                    "agency":      opp.get("fullParentPathName", ""),
                })

        except Exception as e:
            print(f"    [SAM.gov] Error for '{kw}': {e}")

        time.sleep(0.5)

    return results


# ---------------------------------------------------------------------------
# OpenGov Procurement (public API — no key needed)
# ---------------------------------------------------------------------------
def search_opengov(keywords: List[str]) -> List[Dict]:
    """Search OpenGov's public procurement API."""
    results = []
    base_url = "https://procurement.opengov.com/api/opportunities/search"

    for kw in keywords:
        try:
            resp = httpx.get(
                base_url,
                params={"q": kw, "status": "open", "per_page": 25},
                headers=_HEADERS,
                timeout=30,
            )
            if resp.status_code != 200:
                continue

            data = resp.json()
            for opp in data.get("opportunities", data.get("results", [])):
                title = opp.get("title") or opp.get("name", "")
                url   = opp.get("url") or opp.get("permalink", "")
                if title and url:
                    results.append({
                        "title":       title.strip(),
                        "url":         url if url.startswith("http") else f"https://procurement.opengov.com{url}",
                        "description": opp.get("description", "")[:300].strip(),
                        "source":      "OpenGov",
                        "posted_date": opp.get("published_at", ""),
                        "agency":      opp.get("entity_name", ""),
                    })

        except Exception as e:
            print(f"    [OpenGov] Error for '{kw}': {e}")

        time.sleep(0.5)

    return results
