"""Multi-provider email dispatcher with Resend API (Primary Cloud) and Gmail SMTP fallback."""

import base64
import smtplib
import time
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import requests

from src.config import config
from src.mailer.cover_letter_generator import CoverLetterGenerator
from src.models.offer import JobOffer
from src.utils.logger import logger


class EmailSender:
    """
    Dispatches application emails with attached CV.
    Supports Resend REST API (Cloud-friendly, 0% SMTP blocking) with automatic
    fallback to Gmail SMTP.
    """

    def __init__(self):
        self.resend_api_key = config.resend_api_key
        self.resend_from_email = config.resend_from_email
        self.smtp_host = "smtp.gmail.com"
        self.smtp_port = 465
        self.sender_email = config.gmail_user
        self.app_password = config.gmail_app_password
        self.dry_run = config.dry_run
        self.cv_path = config.candidate.cv_path

    def _send_via_resend(
        self,
        recipient: str,
        subject: str,
        plain_body: str,
        html_body: str,
        offer_title: str,
    ) -> bool:
        """Sends application email via Resend REST API (Cloud Free Tier, 3000 emails/mo)."""
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {self.resend_api_key}",
            "Content-Type": "application/json",
        }

        attachments = []
        if self.cv_path.exists():
            with open(self.cv_path, "rb") as f:
                b64_content = base64.b64encode(f.read()).decode("utf-8")
                cand_slug = config.candidate.full_name.replace(" ", "_")
                attachments.append({
                    "filename": f"CV_{cand_slug}_PFE.pdf",
                    "content": b64_content,
                })
        else:
            logger.warning("CV file %s not found for attachment!", self.cv_path)

        sender_header = f"{config.candidate.full_name} <{self.resend_from_email}>"
        payload = {
            "from": sender_header,
            "to": [recipient],
            "reply_to": config.candidate.email,
            "subject": subject,
            "text": plain_body,
            "html": html_body,
        }
        if attachments:
            payload["attachments"] = attachments

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=20)
            if res.status_code in (200, 201):
                logger.info(
                    "Application email successfully sent via Resend API to %s for '%s'!",
                    recipient,
                    offer_title,
                )
                return True
            else:
                logger.error("Resend API error (HTTP %s): %s", res.status_code, res.text)
                return False
        except Exception as e:
            logger.error("Failed to send email via Resend to %s: %s", recipient, e)
            return False

    def _send_via_smtp(
        self,
        recipient: str,
        subject: str,
        plain_body: str,
        html_body: str,
        offer_title: str,
    ) -> bool:
        """Sends application email via standard SSL SMTP (Gmail)."""
        if not self.app_password:
            logger.error(
                "Cannot send email to %s: GMAIL_APP_PASSWORD is not set!", recipient
            )
            return False

        try:
            msg = MIMEMultipart("mixed")
            msg["From"] = f"{config.candidate.full_name} <{self.sender_email}>"
            msg["To"] = recipient
            msg["Subject"] = subject

            alt_container = MIMEMultipart("alternative")
            alt_container.attach(MIMEText(plain_body, "plain", "utf-8"))
            alt_container.attach(MIMEText(html_body, "html", "utf-8"))
            msg.attach(alt_container)

            if self.cv_path.exists():
                with open(self.cv_path, "rb") as f:
                    part = MIMEApplication(f.read(), _subtype="pdf")
                    cand_slug = config.candidate.full_name.replace(" ", "_")
                    part.add_header(
                        "Content-Disposition",
                        "attachment",
                        filename=f"CV_{cand_slug}_PFE.pdf",
                    )
                    msg.attach(part)
            else:
                logger.warning("CV file %s not found for attachment!", self.cv_path)

            with smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=20) as server:
                server.login(self.sender_email, self.app_password)
                server.send_message(msg)

            logger.info(
                "Application email successfully sent via Gmail SMTP to %s for '%s'!",
                recipient,
                offer_title,
            )
            return True
        except Exception as e:
            logger.error("Failed to send email via Gmail SMTP to %s: %s", recipient, e)
            return False

    def send_application(self, offer: JobOffer, to_email: Optional[str] = None) -> bool:
        """
        Sends application email for the given offer to recruiter.
        Prioritizes Resend API, falling back to Gmail SMTP if needed.
        """
        recipient = to_email or offer.contact_email
        if not recipient:
            logger.warning("No recipient email found for offer '%s'", offer.title)
            return False

        subject = CoverLetterGenerator.generate_subject(offer)
        plain_body = CoverLetterGenerator.generate_body(offer)
        html_body = CoverLetterGenerator.generate_html_body(offer)

        # Simulation Mode
        if self.dry_run:
            provider = "Resend API" if self.resend_api_key else "Gmail SMTP"
            logger.info(
                "[DRY-RUN] Simulating email send via %s to: %s | Subject: '%s' | CV: %s (exists=%s)",
                provider,
                recipient,
                subject,
                self.cv_path.name,
                self.cv_path.exists(),
            )
            return True

        # Polite rate limiting between real email dispatches to prevent spam flags
        time.sleep(1.5)

        # 1. Primary Cloud Provider: Resend REST API
        if self.resend_api_key:
            resend_ok = self._send_via_resend(
                recipient, subject, plain_body, html_body, offer.title
            )
            if resend_ok:
                return True
            logger.warning("Resend dispatch failed; attempting fallback to Gmail SMTP...")

        # 2. Secondary Provider: Gmail SMTP
        return self._send_via_smtp(
            recipient, subject, plain_body, html_body, offer.title
        )

