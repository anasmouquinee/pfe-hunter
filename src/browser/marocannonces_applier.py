"""Headless browser automation for MarocAnnonces contact and application submissions."""

import time
from typing import Any, Dict
from src.config import config
from src.models.offer import JobOffer
from src.utils.logger import logger
from src.mailer.cover_letter_generator import CoverLetterGenerator

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    PLAYWRIGHT_INSTALLED = True
except ImportError:
    PLAYWRIGHT_INSTALLED = False
    PlaywrightTimeoutError = Exception


class MarocAnnoncesApplier:
    """
    Automates applications on MarocAnnonces listings via the direct 'Répondre à cette annonce'
    contact form using Playwright headless browser.
    """

    def __init__(self):
        self.dry_run = config.dry_run
        self.candidate = config.candidate
        self.cv_path = config.candidate.cv_path

    def is_configured(self) -> bool:
        """MarocAnnonces requires Playwright and a valid candidate email."""
        return PLAYWRIGHT_INSTALLED and bool(self.candidate.email)

    def apply(self, offer: JobOffer) -> Dict[str, Any]:
        """
        Executes or simulates automated submission on MarocAnnonces.
        Fills candidate name, email, phone, personalized cover message, and attaches CV.
        """
        if not PLAYWRIGHT_INSTALLED:
            logger.debug("Playwright not installed; skipping MarocAnnonces auto-apply.")
            return {"status": "skipped", "applied": False, "reason": "playwright_not_installed"}

        if not offer.url or "marocannonces.com" not in offer.url:
            return {"status": "skipped", "applied": False, "reason": "not_marocannonces_url"}

        logger.info("Initializing headless browser for MarocAnnonces: %s (%s)", offer.company, offer.title)

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=[
                        "--no-sandbox",
                        "--disable-setuid-sandbox",
                        "--disable-dev-shm-usage",
                        "--disable-blink-features=AutomationControlled",
                    ],
                )

                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1280, "height": 800},
                )

                page = context.new_page()
                page.goto(offer.url, timeout=30000, wait_until="domcontentloaded")
                time.sleep(1.5)

                # Look for contact button or apply link directly on the page
                contact_btn = page.query_selector(
                    "a:has-text('Postuler à cette offre'), "
                    "a:has-text('Postuler'), "
                    "a[href*='a=13'], "
                    "a:has-text('Répondre à cette annonce'), "
                    "a:has-text('Contacter l\'annonceur'), "
                    "button:has-text('Répondre'), "
                    ".btn_repondre, #btn_contact"
                )
                if contact_btn and contact_btn.is_visible():
                    logger.info("Clicking MarocAnnonces contact/apply trigger...")
                    contact_btn.click()
                    time.sleep(1.5)

                # Check if phone reveal link is present
                phone_reveal = page.query_selector("#phone_num, a[data-rel='phone_number']")
                if phone_reveal and phone_reveal.is_visible():
                    try:
                        phone_reveal.click()
                        time.sleep(0.5)
                    except Exception:
                        pass

                # Detect form inputs
                name_input = page.query_selector("input[name*='nom'], input[name*='name'], input[id*='nom']")
                email_input = page.query_selector("input[name*='email'], input[type='email']")
                phone_input = page.query_selector("input[name*='tel'], input[name*='phone'], input[type='tel']")
                msg_input = page.query_selector("textarea[name*='message'], textarea[name*='comment'], textarea")

                form_detected = bool(email_input or msg_input)

                if not form_detected:
                    logger.info("No interactive contact form found on MarocAnnonces offer %s", offer.url)
                    browser.close()
                    return {"status": "no_form_found", "applied": False, "platform": "marocannonces"}

                # Dry-run validation
                if self.dry_run:
                    logger.info(
                        "[DRY-RUN] MarocAnnonces application form verified for '%s' @ %s (No submit performed)",
                        offer.title,
                        offer.company,
                    )
                    browser.close()
                    return {
                        "status": "simulated",
                        "applied": False,
                        "platform": "marocannonces",
                        "form_detected": True,
                    }

                # LIVE Execution
                if name_input and not name_input.input_value():
                    name_input.fill(self.candidate.name)

                if email_input and not email_input.input_value():
                    email_input.fill(self.candidate.email)

                if phone_input and not phone_input.input_value():
                    phone_input.fill(self.candidate.phone)

                if msg_input:
                    cover_letter = CoverLetterGenerator.generate_cover_letter_text(offer)
                    msg_input.fill(cover_letter[:1500])

                # Attach CV if file input is available
                file_input = page.query_selector("input[type='file']")
                if file_input and self.cv_path.exists():
                    file_input.set_input_files(str(self.cv_path.resolve()))
                    logger.info("Attached CV %s on MarocAnnonces form", self.cv_path.name)

                # Submit button
                submit_btn = page.query_selector(
                    "input[type='submit'], button[type='submit'], "
                    "button:has-text('Envoyer'), input[value*='Envoyer']"
                )
                if submit_btn and submit_btn.is_visible():
                    submit_btn.click()
                    time.sleep(2)
                    logger.info("Submitted MarocAnnonces contact application for %s!", offer.title)
                    browser.close()
                    return {"status": "applied", "applied": True, "platform": "marocannonces"}

                browser.close()
                return {"status": "form_found_no_submit_btn", "applied": False, "platform": "marocannonces"}

        except Exception as e:
            logger.error("Error during MarocAnnonces application for %s: %s", offer.title, e)
            return {"status": "error", "applied": False, "error": str(e), "platform": "marocannonces"}
