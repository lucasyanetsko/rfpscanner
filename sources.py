"""
Data source scrapers for RFP Scanner.

Sources:
  - Google Search via Serper.dev API       (requires SERPER_API_KEY)
  - BidNet Direct public solicitations     (no key needed)
  - OpenGov Procurement public API         (no key needed)
  - SAM.gov Opportunities API              (requires SAM_API_KEY, optional)
  - Tennessee Procurement static page      (no key needed)
  - Infor/BuySpeed state portals           (no key needed)
      Confirmed: Arizona (app.az.gov)
  - Virginia eVA                           (requires browser / Playwright — Phase 2)
"""

import re
import time
import httpx
from datetime import datetime, timedelta
from typing import List, Dict
from bs4 import BeautifulSoup


# ---------------------------------------------------------------------------
# Shared HTTP headers — full Chrome fingerprint so state portals don't 403
# ---------------------------------------------------------------------------
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
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

        for row in soup.select("table tbody tr, .solicitation-item, .bid-listing"):
            cells = row.find_all("td")
            if not cells:
                continue

            link_el = row.find("a", href=True)
            if not link_el:
                continue

            title = link_el.get_text(strip=True)
            href = link_el["href"]
            if not href.startswith("http"):
                href = f"https://www.bidnetdirect.com{href}"

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
                    "ptype":      "o",
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


# ---------------------------------------------------------------------------
# Tennessee Procurement — static HTML table, no login required
#
# URL: https://www.tn.gov/.../request-for-proposals--rfp--opportunities1.html
# Structure: table with columns [Document ID (links), Dates, Event Name, Updated]
# No keyword search — we fetch the full table and filter locally.
# ---------------------------------------------------------------------------
_TN_RFP_URL = (
    "https://www.tn.gov/generalservices/procurement/"
    "central-procurement-office--cpo-/supplier-information/"
    "request-for-proposals--rfp--opportunities1.html"
)

def search_tennessee(keywords: List[str]) -> List[Dict]:
    """
    Scrape Tennessee's public RFP listing page and return opportunities
    whose Event Name matches any of the supplied keywords.
    """
    kw_lower = [kw.lower() for kw in keywords]
    results: List[Dict] = []

    try:
        resp = httpx.get(
            _TN_RFP_URL,
            headers=_HEADERS,
            timeout=30,
            follow_redirects=True,
        )
        if resp.status_code != 200:
            print(f"    [Tennessee] HTTP {resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, "html.parser")

        for table in soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) < 3:
                    continue

                # Col 2 = Event Name (0-indexed: doc-id, dates, event-name, [updated])
                title = cells[2].get_text(strip=True)
                if not title:
                    continue

                # Keyword filter
                if not any(kw in title.lower() for kw in kw_lower):
                    continue

                # Primary link = first <a> in the doc-id cell (PDF or detail page)
                link_el = cells[0].find("a", href=True)
                href = link_el["href"] if link_el else ""
                if href.startswith("/"):
                    href = "https://www.tn.gov" + href
                elif not href.startswith("http"):
                    href = _TN_RFP_URL

                # Dates = col 1
                dates = cells[1].get_text(strip=True)

                results.append({
                    "title":       title,
                    "url":         href,
                    "description": f"Dates: {dates}" if dates else "",
                    "source":      "Tennessee Procurement",
                    "posted_date": "",
                    "agency":      "State of Tennessee",
                })

        time.sleep(0.5)
        return results

    except Exception as e:
        print(f"    [Tennessee] Error: {e}")
        return []


# ---------------------------------------------------------------------------
# Infor/BuySpeed State Procurement Portals — no login required
#
# Several states run their procurement on the Infor Public Sector platform
# (formerly BuySpeed / Periscope S2G).  All share the same URL pattern:
#
#   Public browse:  {base_url}/page.aspx/en/rfp/request_browse_public
#   AJAX data feed: {base_url}/ajax.aspx/en/rfp/request_browse_public
#
# The AJAX endpoint returns server-rendered HTML with the full grid.
# Pagination is driven by a hidden form field; we POST through all pages.
#
# Confirmed portals (tested Feb 2026):
#   Arizona  — https://app.az.gov
#
# To add a new state: add its base URL to INFOR_PORTALS in config.py and
# verify that {base_url}/ajax.aspx/en/rfp/request_browse_public returns 200.
# ---------------------------------------------------------------------------

