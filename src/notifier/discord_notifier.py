"""Discord webhook notification dispatcher with rich embeds and direct LinkedIn links."""

import requests
from typing import Optional
from src.config import config
from src.models.offer import JobOffer
from src.utils.logger import logger


class DiscordNotifier:
    """Sends real-time PFE alert cards to Anas via Discord Webhook."""

    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or config.discord_webhook_url

    def is_configured(self) -> bool:
        return bool(self.webhook_url)

    def _truncate(self, text: str, max_length: int = 1000) -> str:
        """Safely truncates string values to avoid Discord API 400 Bad Request."""
        if not text:
            return ""
        return text if len(text) <= max_length else text[:max_length - 3] + "..."

    def send_alert(
        self,
        offer: JobOffer,
        email_sent: bool = False,
        status_override: Optional[str] = None,
    ) -> bool:
        """Sends rich Discord embed alert."""
        if not self.is_configured():
            logger.debug("Discord notifier not configured (skipping).")
            return False

        color = 0x22C55E if offer.is_remunerated else 0x3B82F6  # Green if remunerated, Blue otherwise
        remun_text = "🟢 Rémunéré / Gratifié" if offer.is_remunerated else "⚪ Non précisé"

        if status_override:
            action_text = status_override
        elif email_sent:
            action_text = f"✅ Email envoyé avec CV au RH : `{offer.contact_email}`"
        elif offer.contact_email:
            action_text = f"🧪 [Simulation] Email RH détecté : `{offer.contact_email}`"
        else:
            action_text = "⚠️ Email absent -> Postuler manuellement sur LinkedIn"

        fields = [
            {"name": "Entreprise", "value": self._truncate(offer.company, 250), "inline": True},
            {"name": "Localisation", "value": self._truncate(offer.location, 250), "inline": True},
            {"name": "Gratification", "value": remun_text, "inline": True},
            {"name": "Match Score", "value": f"{offer.score}%", "inline": True},
            {"name": "Action RH", "value": self._truncate(action_text, 500), "inline": True},
        ]

        if offer.matched_skills:
            stack_text = ", ".join(offer.matched_skills)
            fields.append({"name": "Stack Détectée", "value": self._truncate(stack_text, 1000), "inline": False})

        if offer.hr_linkedin_url:
            hr_label = f"👤 Recruteur RH : {offer.hr_name}" if offer.hr_name else "👤 Recruteur RH LinkedIn"
            fields.append({
                "name": self._truncate(hr_label, 250),
                "value": f"[Ouvrir le Profil du Recruteur]({offer.hr_linkedin_url}) *(Connectez-vous ou envoyez un message direct)*",
                "inline": False,
            })

        if offer.linkedin_url:
            fields.append({
                "name": "🔗 Postuler Manuellement sur LinkedIn",
                "value": f"[Accéder directement à l'offre LinkedIn]({offer.linkedin_url})",
                "inline": False,
            })
        elif offer.url:
            fields.append({
                "name": "🌐 Lien de l'offre",
                "value": f"[Ouvrir l'offre]({offer.url})",
                "inline": False,
            })

        embed = {
            "title": self._truncate(f"🎯 {offer.title}", 250),
            "url": offer.linkedin_url or offer.url,
            "description": "Nouvelle opportunité de Stage PFE détectée pour Anas Mouqine.",
            "color": color,
            "fields": fields,
            "footer": {"text": f"Source: {offer.source.upper()} | PFE Hunter Agent"},
        }

        try:
            res = requests.post(self.webhook_url, json={"embeds": [embed]}, timeout=10)
            if res.status_code in (200, 204):
                logger.info("Discord alert successfully sent for: %s", offer.title)
                return True
            else:
                logger.error("Discord API error (%s): %s", res.status_code, res.text)
                return False
        except Exception as e:
            logger.error("Failed to send Discord alert: %s", e)
            return False
