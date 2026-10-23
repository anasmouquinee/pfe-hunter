"""Utility functions for URL sanitization, email extraction, and recruiter profile parsing."""

import re
from typing import List, Optional
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

TRACKING_PARAMS = {
    "refid", "trk", "trackingid", "position", "pagenum", "currentjobid",
    "fbclid", "gclid", "_ga", "mc_cid", "mc_eid"
}


def clean_url(url: str) -> str:
    """
    Removes tracking parameters, session fragments, and trailing slashes.
    Preserves essential job identifiers (e.g. ?id=...) while ensuring deterministic hashing.
    """
    if not url:
        return ""
    parsed = urlparse(url.strip())
    query_items = parse_qsl(parsed.query, keep_blank_values=False)
    filtered_items = [
        (k, v) for k, v in query_items
        if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_")
    ]
    new_query = urlencode(filtered_items)
    cleaned = urlunparse((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", new_query, ""))
    return cleaned



def extract_emails(text: str) -> List[str]:
    """
    Extracts valid email addresses from unstructured text.
    Filters out common media/asset false-positives (.png, .jpg, etc.).
    """
    if not text:
        return []

    pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    matches = re.findall(pattern, text)
    valid_emails: List[str] = []

    ignored_extensions = (
        ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
        ".pdf", ".css", ".js", ".html"
    )

    ignored_domains = (
        "@joblia.ma", "@dreamjob.ma", "@emploima.ma", "@emploi.ma", "@rekrute.com",
        "@marocannonces.com", "@talent.com", "@linkedin.com", "@github.com",
        "@sentry.io", "@w3.org", "@example.com", "@cloudflare.com"
    )

    ignored_prefixes = (
        "noreply@", "no-reply@", "ne-pas-repondre@", "donotreply@",
        "support@", "admin@", "abuse@", "postmaster@"
    )

    for candidate in matches:
        cleaned = candidate.strip('.,;!?:()[]"\'<>').lower()
        if not cleaned.endswith(ignored_extensions):
            if not any(cleaned.endswith(dom) for dom in ignored_domains):
                if not any(cleaned.startswith(pfx) for pfx in ignored_prefixes):
                    if cleaned not in valid_emails:
                        valid_emails.append(cleaned)

    return valid_emails



def extract_linkedin_urls(text: str) -> List[str]:
    """
    Extracts LinkedIn job, post, company, or personal profile links.
    """
    if not text:
        return []

    pattern = r'https?://[a-zA-Z0-9.-]*linkedin\.com/(?:in|posts|jobs|company)/[a-zA-Z0-9_.-]+'
    matches = re.findall(pattern, text)
    cleaned_urls: List[str] = []

    for url in matches:
        cleaned = clean_url(url.rstrip('.,;!?:()[]"\''))
        if cleaned and cleaned not in cleaned_urls:
            cleaned_urls.append(cleaned)

    return cleaned_urls


def extract_recruiter_profile(text: str) -> Optional[str]:
    """
    Extracts direct recruiter personal profile URLs (e.g., https://linkedin.com/in/username).
    """
    if not text:
        return None

    pattern = r'https?://[a-zA-Z0-9.-]*linkedin\.com/in/[a-zA-Z0-9_-]+'
    matches = re.findall(pattern, text)
    if matches:
        return clean_url(matches[0].rstrip('.,;!?:()[]"\''))

    return None
