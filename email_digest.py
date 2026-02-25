"""
HTML email digest builder and Resend sender for RFP Scanner.
"""

import httpx
from datetime import datetime
from typing import List, Dict


# ---------------------------------------------------------------------------
# HTML email (table-based for broad email client compatibility)
# ---------------------------------------------------------------------------
def _score_badge(score: int) -> str:
    if score >= 70:
        bg, label = "#16a34a", "High"
    elif score >= 50:
        bg, label = "#d97706", "Medium"
    else:
        bg, label = "#6b7280", "Low"
    return (
        f'<span style="display:inline-block;font-size:10px;font-weight:700;'
        f'color:white;background:{bg};padding:2px 7px;border-radius:10px;'
        f'letter-spacing:0.04em;margin-left:6px;">{label} match</span>'
    )


def _source_badge(source: str) -> str:
    colors = {
        "SAM.gov":          "#7c3aed",
        "BidNet Direct":    "#0891b2",
        "OpenGov":          "#059669",
        "Google / Serper":  "#1d4ed8",
    }
    bg = colors.get(source, "#374151")
    return (
        f'<span style="display:inline-block;font-size:10px;font-weight:700;'
        f'color:white;background:{bg};padding:2px 8px;border-radius:10px;'
        f'letter-spacing:0.04em;">{source}</span>'
    )


def build_html(opportunities: List[Dict]) -> str:
    today   = datetime.now().strftime("%B %d, %Y")
    count   = len(opportunities)
    noun    = "opportunity" if count == 1 else "opportunities"

    # Source summary line
    by_source: Dict[str, int] = {}
    for opp in opportunities:
        src = opp.get("source", "Other")
        by_source[src] = by_source.get(src, 0) + 1
    source_summary = " &nbsp;|&nbsp; ".join(
        f"{src}: <strong>{n}</strong>" for src, n in sorted(by_source.items())
    )

    # Build rows
    rows = []
    for opp in opportunities:
        title       = opp.get("title", "Untitled")
        url         = opp.get("url", "#")
        description = opp.get("description", "")[:250]
        if len(opp.get("description", "")) > 250:
            description += "…"
        source      = opp.get("source", "")
        agency      = opp.get("agency", "")
        posted      = opp.get("posted_date", "")
        score       = opp.get("score", 0)

        meta_parts = []
        if posted:
            meta_parts.append(f"<span>📅 {posted}</span>")
        if agency:
            meta_parts.append(f"<span>🏛 {agency}</span>")
        meta_html = (
            '<span style="color:#d1d5db">&nbsp;|&nbsp;</span>'.join(meta_parts)
            if meta_parts else ""
        )

        rows.append(f"""
        <tr>
          <td style="padding:20px 28px;border-bottom:1px solid #f0f0f0;vertical-align:top;">
            <div style="margin-bottom:8px;">
              {_source_badge(source)}
              {_score_badge(score)}
            </div>
            <a href="{url}"
               style="font-size:15px;font-weight:600;color:#1e40af;text-decoration:none;
                      line-height:1.4;display:block;margin:6px 0 8px;">
              {title}
            </a>
            {"<p style='font-size:13px;color:#6b7280;margin:0 0 10px;line-height:1.6;'>" + description + "</p>" if description else ""}
            <div style="font-size:12px;color:#9ca3af;">
              {meta_html}
              {"<span style='color:#d1d5db'>&nbsp;|&nbsp;</span>" if meta_parts else ""}
              <a href="{url}"
                 style="color:#3b82f6;text-decoration:none;font-weight:500;">
                View opportunity →
              </a>
            </div>
          </td>
        </tr>""")

    rows_html = "\n".join(rows)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>RFP Scout Daily Digest</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <div style="max-width:680px;margin:32px auto 48px;background:white;border-radius:14px;
              overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">

    <!-- ── Header ── -->
    <div style="background:linear-gradient(135deg,#1e3a8a 0%,#2563eb 100%);
                padding:36px 32px 28px;">
      <p style="margin:0 0 6px;font-size:11px;font-weight:700;color:#93c5fd;
                text-transform:uppercase;letter-spacing:0.12em;">
        Daily Digest &mdash; {today}
      </p>
      <h1 style="margin:0 0 6px;font-size:26px;font-weight:800;color:white;
                 letter-spacing:-0.02em;">
        RFP Scout
      </h1>
      <p style="margin:0;font-size:13px;color:#bfdbfe;line-height:1.5;">
        Case Management &bull; Licensing &bull; Certification &bull; Permitting &bull; Workflow Platforms
      </p>
    </div>

    <!-- ── Stats bar ── -->
    <div style="background:#eff6ff;padding:14px 28px;border-bottom:1px solid #dbeafe;
                display:flex;align-items:center;">
      <span style="font-size:15px;font-weight:700;color:#1e40af;">
        {count} new {noun} found
      </span>
      <span style="font-size:12px;color:#6b7280;margin-left:14px;">{source_summary}</span>
    </div>

    <!-- ── Opportunities ── -->
    <table width="100%" cellpadding="0" cellspacing="0" border="0"
           style="border-collapse:collapse;">
      {rows_html}
    </table>

    <!-- ── Footer ── -->
    <div style="padding:24px 28px;background:#f8fafc;border-top:1px solid #e2e8f0;">
      <p style="margin:0;font-size:11px;color:#94a3b8;text-align:center;line-height:1.6;">
        RFP Scout &mdash; Automated daily digest<br>
        Opportunities are scored by relevance to case management, licensing, certification,
        and related government/nonprofit software platforms.
      </p>
    </div>

  </div>
