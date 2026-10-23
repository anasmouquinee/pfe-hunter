"""Headless browser automation for ReKrute job applications."""

import time
from typing import Any, Dict, Optional
from src.config import config
from src.models.offer import JobOffer
from src.utils.logger import logger

try:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    PLAYWRIGHT_INSTALLED = True
except ImportError:
    PLAYWRIGHT_INSTALLED = False
    PlaywrightTimeoutError = Exception


class ReKruteApplier:
    """
    Automates applications on ReKrute using Playwright headless browser.
    Supports candidate session authentication and automated 1-click 'Postuler' submission.
    """

    LOGIN_URL = "https://www.rekrute.com/candidat-connexion.html"

    def __init__(self, email: Optional[str] = None, password: Optional[str] = None):
        self.email = email or config.rekrute_email
        self.password = password or config.rekrute_password
        self.dry_run = config.dry_run
        self.cv_path = config.candidate.cv_path

    def is_configured(self) -> bool:
        """ReKrute application is ready if Playwright is installed and email is configured."""
        return PLAYWRIGHT_INSTALLED and bool(self.email)

    def apply(self, offer: JobOffer) -> Dict[str, Any]:
        """
        Executes or simulates automated application on a ReKrute job offer.
        """
        if not PLAYWRIGHT_INSTALLED:
            logger.debug("Playwright not installed; skipping ReKrute auto-apply.")
            return {"status": "skipped", "applied": False, "reason": "playwright_not_installed"}

        if not offer.url or "rekrute.com" not in offer.url:
            return {"status": "skipped", "applied": False, "reason": "not_rekrute_url"}

        logger.info("Initializing headless browser for ReKrute: %s (%s)", offer.company, offer.title)

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

                # Step 1: Login if credentials are provided
                if self.email and self.password and not self.dry_run:
                    logger.info("Logging into ReKrute with account %s", self.email)
                    page.goto(self.LOGIN_URL, timeout=30000, wait_until="domcontentloaded")
                    time.sleep(1)

                    email_field = page.query_selector("input[name*='email'], input[id*='email'], input[type='email']")
                    pwd_field = page.query_selector("input[name*='pass'], input[id*='pass'], input[type='password']")
                    login_btn = page.query_selector("input[type='submit'], button[type='submit'], button:has-text('Connexion')")

                    if email_field and pwd_field and login_btn:
                        email_field.fill(self.email)
                        pwd_field.fill(self.password)
                        login_btn.click()
                        time.sleep(2)

                # Step 2: Navigate to the target offer
                page.goto(offer.url, timeout=30000, wait_until="domcontentloaded")
                time.sleep(1.5)

                # Detect Postuler button
                postuler_selectors = [
                    "a.postuler",
                    ".btn-postuler",
                    "a:has-text('Postuler')",
                    "button:has-text('Postuler')",
                    "a[href*='postuler']",
                    "input[value*='Postuler']",
                ]

                postuler_btn = None
                for sel in postuler_selectors:
                    elem = page.query_selector(sel)
                    if elem and elem.is_visible():
                        postuler_btn = elem
                        break

                if not postuler_btn:
                    logger.info("No 'Postuler' button detected on ReKrute offer %s", offer.url)
                    browser.close()
                    return {"status": "no_button", "applied": False, "platform": "rekrute"}

                # Dry-run validation
                if self.dry_run:
                    logger.info(
                        "[DRY-RUN] ReKrute 'Postuler' button detected and validated for '%s' @ %s (No click performed)",
                        offer.title,
                        offer.company,
                    )
                    browser.close()
                    return {
                        "status": "simulated",
                        "applied": False,
                        "platform": "rekrute",
                        "postuler_available": True,
                    }

                # LIVE Execution
                postuler_btn.click()
                time.sleep(2)

                # Check for confirm modal / CV selection
                confirm_btn = page.query_selector(
                    "button:has-text('Confirmer'), "
                    "input[value*='Confirmer'], "
                    "button:has-text('Envoyer ma candidature'), "
                    "a:has-text('Confirmer')"
                )
                if confirm_btn and confirm_btn.is_visible():
                    confirm_btn.click()
                    time.sleep(2)
                    logger.info("Confirmed ReKrute application submission for %s!", offer.title)
                    browser.close()
                    return {"status": "applied", "applied": True, "platform": "rekrute"}

                browser.close()
                return {"status": "postuler_clicked", "applied": True, "platform": "rekrute"}

        except Exception as e:
            logger.error("Error during ReKrute browser application for %s: %s", offer.title, e)
            return {"status": "error", "applied": False, "error": str(e), "platform": "rekrute"}