def _infor_parse_page(html: str, base_url: str, state_name: str) -> List[Dict]:
    """Parse one page of results from an Infor procurement portal HTML fragment."""
    results: List[Dict] = []
    soup = BeautifulSoup(html, "html.parser")

    # The grid table has an id matching *grd*
    grid = soup.find("table", id=re.compile(r"grd"))
    if not grid:
        return results

    for row in grid.find_all("tr"):
        # Title lives in: <span class="sr-only">Edit [TITLE]</span>
        sr_spans = row.find_all("span", class_="sr-only")
        title = None
        for span in sr_spans:
            text = span.get_text(strip=True)
            if text.startswith("Edit "):
                title = text[5:]  # strip the "Edit " prefix
                break

        if not title:
            continue

        # Detail link: href="/page.aspx/en/bpm/process_manage_extranet/[ID]"
        manage_link = row.find("a", href=re.compile(r"process_manage_extranet"))
        if manage_link:
            href = manage_link.get("href", "")
            opp_url = (base_url.rstrip("/") + href) if href.startswith("/") else href
        else:
            opp_url = base_url.rstrip("/") + "/page.aspx/en/rfp/request_browse_public"

        # Additional cell data: [edit_btn, bpm_code, label, pub_begin, commodity,
        #                         agency, pub_end, status, awarded, remaining, begin, end]
        cells = row.find_all("td")
        cell_texts = [c.get_text(strip=True) for c in cells]
        agency   = cell_texts[5] if len(cell_texts) > 5 else ""
        pub_end  = cell_texts[6] if len(cell_texts) > 6 else ""

        results.append({
            "title":       title,
            "url":         opp_url,
            "description": f"Due: {pub_end}" if pub_end else "",
            "source":      f"{state_name} Procurement",
            "posted_date": "",
            "agency":      agency,
        })

    return results


def search_infor_portal(base_url: str, state_name: str, keywords: List[str]) -> List[Dict]:
    """
    Fetch all open solicitations from an Infor/BuySpeed state portal,
    paginate through every page, and return keyword-matched opportunities.
    """
    ajax_url = base_url.rstrip("/") + "/ajax.aspx/en/rfp/request_browse_public"
    headers = {
        **_HEADERS,
        "Referer":           base_url.rstrip("/") + "/page.aspx/en/rfp/request_browse_public",
        "X-Requested-With":  "XMLHttpRequest",
    }
    kw_lower = [kw.lower() for kw in keywords]
    all_opps: List[Dict] = []

    try:
        # ── Page 0: GET ──────────────────────────────────────────────────
        resp = httpx.get(ajax_url, headers=headers, timeout=30, follow_redirects=True)
        if resp.status_code != 200:
            print(f"    [{state_name}] HTTP {resp.status_code}")
            return []

        html = resp.text

        # How many pages are there?
        max_page_m = re.search(
            r'name=["\x27]maxpageindexbody_x_grid_grd["\x27][^>]*value=["\x27](\d+)',
            html,
        )
        max_page = int(max_page_m.group(1)) if max_page_m else 0

        all_opps.extend(_infor_parse_page(html, base_url, state_name))

        # ── Extract form data for pagination POSTs ────────────────────────
        form_data: Dict[str, str] = {}
        for field in re.findall(r'<input[^>]*type=["\x27]hidden["\x27][^>]*>', html, re.DOTALL):
            name_m = re.search(r'name=["\x27]([^"\x27]+)', field)
            val_m  = re.search(r'value=["\x27]([^"\x27]*)', field)
            if name_m:
                form_data[name_m.group(1)] = val_m.group(1) if val_m else ""

        # ── Pages 1..N: POST ──────────────────────────────────────────────
        for page_idx in range(1, min(max_page + 1, 15)):   # cap at 15 pages
            time.sleep(0.5)
            form_data["hdnCurrentPageIndexbody_x_grid_grd"] = str(page_idx)

            page_resp = httpx.post(
                ajax_url,
                headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
                data=form_data,
                timeout=30,
                follow_redirects=True,
            )
            if page_resp.status_code != 200:
                break

            all_opps.extend(_infor_parse_page(page_resp.text, base_url, state_name))

        # ── Keyword filter ────────────────────────────────────────────────
        matched = [
            opp for opp in all_opps
            if any(kw in f"{opp['title']} {opp.get('description','')} {opp.get('agency','')}".lower()
                   for kw in kw_lower)
        ]

        return matched

    except Exception as e:
        print(f"    [{state_name}] Error: {e}")
        return []
