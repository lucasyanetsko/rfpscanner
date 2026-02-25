"""
RFP Scanner Configuration
--------------------------
Edit keywords and search queries here to tune what opportunities get surfaced.
"""

# ---------------------------------------------------------------------------
# REQUIRED KEYWORDS
# At least one of these must appear in the title or description.
# An opportunity that matches none of these will be scored 0 and dropped.
# ---------------------------------------------------------------------------
REQUIRED_KEYWORDS = [
    # Case management
    "case management",
    "case management system",
    "case management software",
    "case management platform",
    # Licensing & certification
    "licensing system",
    "licensing platform",
    "licensing software",
    "license management",
    "certification system",
    "certification management",
    "certification platform",
    "credentialing system",
    "credentialing platform",
    # Permitting
    "permit management",
    "permitting system",
    "permitting software",
    "permitting platform",
    "permit tracking",
    # Benefits / services
    "benefits administration",
    "benefits management",
    "benefits platform",
    # Intake & workflow
    "intake management",
    "intake system",
    "workflow management",
    "workflow platform",
    "workflow automation",
    # Portals & citizen-facing
    "constituent portal",
    "citizen portal",
    "client portal",
    "self-service portal",
    # Grants
    "grants management",
    "grants management system",
    "grant tracking",
    # Compliance & inspections
    "compliance management",
    "compliance management system",
    "inspection management",
    "enforcement management",
    "regulatory management",
    # Application tracking
    "application tracking system",
    "application management system",
    "application processing",
    # Forms & review
    "form management",
    "digital forms",
    "online application",
    "online permitting",
]

# ---------------------------------------------------------------------------
# BOOST KEYWORDS
# These raise the relevance score. Not required but helpful.
# ---------------------------------------------------------------------------
BOOST_KEYWORDS = [
    "request for proposal",
    "rfp",
    "solicitation",
    "procurement",
    "bid",
    "rfi",
    "request for information",
    "software",
    "platform",
    "system",
    "application",
    "saas",
    "cloud",
    "cloud-based",
    "web-based",
    "digital transformation",
    "modernization",
    "implementation",
    "government",
    "state",
    "county",
    "municipal",
    "nonprofit",
    "non-profit",
    "agency",
]

# ---------------------------------------------------------------------------
# NEGATIVE KEYWORDS
# Opportunities containing any of these will be penalized or dropped.
# ---------------------------------------------------------------------------
NEGATIVE_KEYWORDS = [
    "job posting",
    "career opportunity",
    "employment opportunity",
    "hiring",
    "salary",
    "resume",
    "curriculum vitae",
    "internship",
]

# ---------------------------------------------------------------------------
# GOOGLE SEARCH QUERIES (run via Serper.dev)
# These are fed one-by-one to the Google Search API.
# Each returns up to 20 results from the last LOOKBACK_DAYS days.
# ---------------------------------------------------------------------------
SEARCH_QUERIES = [
    # ── Core procurement queries ───────────────────────────────────────────
    '"request for proposal" "case management" software',
    '"request for proposal" "case management system"',
    '"request for proposal" "licensing system" OR "licensing platform" software',
    '"request for proposal" "certification management" OR "certification system" software',
    '"request for proposal" "permitting system" OR "permit management" software',
    '"request for proposal" "intake management" OR "intake system" software',
    '"request for proposal" "workflow management" OR "workflow platform" software',
    '"request for proposal" "constituent portal" OR "citizen portal"',
    '"request for proposal" "benefits administration" OR "benefits management" software',
    '"request for proposal" "grants management" system software',
    '"request for proposal" "compliance management" software government',
    '"request for proposal" "credentialing system" OR "credentialing platform"',
    '"request for information" "case management" software government',
    '"request for proposal" "application processing" software government',
    '"request for proposal" "online permitting" OR "online licensing" platform',
    '"request for proposal" "form management" OR "digital forms" government software',

    # ── .gov domain targeting (hits state portals Google has indexed) ──────
    'site:.gov "request for proposal" "case management" software',
    'site:.gov "request for proposal" "licensing system" OR "permitting system"',
    'site:.gov "request for proposal" "workflow management" software',
    'site:.gov "solicitation" "case management" OR "permitting" software',
    'site:.gov "request for proposal" "grants management" software',
    'site:.gov "request for proposal" "benefits administration" software',
    'site:.gov "request for proposal" "credentialing" OR "certification management"',
    'site:.gov "invitation to bid" "case management" OR "licensing system"',
    'site:.gov solicitation "intake management" OR "intake system" software',
    'site:.gov "request for information" "case management" OR "workflow" software',

    # ── State-specific high-volume portal targeting ────────────────────────
    'site:eva.virginia.gov "case management" OR "licensing" OR "permitting" software',
    'site:esbd.cpa.texas.gov "case management" OR "workflow" OR "permitting"',
    'site:ips.state.nc.us "case management" OR "licensing" OR "permitting"',
    'site:emaryland.buyspeed.com "case management" OR "workflow" OR "licensing"',

    # ── Year-anchored queries to ensure fresh 2026 results ────────────────
    'RFP "case management" (state OR county OR municipality) software 2026',
    'RFP "licensing software" OR "licensing platform" government 2026',
    '"request for proposal" "case management system" government 2026',
    '"request for proposal" "permitting software" OR "permitting platform" 2026',
    '"request for proposal" "workflow automation" government agency 2026',
    '"request for proposal" "citizen portal" OR "constituent portal" software 2026',
]

