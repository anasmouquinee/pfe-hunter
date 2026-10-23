"""ReKrute scraper for Moroccan PFE and tech opportunities across Morocco."""

import re
from typing import List, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from src.scrapers.base import BaseScraper
from src.models.offer import JobOffer
from src.utils.logger import logger
from src.utils.text_extractor import clean_url, extract_emails, extract_linkedin_urls


class ReKruteScraper(BaseScraper):
    name: str = "rekrute"
    BASE_URL = "https://www.rekrute.com"

    def scrape(self, keyword: str = "stage pfe", location: str = "Casablanca", max_pages: int = 2) -> List[JobOffer]:
        offers: List[JobOffer] = []
        seen_urls = set()
        search_query = quote_plus(keyword)

        for page in range(1, max_pages + 1):
            url = f"{self.BASE_URL}/offres-emploi-maroc.html?keyword={search_query}&p={page}"

            try:
                response = self.session.get(url, timeout=self.timeout)
                if response.status_code != 200:
                    if page == 1:
                        logger.warning("ReKrute returned status %s for query '%s'", response.status_code, keyword)
                    break

                soup = BeautifulSoup(response.text, "html.parser")
                page_offers = self.parse_html(soup)
                if not page_offers:
                    break

                for off in page_offers:
                    if off.url not in seen_urls:
                        seen_urls.add(off.url)
                        offers.append(off)

            except Exception as e:
                logger.error("Error scraping ReKrute page %d for '%s': %s", page, keyword, e)
                break

        logger.info("ReKrute found %d offers for '%s'", len(offers), keyword)
        return offers

    def _fetch_offer_detail(self, detail_url: str) -> Optional[str]:
        """Optionally fetches the full job description from ReKrute offer page."""
        try:
            res = self.session.get(detail_url, timeout=self.timeout)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                content_elem = soup.select_one("#recruiterDescription, .contentJob, div.col-sm-12")
                if content_elem:
                    return content_elem.get_text(" ", strip=True)
        except Exception as e:
            logger.debug("Failed to fetch ReKrute detail for %s: %s", detail_url, e)
        return None

    def parse_html(self, soup: BeautifulSoup) -> List[JobOffer]:
        offers: List[JobOffer] = []
        cards = soup.select(".post-id")

        for card in cards:
            title_elem = card.select_one(".titreJob, h2 a, h3 a, a.title")
            if not title_elem:
                continue

            raw_title = title_elem.get_text(strip=True)
            href = title_elem.get("href", "")
            raw_url = f"{self.BASE_URL}{href}" if href.startswith("/") else href
            url = clean_url(raw_url)

            # Extract location from title (e.g. "Poste | Casablanca (Maroc)")
            location = "Casablanca, Maroc"
            if "|" in raw_title:
                parts = raw_title.split("|")
                title = parts[0].strip()
                location = parts[-1].strip()
            else:
                title = raw_title

            # Company name extraction from logo or text
            company = "Entreprise Partenaire (ReKrute)"
            photo_elem = card.select_one("img.photo, img[alt]")
            if photo_elem:
                company = photo_elem.get("title") or photo_elem.get("alt") or company
            else:
                comp_elem = card.select_one(".company, .info a")
                if comp_elem and comp_elem.get_text(strip=True):
                    company = comp_elem.get_text(strip=True)

            # Snippet description
            info_elem = card.select_one("div.holder .info span, .holder .info, .info, .text")
            snippet = info_elem.get_text(" ", strip=True) if info_elem else title

            # Date extraction (Publication : du DD/MM/YYYY)
            posted_date = ""
            date_elem = card.select_one("em.date, .date, span.date")
            if date_elem:
                date_match = re.search(r'(\d{2}/\d{2}/\d{4})', date_elem.get_text())
                if date_match:
                    posted_date = date_match.group(1)

            # Emails and LinkedIn links
            emails = extract_emails(snippet)
            contact_email = emails[0] if emails else None
            linkedin_urls = extract_linkedin_urls(snippet)
            linkedin_url = linkedin_urls[0] if linkedin_urls else None

            # If tech/PFE relevant and no email in snippet, fetch detail page
            full_desc = snippet
            if not contact_email and any(kw in title.lower() for kw in ("pfe", "stage", "data", "ia", "dev", "engineer")):
                detail_text = self._fetch_offer_detail(url)
                if detail_text:
                    full_desc = f"{snippet} -- {detail_text}"
                    detail_emails = extract_emails(detail_text)
                    if detail_emails:
                        contact_email = detail_emails[0]

            offer = JobOffer(
                title=title,
                company=company,
                location=location,
                url=url,
                description=full_desc,
                source=self.name,
                contact_email=contact_email,
                linkedin_url=linkedin_url,
                posted_date=posted_date,
            )
            offers.append(offer)

        return offers
