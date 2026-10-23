"""Headless browser automation for LinkedIn Easy Apply submissions."""

import time
from pathlib import Path
from typing import Any, Dict, Optional

from src.config import config
from src.models.offer import JobOffer
from src.utils.logger import logger

# Graceful import check for Playwright
try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    PLAYWRIGHT_INSTALLED = True
except ImportError:
    PLAYWRIGHT_INSTALLED = False
    PlaywrightTimeoutError = Exception


class LinkedInApplier:
    """
    Automates LinkedIn Easy Apply applications using Playwright headless browser
    and authenticated session cookie injection (li_at).
    Runs seamlessly both in Cloud environments (GitHub Actions) and locally.
    """

    def __init__(self, li_at_cookie: Optional[str] = None):
        self.li_at = li_at_cookie or config.linkedin_li_at
        self.dry_run = config.dry_run
        self.cv_path = config.candidate.cv_path

    def is_configured(self) -> bool:
        """Checks if both Playwright and LinkedIn session cookie are available."""
        return PLAYWRIGHT_INSTALLED and bool(self.li_at)

    def apply(self, offer: JobOffer) -> Dict[str, Any]:
        """
        Executes or simulates automated Easy Apply for a LinkedIn offer.
        Returns a dictionary with execution status and details.
        """
        if not PLAYWRIGHT_INSTALLED:
            logger.debug("Playwright not installed; skipping browser auto-apply.")
            return {"status": "skipped", "applied": False, "reason": "playwright_not_installed"}

        if not self.li_at:
            logger.debug("LINKEDIN_LI_AT cookie not configured; skipping browser auto-apply.")
            return {"status": "skipped", "applied": False, "reason": "cookie_not_configured"}

        target_url = offer.linkedin_url or offer.url
        if not target_url or "linkedin.com" not in target_url:
            return {"status": "skipped", "applied": False, "reason": "not_linkedin_url"}

        logger.info("Initializing headless browser for LinkedIn: %s (%s)", offer.company, offer.title)

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

                # Inject authenticated session cookie
                context.add_cookies([
                    {
                        "name": "li_at",
                        "value": self.li_at.strip(),
                        "domain": ".www.linkedin.com",
                        "path": "/",
                        "httpOnly": True,
                        "secure": True,
                    }
                ])

                page = context.new_page()
                page.goto(target_url, timeout=30000, wait_until="domcontentloaded")
                time.sleep(2)

                # Detect Easy Apply button (French & English labels)
                easy_apply_selectors = [
                    "button.jobs-apply-button",
                    "button[aria-label*='Candidature simplifiée']",
                    "button[aria-label*='Easy Apply']",
                    "button[aria-label*='Postuler']",
                    ".jobs-s-apply button",
                ]

                apply_btn = None
                for sel in easy_apply_selectors:
                    elem = page.query_selector(sel)
                    if elem and elem.is_visible():
                        apply_btn = elem
                        break

                if not apply_btn:
                    logger.info("No Easy Apply button detected on %s (External portal required)", target_url)
                    browser.close()
                    return {"status": "external_apply", "applied": False, "reason": "no_easy_apply_button"}

                btn_text = apply_btn.inner_text().strip()
                logger.info("Easy Apply button detected: '%s' on %s", btn_text, offer.title)

                # Simulation Mode
                if self.dry_run:
                    logger.info(
                        "[DRY-RUN] Easy Apply verified successfully for '%s' @ %s (No click performed)",
                        offer.title,
                        offer.company,
                    )
                    browser.close()
                    return {"status": "simulated", "applied": False, "easy_apply_available": True}

                # LIVE Execution
                apply_btn.click()
                time.sleep(2)

                # 1. Fill phone number if empty
                phone_input = page.query_selector("input[id*='phoneNumber'], input[name*='phoneNumber']")
                if phone_input and not phone_input.input_value():
                    phone_input.fill(config.candidate.phone)

                # 2. Upload CV PDF if upload field exists
                file_input = page.query_selector("input[type='file']")
                if file_input and self.cv_path.exists():
                    file_input.set_input_files(str(self.cv_path.resolve()))
                    logger.info("Attached CV PDF %s to LinkedIn Easy Apply modal", self.cv_path.name)
                    time.sleep(1)

                # 3. Check for Next / Review / Submit buttons
                submit_selectors = [
                    "button[aria-label*='Soumettre la candidature']",
                    "button[aria-label*='Submit application']",
                    "button:has-text('Soumettre la candidature')",
                    "button:has-text('Submit application')",
                ]

                submitted = False
                for s_sel in submit_selectors:
                    s_btn = page.query_selector(s_sel)
                    if s_btn and s_btn.is_visible():
                        s_btn.click()
                        submitted = True
                        time.sleep(2)
                        break

                if submitted:
                    logger.info("Successfully submitted Easy Apply application for %s!", offer.title)
                    browser.close()
                    return {"status": "applied", "applied": True}

                # Check if multi-step form has Next button
                next_btn = page.query_selector("button[aria-label*='Suivant'], button[aria-label*='Next'], button:has-text('Suivant')")
                if next_btn and next_btn.is_visible():
                    logger.info("Multi-step questionnaire detected on %s; requires candidate answers", offer.title)
                    browser.close()
                    return {
                        "status": "manual_review_needed",
                        "applied": False,
                        "reason": "multi_step_custom_questions",
                        "easy_apply_available": True,
                    }

                browser.close()
                return {"status": "unresolved_modal", "applied": False}

        except Exception as e:
            logger.error("Error during LinkedIn browser application for %s: %s", offer.title, e)
            return {"status": "error", "applied": False, "error": str(e)}
