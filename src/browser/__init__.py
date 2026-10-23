"""Browser automation package for headless Cloud and local applications."""

from src.browser.linkedin_applier import LinkedInApplier
from src.browser.rekrute_applier import ReKruteApplier
from src.browser.marocannonces_applier import MarocAnnoncesApplier
from src.browser.generic_form_applier import GenericWebFormApplier
from src.browser.auto_applier import AutoApplierRouter

__all__ = [
    "LinkedInApplier",
    "ReKruteApplier",
    "MarocAnnoncesApplier",
    "GenericWebFormApplier",
    "AutoApplierRouter",
]
