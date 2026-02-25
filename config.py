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
    'site:.gov "request for proposal" "case management" OR "licensing" software',
    'site:.gov "solicitation" "case management" OR "permitting" software',
    'RFP "case management" (government OR state OR county OR nonprofit) software 2025',
    'RFP "licensing software" OR "licensing platform" government 2025',
    '"request for information" "case management" software government',
    '"request for proposal" "application processing" software government',
    '"request for proposal" "online permitting" OR "online licensing" platform',
    '"request for proposal" "form management" OR "digital forms" government software',
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
MIN_SCORE = 35

# Look back this many days when searching (slightly overlapping to avoid gaps)
LOOKBACK_DAYS = 2
