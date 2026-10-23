"""Headless browser automation for generic career portals and web application forms."""

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


class GenericWebFormApplier:
    """
    Intelligent form-filler for online job application portals (Emploi.ma, Dreamjob, Talent,
    and direct corporate career pages) using Playwright headless browser.
    """

    def __init__(self):
        self.dry_run = config.dry_run
        self.candidate = config.candidate
        self.cv_path = config.candidate.cv_path

    def is_configured(self) -> bool:
        return PLAYWRIGHT_INSTALLED and bool(self.candidate.email)

    def apply(self, offer: JobOffer) -> Dict[str, Any]:
        """
        Detects, fills, and submits web job application forms automatically.
        """
        if not PLAYWRIGHT_INSTALLED:
            logger.debug("Playwright not installed; skipping generic form auto-apply.")
            return {"status": "skipped", "applied": False, "reason": "playwright_not_installed"}

        if not offer.url:
            return {"status": "skipped", "applied": False, "reason": "missing_url"}

        logger.info("Inspecting web application form for %s @ %s", offer.title, offer.company)

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

                # Check if we need to click an "Apply" button to reveal the form
                apply_triggers = [
                    "button:has-text('Postuler')",
                    "a:has-text('Postuler')",
                    "button:has-text('Apply')",
                    "a:has-text('Apply')",
                    "a:has-text('Candidater')",
                    ".btn-apply",
                    "#btn-apply",
                ]
                for trig in apply_triggers:
                    elem = page.query_selector(trig)
                    if elem and elem.is_visible():
                        # Only click if not a direct external link leaving the domain
                        href = elem.get_attribute("href")
                        if not href or href.startswith("#") or "javascript" in href:
                            elem.click()
                            time.sleep(1)
                            break

                # Form input detection heuristics
                email_input = page.query_selector("input[type='email'], input[name*='email'], input[id*='email']")
                name_input = page.query_selector(
                    "input[name*='nom'], input[name*='name'], input[id*='name'], input[id*='nom']"
                )
                phone_input = page.query_selector(
                    "input[type='tel'], input[name*='phone'], input[name*='tel'], input[id*='phone']"
                )
                file_input = page.query_selector("input[type='file']")
                msg_input = page.query_selector("textarea[name*='message'], textarea[name*='letter'], textarea")

                has_form = bool(email_input or file_input or (name_input and msg_input))

                if not has_form:
                    logger.debug("No standard application form detected on %s", offer.url)
                    browser.close()
                    return {"status": "no_form_detected", "applied": False, "platform": "web_form"}

                # Dry-run validation
                if self.dry_run:
                    logger.info(
                        "[DRY-RUN] Direct application form detected and verified on '%s' @ %s (No submit performed)",
                        offer.title,
                        offer.company,
                    )
                    browser.close()
                    return {
                        "status": "simulated",
                        "applied": False,
                        "platform": "web_form",
                        "form_detected": True,
                    }

                # LIVE Execution
                if name_input and not name_input.input_value():
                    name_input.fill(self.candidate.name)

                if email_input and not email_input.input_value():
                    email_input.fill(self.candidate.email)

                if phone_input and not phone_input.input_value():
                    phone_input.fill(self.candidate.phone)

                if msg_input and not msg_input.input_value():
                    letter_text = CoverLetterGenerator.generate_cover_letter_text(offer)
                    msg_input.fill(letter_text[:1200])

                if file_input and self.cv_path.exists():
                    file_input.set_input_files(str(self.cv_path.resolve()))
                    logger.info("Attached CV %s on web application form", self.cv_path.name)
                    time.sleep(1)

                # Locate submit button
                submit_btn = page.query_selector(
                    "button[type='submit'], input[type='submit'], "
                    "button:has-text('Envoyer'), button:has-text('Postuler'), "
                    "button:has-text('Submit'), input[value*='Envoyer']"
                )

                if submit_btn and submit_btn.is_visible():
                    submit_btn.click()
                    time.sleep(2)
                    logger.info("Successfully submitted web application for %s!", offer.title)
                    browser.close()
                    return {"status": "applied", "applied": True, "platform": "web_form"}

                browser.close()
                return {"status": "form_filled_no_submit_btn", "applied": False, "platform": "web_form"}

        except Exception as e:
            logger.error("Error during web form application for %s: %s", offer.title, e)
            return {"status": "error", "applied": False, "error": str(e), "platform": "web_form"}
