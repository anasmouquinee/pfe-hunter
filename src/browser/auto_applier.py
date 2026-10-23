"""Unified multi-platform automated job applicant for PFE-Hunter."""

from typing import Any, Dict
from src.config import config
from src.models.offer import JobOffer
from src.utils.logger import logger
from src.browser.linkedin_applier import LinkedInApplier
from src.browser.rekrute_applier import ReKruteApplier
from src.browser.marocannonces_applier import MarocAnnoncesApplier
from src.browser.generic_form_applier import GenericWebFormApplier


class AutoApplierRouter:
    """
    Intelligent router that selects and delegates automated job applications
    across multiple Moroccan and international employment platforms:
    - LinkedIn Easy Apply
    - ReKrute
    - MarocAnnonces
    - Generic Web & Corporate Portals (Emploi.ma, Dreamjob, Talent, etc.)
    """

    def __init__(self):
        self.linkedin = LinkedInApplier()
        self.rekrute = ReKruteApplier()
        self.marocannonces = MarocAnnoncesApplier()
        self.generic = GenericWebFormApplier()

    def can_apply(self, offer: JobOffer) -> bool:
        """Determines if the offer can be processed by any platform applier."""
        target_url = (offer.linkedin_url or offer.url or "").lower()
        source = (offer.source or "").lower()

        if "linkedin.com" in target_url and self.linkedin.is_configured():
            return True
        elif ("rekrute.com" in target_url or source == "rekrute") and self.rekrute.is_configured():
            return True
        elif ("marocannonces.com" in target_url or source == "marocannonces") and self.marocannonces.is_configured():
            return True
        elif target_url and self.generic.is_configured():
            return True

        return False

    def apply(self, offer: JobOffer) -> Dict[str, Any]:
        """
        Dispatches application to the appropriate platform handler.
        """
        target_url = (offer.linkedin_url or offer.url or "").lower()
        source = (offer.source or "").lower()

        # 1. LinkedIn
        if "linkedin.com" in target_url:
            if self.linkedin.is_configured():
                return self.linkedin.apply(offer)
            else:
                logger.debug("LinkedIn cookie not configured; skipping LinkedIn applier.")
                return {"status": "skipped", "applied": False, "platform": "linkedin", "reason": "cookie_missing"}

        # 2. ReKrute
        if "rekrute.com" in target_url or source == "rekrute":
            if self.rekrute.is_configured():
                return self.rekrute.apply(offer)

        # 3. MarocAnnonces
        if "marocannonces.com" in target_url or source == "marocannonces":
            if self.marocannonces.is_configured():
                return self.marocannonces.apply(offer)

        # 4. Generic Web Application Portals (Emploi.ma, Dreamjob, Talent, direct careers)
        if target_url and self.generic.is_configured():
            return self.generic.apply(offer)

        return {"status": "unsupported", "applied": False, "platform": source or "unknown"}
