"""Joblia.ma scraper for Moroccan corporate PFE campaigns and tech opportunities."""

import json
import re
import time
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from typing import List, Optional, Tuple
from src.scrapers.base import BaseScraper
from src.models.offer import JobOffer
from src.utils.text_extractor import clean_url, extract_emails, extract_linkedin_urls, extract_recruiter_profile
from src.utils.logger import logger


class JobliaScraper(BaseScraper):
    """
    Scrapes Joblia.ma, a prominent Moroccan job aggregator for corporate recruitment campaigns,
    PFE internship campaigns, and tech opportunities.
    Extracts publication date, direct application links (LinkedIn, ReKrute, corporate portals),
    and HR contact emails.
    """
    name: str = "joblia"
    BASE_URL = "https://joblia.ma"

    RELEVANT_PATTERNS = [
        r'\bstage\b',
        r'\bpfe\b',
        r'\bdata\b',
        r'\bia\b',
        r'\bai\b',
        r'intelligence artificielle',
        r'machine learning',
        r'python',
        r'stagiaire',
        r'ingénieur',
        r'ingenieur',
        r'engineer',
        r'développeur',
        r'developpeur',
        r'informatique',
        r'pré-embauche',
        r'pre-embauche',
        r'consultant',
        r'cloud',
    ]

    def _is_relevant_title(self, title: str) -> bool:
        """Determines if the article title is relevant to engineering/internships before fetching details."""
        title_lower = title.lower()
        return any(re.search(pat, title_lower) for pat in self.RELEVANT_PATTERNS)

    def scrape(self, keyword: str = "stage pfe data", location: str = "Casablanca", max_pages: int = 2) -> List[JobOffer]:
        offers: List[JobOffer] = []
        search_query = quote_plus(keyword)

        for page in range(1, max_pages + 1):
            if page == 1:
                url = f"{self.BASE_URL}/?s={search_query}"
            else:
                url = f"{self.BASE_URL}/page/{page}/?s={search_query}"

            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code != 200:
                    if page == 1:
                        logger.warning("Joblia returned HTTP %s for query '%s'", response.status_code, keyword)
                    break

                soup = BeautifulSoup(response.text, "html.parser")
                parsed = self.parse_html(soup)
                offers.extend(parsed)
            except Exception as e:
                logger.error("Error scraping Joblia page %d for '%s': %s", page, keyword, e)
                break

        logger.info("Joblia found %d offers for '%s'", len(offers), keyword)
        return offers

    def _extract_company_from_title(self, title: str) -> str:
        """Heuristically extracts company name from Joblia campaign titles."""
        patterns = [
            r'^([A-Za-z0-9\s.&_-]+?)\s+(?:lance|recrute|ouvre|cherche|organise|embauche)',
            r'(?:chez|at)\s+([A-Za-z0-9\s.&_-]+?)(?:\s*[-–:]|\s+lance|\s+recrute|\s+au|\s+en|\s*$)',
            r'Rejoignez\s+([A-Za-z0-9.&_-]+(?:\s+[A-Za-z0-9.&_-]+)?)',
        ]
        for p in patterns:
            match = re.search(p, title, re.IGNORECASE)
            if match:
                candidate = match.group(1).strip(" :,-–")
                if 2 < len(candidate) < 35:
                    return candidate
        return "Entreprise Maroc"

    def _fetch_article_details(self, article_url: str) -> Tuple[str, Optional[str], Optional[str], Optional[str], str]:
        """
        Fetches the full campaign article page to discover HR contact emails,
        application links, recruiter profiles, and ISO publication dates.
        """
        desc_text = ""
        contact_email = None
        linkedin_url = None
        hr_linkedin_url = None
        posted_date = ""

        try:
            time.sleep(0.2)
            res = self.session.get(article_url, timeout=self.timeout)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")

                # 1. Extract publication date from JSON-LD schema or time tag
                time_tag = soup.select_one("time")
                if time_tag:
                    posted_date = time_tag.get("datetime", time_tag.get_text(strip=True))

                if not posted_date:
                    for s in soup.find_all("script", type="application/ld+json"):
                        try:
                            data = json.loads(s.string)
                            for item in data.get("@graph", [data]):
                                if "datePublished" in item:
                                    posted_date = item["datePublished"]
                                    break
                        except Exception:
                            pass

                # 2. Extract description text
                content_elem = soup.select_one(".entry-content, .post-content, article")
                if content_elem:
                    desc_text = content_elem.get_text(" ", strip=True)

                    # 3. Extract direct HR emails (exclude internal joblia support)
                    all_emails = extract_emails(desc_text)
                    valid_emails = [e for e in all_emails if not e.endswith("joblia.ma")]
                    if valid_emails:
                        contact_email = valid_emails[0]

                    # 4. Extract apply button link / external URL
                    for a in content_elem.find_all("a", href=True):
                        txt = a.get_text(strip=True).lower()
                        if any(w in txt for w in ["postuler", "candidater", "déposer", "postulez"]):
                            href = clean_url(a["href"])
                            if "linkedin.com" in href:
                                linkedin_url = href
                            elif not contact_email and href.startswith("mailto:"):
                                mail = href.replace("mailto:", "").split("?")[0].strip()
                                if not mail.endswith("joblia.ma"):
                                    contact_email = mail
                            break

                    # 5. Extract LinkedIn profiles if present
                    li_urls = extract_linkedin_urls(desc_text)
                    if li_urls and not linkedin_url:
                        linkedin_url = li_urls[0]

                    hr_profile = extract_recruiter_profile(desc_text)
                    if hr_profile:
                        hr_linkedin_url = hr_profile

        except Exception as e:
            logger.debug("Failed to fetch Joblia details for %s: %s", article_url, e)

        return desc_text, contact_email, linkedin_url, hr_linkedin_url, posted_date

    def parse_html(self, soup: BeautifulSoup) -> List[JobOffer]:
        offers: List[JobOffer] = []
        seen_urls = set()
        articles = soup.select("article, .post-item, div.post")

        for article in articles:
            title_elem = article.select_one("h2.entry-title a, h2 a, h3 a, a.entry-title-link")
            if not title_elem:
                continue

            title = title_elem.get_text(strip=True)
            raw_url = title_elem.get("href", "")
            url = clean_url(raw_url)

            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            company = self._extract_company_from_title(title)

            # Fallback date from article element if present
            date_elem = article.select_one("time, .post-date, .entry-date")
            posted_date = date_elem.get_text(strip=True) if date_elem else ""

            # Check relevance before fetching details to preserve latency & bandwidth
            detail_desc, contact_email, li_url, hr_url, detail_date = "", None, None, None, ""
            if self._is_relevant_title(title):
                detail_desc, contact_email, li_url, hr_url, detail_date = self._fetch_article_details(url)
                if detail_date:
                    posted_date = detail_date

            full_desc = detail_desc if detail_desc else title

            offer = JobOffer(
                title=title,
                company=company,
                location="Casablanca, Maroc",
                url=url,
                description=full_desc,
                source=self.name,
                contact_email=contact_email,
                linkedin_url=li_url,
                hr_linkedin_url=hr_url,
                posted_date=posted_date,
            )
            offers.append(offer)

        return offers
