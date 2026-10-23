"""Unified JobOffer model for scraped PFE opportunities."""

import hashlib
from typing import Optional
from pydantic import BaseModel, Field
from src.utils.text_extractor import clean_url, extract_emails, extract_recruiter_profile


class JobOffer(BaseModel):
    id: str = ""
    title: str
    company: str
    location: str = "Casablanca, Maroc"
    url: str
    description: str = ""
    source: str  # "rekrute", "emploima", "linkedin_guest", "linkedin_post"
    contact_email: Optional[str] = None
    linkedin_url: Optional[str] = None  # Direct LinkedIn offer or post URL
    hr_name: Optional[str] = None
    hr_linkedin_url: Optional[str] = None  # Direct Recruiter / HR LinkedIn profile URL
    is_remunerated: Optional[bool] = None
    posted_date: Optional[str] = None
    score: int = 0
    matched_skills: list[str] = Field(default_factory=list)
    applied: bool = False
    notified: bool = False
    simulated: bool = False

    def model_post_init(self, __context):
        # Normalize main URL to remove tracking parameters
        normalized_url = clean_url(self.url) if self.url else ""

        if not self.id:
            # Deterministic unique hash based on source, company, and normalized title/URL
            hash_input = f"{self.source}:{self.company.lower().strip()}:{self.title.lower().strip()}:{normalized_url}"
            self.id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        # Auto-detect clean LinkedIn URL if the main URL points to LinkedIn
        if not self.linkedin_url and "linkedin.com" in self.url:
            self.linkedin_url = normalized_url or self.url.split("?")[0]

            # Auto-extract email from description if not already provided
            if not self.contact_email:
                emails = extract_emails(self.description)
                if emails:
                    self.contact_email = emails[0]

            # Auto-extract direct recruiter/HR LinkedIn profile (/in/...)
            if not self.hr_linkedin_url:
                self.hr_linkedin_url = extract_recruiter_profile(self.description)

        # Fallback: resolve verified company talent inbox if still missing email
        if not self.contact_email:
            try:
                from src.matcher.company_directory import resolve_company_email
                resolved_email, _ = resolve_company_email(self.company, self.description)
                if resolved_email:
                    self.contact_email = resolved_email
            except Exception:
                pass