</body>
</html>"""


def build_plain_text(opportunities: List[Dict]) -> str:
    today = datetime.now().strftime("%B %d, %Y")
    lines = [
        f"RFP Scout — Daily Digest — {today}",
        "=" * 55,
        "",
        f"{len(opportunities)} new {'opportunity' if len(opportunities) == 1 else 'opportunities'} found",
        "",
    ]

    for i, opp in enumerate(opportunities, 1):
        lines.append(f"{i}. {opp.get('title', 'Untitled')}")
        lines.append(f"   Source : {opp.get('source', '')}")
        lines.append(f"   Score  : {opp.get('score', 0)}/100")
        if opp.get("agency"):
            lines.append(f"   Agency : {opp['agency']}")
        if opp.get("posted_date"):
            lines.append(f"   Posted : {opp['posted_date']}")
        if opp.get("description"):
            desc = opp["description"][:180]
            lines.append(f"   {desc}{'…' if len(opp['description']) > 180 else ''}")
        lines.append(f"   Link   : {opp.get('url', '')}")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Resend sender
# ---------------------------------------------------------------------------
def send_digest(
    opportunities: List[Dict],
    recipient: str,
    api_key: str,
    sender: str,
) -> dict:
    """Send the daily digest via Resend and return the API response."""
    count   = len(opportunities)
    noun    = "opportunity" if count == 1 else "opportunities"
    today   = datetime.now().strftime("%B %d, %Y")
    subject = f"RFP Scout: {count} new {noun} — {today}"

    payload = {
        "from":    sender,
        "to":      [recipient],
        "subject": subject,
        "html":    build_html(opportunities),
        "text":    build_plain_text(opportunities),
    }
    print(f"  [Resend] from={sender!r}  to={recipient!r}")

    resp = httpx.post(
        "https://api.resend.com/emails",
        headers={
            "Authorization":  f"Bearer {api_key}",
            "Content-Type":   "application/json",
        },
        json=payload,
        timeout=30,
    )

    if not resp.is_success:
        print(f"  [Resend] HTTP {resp.status_code} — response body:")
        print(f"  {resp.text}")
        resp.raise_for_status()

    return resp.json()
