"""Headless browser automation for LinkedIn Easy Apply submissions."""

import re
import time
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
    Supports multi-step application wizards (Contact -> CV -> Screening -> Review -> Submit).
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
        Navigates through the multi-step application wizard to completion.
        """
        if not PLAYWRIGHT_INSTALLED:
            logger.debug("Playwright not installed; skipping LinkedIn browser auto-apply.")
            return {"status": "skipped", "applied": False, "reason": "playwright_not_installed"}

        if not self.li_at:
            logger.debug("LINKEDIN_LI_AT cookie not configured; skipping LinkedIn browser auto-apply.")
            return {"status": "skipped", "applied": False, "reason": "cookie_not_configured"}

        raw_url = offer.linkedin_url or offer.url or ""
        if not raw_url or "linkedin.com" not in raw_url:
            return {"status": "skipped", "applied": False, "reason": "not_linkedin_url"}

        # Normalize country subdomains (ma.linkedin.com, fr.linkedin.com) to canonical www.linkedin.com
        target_url = re.sub(r"https://[a-z]{2}\.linkedin\.com/", "https://www.linkedin.com/", raw_url)

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

                # Inject authenticated session cookie across all LinkedIn subdomains
                context.add_cookies([
                    {
                        "name": "li_at",
                        "value": self.li_at.strip(),
                        "domain": ".linkedin.com",
                        "path": "/",
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "None",
                    },
                    {
                        "name": "li_at",
                        "value": self.li_at.strip(),
                        "domain": ".www.linkedin.com",
                        "path": "/",
                        "httpOnly": True,
                        "secure": True,
                        "sameSite": "None",
                    },
                ])

                page = context.new_page()
                page.goto(target_url, timeout=35000, wait_until="domcontentloaded")
                time.sleep(2)

                # Detect Easy Apply button (French & English labels, desktop & top-card variations)
                easy_apply_selectors = [
                    "button.jobs-apply-button",
                    "button[aria-label*='Candidature simplifiée']",
                    "button[aria-label*='Easy Apply']",
                    "button:has-text('Candidature simplifiée')",
                    "button:has-text('Easy Apply')",
                    ".jobs-s-apply button",
                    "div.jobs-apply-button--top-card button",
                ]

                apply_btn = None
                for sel in easy_apply_selectors:
                    elem = page.query_selector(sel)
                    if elem and elem.is_visible():
                        apply_btn = elem
                        break

                if not apply_btn:
                    logger.info("No Easy Apply button detected on %s (External portal or non-Easy Apply)", target_url)
                    browser.close()
                    return {"status": "external_apply", "applied": False, "reason": "no_easy_apply_button"}

                btn_text = apply_btn.inner_text().strip()
                logger.info("Easy Apply button confirmed: '%s' on %s", btn_text, offer.title)

                # Simulation Mode
                if self.dry_run:
                    logger.info(
                        "[DRY-RUN] Easy Apply verified successfully for '%s' @ %s (No click performed)",
                        offer.title,
                        offer.company,
                    )
                    browser.close()
                    return {"status": "simulated", "applied": False, "easy_apply_available": True}

                # LIVE Execution: Open the Easy Apply modal
                apply_btn.click()
                time.sleep(2)

                # Navigate through the multi-step application wizard
                max_wizard_steps = 7
                current_step = 0
                submitted = False

                while current_step < max_wizard_steps:
                    current_step += 1
                    time.sleep(1.5)

                    # 1. Check if final Submit button is present
                    submit_selectors = [
                        "button[aria-label*='Soumettre la candidature']",
                        "button[aria-label*='Submit application']",
                        "button:has-text('Soumettre la candidature')",
                        "button:has-text('Submit application')",
                        "button:has-text('Soumettre')",
                        "button:has-text('Submit')",
                    ]
                    submit_btn = None
                    for s_sel in submit_selectors:
                        s_elem = page.query_selector(s_sel)
                        if s_elem and s_elem.is_visible():
                            submit_btn = s_elem
                            break

                    if submit_btn:
                        logger.info("Final Submit button found on step %d for %s; submitting!", current_step, offer.title)
                        submit_btn.click()
                        time.sleep(3)
                        # Dismiss confirmation modal if present
                        dismiss_btn = page.query_selector(
                            "button[aria-label*='Ignorer'], button[aria-label*='Dismiss'], "
                            "button:has-text('Terminé'), button:has-text('Done')"
                        )
                        if dismiss_btn and dismiss_btn.is_visible():
                            dismiss_btn.click()
                        submitted = True
                        break

                    # 2. Fill Phone number if empty
                    phone_input = page.query_selector("input[id*='phoneNumber'], input[name*='phoneNumber'], input[type='tel']")
                    if phone_input and phone_input.is_visible() and not phone_input.input_value():
                        phone_input.fill(config.candidate.phone)

                    # 3. Handle CV upload or resume selection
                    file_input = page.query_selector("input[type='file']")
                    if file_input and self.cv_path.exists():
                        try:
                            file_input.set_input_files(str(self.cv_path.resolve()))
                            logger.info("Uploaded CV PDF %s on step %d", self.cv_path.name, current_step)
                            time.sleep(1)
                        except Exception as e:
                            logger.debug("CV file upload step skipped: %s", e)

                    resume_radio = page.query_selector("input[type='radio'][id*='resume'], .jobs-document-upload__title input[type='radio']")
                    if resume_radio and not resume_radio.is_checked():
                        try:
                            resume_radio.check()
                        except Exception:
                            pass

                    # 4. Handle common screening questions
                    yes_labels = page.query_selector_all("label:has-text('Oui'), label:has-text('Yes')")
                    for yl in yes_labels:
                        try:
                            if yl.is_visible():
                                yl.click()
                        except Exception:
                            pass

                    numeric_inputs = page.query_selector_all("input[type='text'][id*='numeric'], input[type='number']")
                    for num_inp in numeric_inputs:
                        try:
                            if num_inp.is_visible() and not num_inp.input_value():
                                num_inp.fill("1")
                        except Exception:
                            pass

                    # 5. Look for Review button
                    review_btn = page.query_selector(
                        "button[aria-label*='Vérifier'], button[aria-label*='Review'], "
                        "button:has-text('Vérifier'), button:has-text('Review')"
                    )
                    if review_btn and review_btn.is_visible():
                        review_btn.click()
                        continue

                    # 6. Look for Next (Suivant) button
                    next_btn = page.query_selector(
                        "button[aria-label*='Suivant'], button[aria-label*='Next'], "
                        "button:has-text('Suivant'), button:has-text('Next')"
                    )
                    if next_btn and next_btn.is_visible():
                        next_btn.click()
                        continue

                    # If no forward button exists
                    logger.info("No forward progression button found on step %d for %s", current_step, offer.title)
                    break

                if submitted:
                    logger.info("Successfully completed LinkedIn Easy Apply for %s!", offer.title)
                    browser.close()
                    return {"status": "applied", "applied": True}

                # If wizard couldn't finish automatically due to complex questions
                logger.info("Multi-step wizard requires specific recruiter answers for %s", offer.title)
                browser.close()
                return {
                    "status": "manual_review_needed",
                    "applied": False,
                    "reason": "complex_screening_questions",
                    "easy_apply_available": True,
                }

        except Exception as e:
            logger.error("Error during LinkedIn browser application for %s: %s", offer.title, e)
            return {"status": "error", "applied": False, "error": str(e)}
