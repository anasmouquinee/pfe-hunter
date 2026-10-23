"""Directory of verified recruitment contacts for Moroccan tech and multinational employers."""

import re
from typing import Optional, Tuple
from src.utils.logger import logger

# Moroccan Tech, Banking, and Engineering Corporate Inboxes
MOROCCO_TECH_DIRECTORY = [
    (r'\bcapgemini\b', "recrutementmaroc.ceg@capgemini.com", "Capgemini Morocco"),
    (r'\bsofrecom\b|\borange\b', "recrutement.maroc@sofrecom.com", "Sofrecom / Orange Maroc"),
    (r'\balten\b', "recrutement.maroc@alten.com", "Alten Maroc"),
    (r'\bsqli\b', "recrutement-maroc@sqli.com", "SQLI Maroc"),
    (r'\bcgi\b', "carrieres.maroc@cgi.com", "CGI Maroc"),
    (r'\batos\b|\beviden\b', "maroc.recrutement@atos.net", "Atos / Eviden"),
    (r'\bdxc\b', "dxc-recrutement-maroc@dxc.com", "DXC Technology Maroc"),
    (r'\bleyton\b', "recrutement-maroc@leyton.com", "Leyton Maroc"),
    (r'\bsopra\s*steria\b', "recrutement.maroc@soprasteria.com", "Sopra Steria Maroc"),
    (r'\bdell\b', "morocco.careers@dell.com", "Dell Technologies Casablanca"),
    (r'\bintelcia\b', "recrutement.it@intelcia.com", "Intelcia IT Solutions"),
    (r'\binwi\b|\bwana\b', "recrutement@inwi.ma", "inwi"),
    (r'\bmaroc\s*telecom\b|\biam\b', "recrutement@iam.ma", "Maroc Telecom"),
    (r'\bthales\b', "recrutement.maroc@thalesgroup.com", "Thales Maroc"),
    (r'\bcoface\b', "recrutement-maroc@coface.com", "Coface"),
    (r'\blabel\s*[\'’]?vie\b|\bcarrefour\b', "recrutement@labelvie.ma", "Label'Vie Carrefour"),
    (r'\battijari\b|\battijariwafa\b', "recrutement@attijariwafa.com", "Attijariwafa bank"),
    (r'\bbank\s*of\s*africa\b|\bbmce\b', "recrutement@bankofafrica.ma", "Bank of Africa"),
    (r'\bbanque\s*populaire\b|\bbcp\b', "recrutement@cpm.ma", "Banque Populaire"),
    (r'\bcih\b', "recrutement@cihbank.ma", "CIH Bank"),
    (r'\bcr[ée]dit\s*du\s*maroc\b|\bcdm\b', "recrutement@cdm.ma", "Crédit du Maroc"),
    (r'\bsoci[ée]t[ée]\s*g[ée]n[ée]rale\b|\bsgabs\b', "recrutement@socgen.com", "Société Générale Maroc"),
    (r'\bocp\b', "recrutement@ocpgroup.ma", "OCP Group"),
    (r'\bmasen\b', "recrutement@masen.ma", "MASEN"),
    (r'\boncf\b', "recrutement@oncf.ma", "ONCF"),
    (r'\bmanpower\b', "recrutement@manpower-maroc.com", "Manpower Maroc"),
    (r'\bakkodis\b|\bakka\b', "recrutement.maroc@akkodis.com", "Akkodis Maroc"),
    (r'\badecco\b', "recrutement@adecco.ma", "Adecco Maroc"),
    (r'\bmichael\s*page\b', "contact.maroc@michaelpage.com", "Michael Page Maroc"),
    (r'\bum6p\b', "recrutement@um6p.ma", "UM6P"),
    (r'\bmascir\b', "recrutement@mascir.com", "MAScIR"),
    (r'\bcnss\b', "recrutement@cnss.ma", "CNSS"),
]


def resolve_company_email(company_name: str, description: str = "") -> Tuple[Optional[str], Optional[str]]:
    """
    Attempts to match a company name or description against verified recruitment inboxes.
    Returns (verified_email, standardized_company_name) or (None, None).
    """
    if not company_name:
        return None, None

    search_target = f"{company_name} {description}".lower()

    for pattern, email, standard_name in MOROCCO_TECH_DIRECTORY:
        if re.search(pattern, search_target, re.IGNORECASE):
            logger.info("Resolved recruitment contact for '%s' -> %s (%s)", company_name, email, standard_name)
            return email, standard_name

    return None, None
