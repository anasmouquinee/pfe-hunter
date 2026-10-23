"""Telegram notification dispatcher with robust HTML parsing and direct LinkedIn links."""

import html
import requests
from typing import Optional
from src.config import config
from src.models.offer import JobOffer
from src.utils.logger import logger


class TelegramNotifier:
    """Sends real-time PFE alert cards to Anas via Telegram Bot using HTML formatting."""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or config.telegram_bot_token
        self.chat_id = chat_id or config.telegram_chat_id

    def is_configured(self) -> bool:
        return bool(self.bot_token and self.chat_id)

    def format_message(
        self,
        offer: JobOffer,
        email_sent: bool = False,
        status_override: Optional[str] = None,
    ) -> str:
        """
        Formats an offer into a clean HTML card.
        HTML mode avoids Telegram Markdown errors when URLs or names contain underscores ('_').
        """
        remun_icon = "🟢 Rémunéré / Gratifié" if offer.is_remunerated else "⚪ Non précisé"

        if status_override:
            action_text = status_override
        elif email_sent:
            action_text = f"✅ Candidature envoyée avec CV au RH : <code>{html.escape(offer.contact_email or '')}</code>"
        elif offer.contact_email:
            action_text = f"🧪 [Simulation] Email RH détecté : <code>{html.escape(offer.contact_email)}</code>"
        else:
            action_text = "⚠️ Email absent -> Postulation 1-clic ci-dessous"

        skills_str = ", ".join(offer.matched_skills) if offer.matched_skills else "IA / Data"

        safe_title = html.escape(offer.title)
        safe_company = html.escape(offer.company)
        safe_location = html.escape(offer.location)
        safe_skills = html.escape(skills_str)

        msg = (
            f"🎯 <b>NOUVELLE OPPORTUNITÉ STAGE PFE (Match: {offer.score}%)</b>\n\n"
            f"🏢 <b>Entreprise :</b> {safe_company}\n"
            f"📌 <b>Poste :</b> {safe_title}\n"
            f"📍 <b>Ville :</b> {safe_location}\n"
            f"💰 <b>Gratification :</b> {remun_icon}\n"
            f"🛠 <b>Stack :</b> {safe_skills}\n"
            f"📤 <b>Statut Candidature :</b> {action_text}\n"
        )

        if offer.hr_linkedin_url:
            recruiter_label = html.escape(offer.hr_name or "Recruteur RH LinkedIn")
            msg += (
                f"\n👤 <b>Profil Recruteur :</b>\n"
                f"👉 <a href=\"{offer.hr_linkedin_url}\">{recruiter_label}</a> "
                f"<i>(Connectez-vous ou envoyez un message direct)</i>\n"
            )

        if offer.linkedin_url:
            msg += (
                f"\n🔗 <b>Lien LinkedIn :</b>\n"
                f"👉 <a href=\"{offer.linkedin_url}\">Ouvrir l'offre LinkedIn</a>\n"
            )
        elif offer.url:
            msg += (
                f"\n🌐 <b>Lien de l'offre :</b>\n"
                f"👉 <a href=\"{offer.url}\">Consulter l'offre</a>\n"
            )

        return msg

    def send_alert(
        self,
        offer: JobOffer,
        email_sent: bool = False,
        status_override: Optional[str] = None,
    ) -> bool:
        """Sends Telegram alert formatted in HTML with 1-click interactive inline buttons."""
        if not self.is_configured():
            logger.debug("Telegram notifier not configured (skipping).")
            return False

        # Build interactive 1-click buttons
        inline_keyboard = []
        btn_row = []
        target_link = offer.linkedin_url or offer.url
        if target_link:
            btn_row.append({"text": "⚡ Ouvrir l'offre", "url": target_link})
        if offer.hr_linkedin_url:
            btn_row.append({"text": "👤 Contacter le RH", "url": offer.hr_linkedin_url})
        if btn_row:
            inline_keyboard.append(btn_row)

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": self.format_message(offer, email_sent, status_override=status_override),
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }
        if inline_keyboard:
            payload["reply_markup"] = {"inline_keyboard": inline_keyboard}

        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                logger.info("Telegram alert successfully sent for: %s", offer.title)
                return True
            else:
                logger.error("Telegram API error (%s): %s", res.status_code, res.text)
                return False
        except Exception as e:
            logger.error("Failed to send Telegram alert: %s", e)
            return False