# ---------------------------------------------------------------------------
# BIDNET DIRECT KEYWORD SEARCHES
# BidNet is used by hundreds of state/local agencies.
# ---------------------------------------------------------------------------
BIDNET_KEYWORDS = [
    "case management",
    "licensing system",
    "certification management",
    "permit management",
    "benefits administration",
    "workflow management",
    "constituent portal",
    "grants management",
    "credentialing",
    "intake system",
]

# ---------------------------------------------------------------------------
# SAM.GOV KEYWORDS (Federal opportunities — requires SAM_API_KEY secret)
# ---------------------------------------------------------------------------
SAM_KEYWORDS = [
    "case management software",
    "case management system",
    "licensing system",
    "certification management",
    "permit management software",
    "workflow management platform",
    "constituent portal",
    "grants management system",
    "benefits administration software",
]

# ---------------------------------------------------------------------------
# SCORING THRESHOLDS
# ---------------------------------------------------------------------------
# Only include opportunities with a score at or above this value in the digest
MIN_SCORE = 45

# Look back this many days when searching (slightly overlapping to avoid gaps)
LOOKBACK_DAYS = 2

# ---------------------------------------------------------------------------
# BLOCKED DOMAINS
# Known non-procurement sites that should never appear in results.
# ---------------------------------------------------------------------------
BLOCKED_DOMAINS = [
    # E-commerce / corporate blogs
    "amazon.com", "amazon.co.uk",
    # Job boards
    "linkedin.com", "indeed.com", "glassdoor.com", "ziprecruiter.com",
    "monster.com", "careerbuilder.com",
    # General news / media
    "medium.com", "substack.com", "forbes.com", "bloomberg.com",
    "reuters.com", "techcrunch.com", "venturebeat.com", "wired.com",
    "theverge.com", "zdnet.com", "cnet.com",
    # PR wire services (press releases, not RFPs)
    "businesswire.com", "prnewswire.com", "globenewswire.com", "prweb.com",
    "accesswire.com",
    # Wikipedia / reference
    "wikipedia.org", "en.wikipedia.org",
    # Social media
    "twitter.com", "x.com", "facebook.com", "reddit.com",
]

# ---------------------------------------------------------------------------
# FOREIGN TLDs — results on these domains are outside the US
# ---------------------------------------------------------------------------
FOREIGN_TLDS = [
    # UK
    ".co.uk", ".org.uk", ".gov.uk", ".ac.uk", ".me.uk",
    # Australia / NZ
    ".com.au", ".net.au", ".org.au", ".gov.au", ".co.nz", ".govt.nz",
    # Canada
    ".ca",
    # Europe
    ".de", ".fr", ".eu", ".it", ".es", ".nl", ".be", ".se", ".no",
    ".dk", ".fi", ".pl", ".at", ".ch", ".ie", ".pt", ".cz", ".hu",
    # Asia / Pacific
    ".cn", ".jp", ".kr", ".in", ".sg", ".hk", ".tw",
    # Latin America
    ".br", ".mx", ".ar", ".co", ".cl",
    # Africa / Middle East
    ".za", ".ae", ".sa",
    # Other
    ".ru", ".ua",
]

# ---------------------------------------------------------------------------
# JUNK URL PATH PATTERNS
# URLs containing these path segments are almost certainly blog posts,
# news articles, or other non-procurement content.
# ---------------------------------------------------------------------------
JUNK_URL_PATHS = [
    "/blog/", "/blogs/",
    "/news/", "/newsroom/",
    "/article/", "/articles/",
    "/press/", "/press-release/", "/press-releases/",
    "/media/", "/media-center/",
    "/insights/", "/insight/",
    "/resources/", "/resource/",
    "/thought-leadership/",
    "/whitepaper/", "/white-paper/",
    "/podcast/", "/webinar/",
    "/story/", "/stories/",
    "/post/", "/posts/",
]

# ---------------------------------------------------------------------------
# USASPENDING.GOV KEYWORDS
# Searched against the federal contract database for contracts expiring
# within the next 12 months — signals agencies likely to issue RFPs soon.
# Keep this list focused; USASpending keyword search is exact-phrase based.
# ---------------------------------------------------------------------------
USASPENDING_KEYWORDS = [
    "case management software",
    "case management system",
    "licensing system",
    "licensing software",
    "permitting software",
    "permit management",
    "certification management",
    "credentialing system",
    "workflow management",
    "benefits administration",
    "grants management",
    "constituent portal",
    "intake management",
]

# ---------------------------------------------------------------------------
# INFOR/BUYSPEED STATE PROCUREMENT PORTALS
#
# These states run procurement on the Infor Public Sector platform.
# All share the same scraping pattern — see search_infor_portal() in sources.py.
#
# Key: display name used in email digest  Value: base URL (no trailing slash)
#
# To add a new state, confirm its /ajax.aspx/en/rfp/request_browse_public
# endpoint returns HTTP 200, then add it here.
# ---------------------------------------------------------------------------
INFOR_PORTALS = {
    "Arizona":  "https://app.az.gov",
    # Add more states as confirmed:
    # "Maryland": "https://emma.maryland.gov",    # has browser-check CAPTCHA
    # "Colorado": "https://bids.colorado.gov",    # TLS issues as of Feb 2026
    # "Delaware": "https://bid.delaware.gov",     # connection refused as of Feb 2026
}
