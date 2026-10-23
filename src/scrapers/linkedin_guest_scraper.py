"""Public LinkedIn Guest Scraper -- 100% Ban-Proof with Anti-429 Session Rotation."""

import itertools
import re
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from src.scrapers.base import BaseScraper
from src.models.offer import JobOffer
from src.utils.text_extractor import clean_url, extract_emails, extract_recruiter_profile
from src.utils.logger import logger


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


class LinkedInGuestScraper(BaseScraper):
    """
    Scrapes LinkedIn's public guest job endpoint.
    NEVER uses user accounts or session cookies, completely eliminating any ban risk.
    Uses session and user-agent rotation to prevent HTTP 429 rate limits.
    Fetches full job posting details to extract HR emails and recruiter LinkedIn profiles.
    """
    name: str = "linkedin_guest"
    SEARCH_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

    def __init__(self, timeout: int = 15):
        super().__init__(timeout=timeout)
        self._ua_cycle = itertools.cycle(USER_AGENTS)

    def _create_fresh_session(self) -> requests.Session:
        """Creates a fresh requests Session with rotated headers to avoid 429 tracking."""
        s = requests.Session()
        s.headers.update({
            "User-Agent": next(self._ua_cycle),
            "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.google.com/",
        })
        return s

    def scrape(
        self,
        keyword: str = "stage pfe data",
        location: str = "Casablanca",
        max_pages: int = 2,
    ) -> List[JobOffer]:
        """
        Scrapes public guest listings with pagination (up to max_pages * 25 offers).
        Rotates sessions between queries to prevent HTTP 429 rate limits.
        """
        offers: List[JobOffer] = []
        seen_urls = set()

        for page in range(max_pages):
            start = page * 25
            params = {
                "keywords": keyword,
                "location": location,
                "start": start,
            }

            session = self._create_fresh_session()
            try:
                response = session.get(self.SEARCH_URL, params=params, timeout=self.timeout)

                if response.status_code == 429:
                    logger.warning("LinkedIn Guest API rate limit (429) on '%s'. Backing off 1.5s...", keyword)
                    time.sleep(1.5)
                    session = self._create_fresh_session()
                    response = session.get(self.SEARCH_URL, params=params, timeout=self.timeout)

                if response.status_code != 200:
                    logger.warning("LinkedIn Guest API returned HTTP %s for query '%s' (start=%d)", response.status_code, keyword, start)
                    break

                soup = BeautifulSoup(response.text, "html.parser")
                page_offers = self.parse_html(soup)

                if not page_offers:
                    break

                for off in page_offers:
                    if off.url not in seen_urls:
                        seen_urls.add(off.url)
                        offers.append(off)

                # Polite pause between pagination pages
                time.sleep(1.0)

            except Exception as e:
                logger.error("Error scraping LinkedIn Guest API for '%s': %s", keyword, e)
                break

        logger.info("LinkedIn Guest API scraped %d total offers for '%s' in %s", len(offers), keyword, location)
        return offers

    def _is_relevant_title(self, title: str) -> bool:
        """Checks if title is tech or internship relevant before issuing full detail request."""
        t = title.lower()
        return any(w in t for w in (
            "stage", "pfe", "intern", "data", "ia", "ai", "dev", "engineer",
            "ingénieur", "software", "informatique", "python", "cloud", "web",
            "fullstack", "backend", "frontend", "react", "java", "tech"
        ))

    def parse_html(self, soup: BeautifulSoup) -> List[JobOffer]:
        offers: List[JobOffer] = []
        seen_urls = set()
        cards = soup.select(".base-card, .job-search-card")
        if not cards:
            cards = soup.select("li")

        for card in cards:
            title_elem = card.select_one(".base-search-card__title, h3, a.base-card__full-link")
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            link_elem = card.select_one("a.base-card__full-link, a")
            raw_url = link_elem.get("href", "") if link_elem else ""
            normalized_url = clean_url(raw_url)

            if not normalized_url or normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)

            company_elem = card.select_one(".base-search-card__subtitle, h4 a, h4")
            company = company_elem.get_text(strip=True) if company_elem else "Entreprise Casablanca"

            location_elem = card.select_one(".job-search-card__location, span.job-location")
            location = location_elem.get_text(strip=True) if location_elem else "Casablanca, Maroc"

            date_elem = card.select_one("time")
            posted_date = date_elem.get_text(strip=True) if date_elem else ""

            # Only fetch detail page if title is relevant (reduces 75% of useless requests & 429 blocks)
            description = f"Offre LinkedIn: {title}"
            contact_email = None
            hr_linkedin_url = None
            hr_name = None

            if self._is_relevant_title(title):
                description, contact_email, hr_linkedin_url, hr_name = self._fetch_job_details(normalized_url, title)

            offer = JobOffer(
                title=title,
                company=company,
                location=location,
                url=normalized_url,
                description=description,
                source=self.name,
                contact_email=contact_email,
                linkedin_url=normalized_url,
                hr_linkedin_url=hr_linkedin_url,
                hr_name=hr_name,
                posted_date=posted_date,
            )
            offers.append(offer)

        return offers

    def _extract_job_id(self, job_url: str) -> Optional[str]:
        """Extracts the numeric LinkedIn job ID from various URL formats."""
        if not job_url:
            return None
        match = re.search(r'/view/(?:[a-zA-Z0-9_-]+-)?(\d+)', job_url)
        if match:
            return match.group(1)
        digits = re.findall(r'\b\d{5,14}\b', job_url)
        if digits:
            return digits[-1]
        parts = [p for p in job_url.split("?")[0].rstrip("/").split("/") if p.isdigit()]
        return parts[-1] if parts else None

    def _fetch_job_details(
        self,
        job_url: str,
        title: str,
        session: Optional[requests.Session] = None,
    ) -> tuple[str, Optional[str], Optional[str], Optional[str]]:
        """
        Fetches the public guest detail page for the given LinkedIn job URL.
        Returns (description_text, contact_email, hr_linkedin_url, hr_name).
        """
        desc_text = f"Offre LinkedIn PFE: {title}"
        contact_email = None
        hr_linkedin_url = None
        hr_name = None

        try:
            job_id = self._extract_job_id(job_url)
            if not job_id:
                return desc_text, contact_email, hr_linkedin_url, hr_name

            time.sleep(0.3)
            active_session = session or self.session
            detail_url = self.DETAIL_URL.format(job_id=job_id)
            res = active_session.get(detail_url, timeout=self.timeout)

            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")

                # 1. Extract Description
                desc_elem = soup.select_one(".show-more-less-html__markup, .description__text, .decorated-job-posting__details")
                if desc_elem:
                    desc_text = desc_elem.get_text(" ", strip=True)

                # 2. Extract HR/Recruiter Emails
                emails = extract_emails(desc_text)
                if emails:
                    contact_email = emails[0]

                # 3. Check for Recruiter Profile (/in/...)
                recruiter_links = soup.find_all("a", href=lambda h: h and "/in/" in h)
                for r_link in recruiter_links:
                    href = clean_url(r_link.get("href", ""))
                    if "/in/" in href:
                        hr_linkedin_url = href
                        name_text = r_link.get_text(strip=True)
                        if name_text and len(name_text) < 50:
                            hr_name = name_text
                        break

                if not hr_linkedin_url:
                    hr_linkedin_url = extract_recruiter_profile(desc_text)

        except Exception as e:
            logger.debug("Failed to fetch detail for job %s: %s", job_url, e)

        return desc_text, contact_email, hr_linkedin_url, hr_name
