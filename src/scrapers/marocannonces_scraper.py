"""MarocAnnonces scraper for Moroccan PFE and tech opportunities."""

import re
from typing import List, Optional
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from src.scrapers.base import BaseScraper
from src.models.offer import JobOffer
from src.utils.text_extractor import clean_url, extract_emails
from src.utils.logger import logger


class MarocAnnoncesScraper(BaseScraper):
    name: str = "marocannonces"
    BASE_URL = "https://www.marocannonces.com"

    def _normalize_search_keyword(self, keyword: str) -> str:
        """Adapts long queries to single high-converting search keywords for MarocAnnonces."""
        kw = keyword.lower()
        if "developp" in kw or "développ" in kw or "web" in kw or "fullstack" in kw or "backend" in kw:
            return "developpeur"
        elif "informatique" in kw or "software" in kw:
            return "informatique"
        elif "pfe" in kw:
            return "pfe"
        elif "data" in kw:
            return "data"
        elif "ia" in kw or "intelligence" in kw or "machine learning" in kw:
            return "ia"
        elif "stage" in kw or "stagiaire" in kw:
            return "stage"
        return kw.split()[0] if kw.split() else "stage"

    def scrape(self, keyword: str = "stage", location: str = "Casablanca") -> List[JobOffer]:
        offers: List[JobOffer] = []
        target_kw = self._normalize_search_keyword(keyword)
        search_query = quote_plus(target_kw)
        
        # Category 309 corresponds to 'Offres d'emploi' (enterprise job postings)
        url = f"{self.BASE_URL}/maroc/offres-emploi-casablanca-b309.html?kw={search_query}"

        try:
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code != 200:
                logger.warning("MarocAnnonces returned HTTP %s for query '%s'", response.status_code, target_kw)
                return offers

            soup = BeautifulSoup(response.text, "html.parser")
            parsed_offers = self.parse_html(soup)
            logger.info("MarocAnnonces found %d offers for '%s' (queried as '%s')", len(parsed_offers), keyword, target_kw)
            return parsed_offers
        except Exception as e:
            logger.error("Error scraping MarocAnnonces for '%s': %s", keyword, e)
            return offers

    def _fetch_ad_detail(self, ad_url: str) -> Optional[str]:
        """Fetches full description and contact details from the MarocAnnonces ad page."""
        try:
            res = self.session.get(ad_url, timeout=self.timeout)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                desc_elem = soup.select_one("div.desccatemploi, div.description, div.parameter")
                if desc_elem:
                    return desc_elem.get_text(" ", strip=True)
        except Exception as e:
            logger.debug("Failed to fetch MarocAnnonces detail for %s: %s", ad_url, e)
        return None

    def parse_html(self, soup: BeautifulSoup) -> List[JobOffer]:
        offers: List[JobOffer] = []
        seen_urls = set()
        cards = soup.select("ul.cars-list li")

        for card in cards:
            a_elem = card.find("a")
            if not a_elem:
                continue

            h3_elem = a_elem.find("h3")
            title = h3_elem.get_text(strip=True) if h3_elem else a_elem.get_text(strip=True)
            if not title:
                continue

            raw_href = a_elem.get("href", "")
            if not raw_href:
                continue

            full_url = f"{self.BASE_URL}/{raw_href.lstrip('/')}"
            url = clean_url(full_url)

            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Location / City
            loc_elem = card.select_one(".location, .used-car-city, span.city")
            location_text = loc_elem.get_text(strip=True) if loc_elem else "Casablanca, Maroc"

            # Date
            date_elem = card.select_one(".date, span.date")
            posted_date = date_elem.get_text(strip=True) if date_elem else ""

            # Description snippet
            desc_elem = card.select_one("p, .desc")
            desc_text = desc_elem.get_text(" ", strip=True) if desc_elem else title

            # If title is relevant to tech/internship, fetch full ad details to extract email
            contact_email = None
            if any(term in title.lower() for term in ("stage", "pfe", "dev", "data", "informatique", "web", "ingenieur")):
                full_detail = self._fetch_ad_detail(url)
                if full_detail:
                    desc_text = full_detail
                    emails = extract_emails(full_detail)
                    if emails:
                        contact_email = emails[0]

            if not contact_email:
                emails = extract_emails(desc_text)
                contact_email = emails[0] if emails else None

            offer = JobOffer(
                title=title,
                company="Entreprise Partenaire (MarocAnnonces)",
                location=location_text,
                url=url,
                description=desc_text,
                source=self.name,
                contact_email=contact_email,
                posted_date=posted_date,
            )
            offers.append(offer)

        return offers
