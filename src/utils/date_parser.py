"""Robust multi-format date parsing and offer age calculation for Moroccan job platforms."""

import re
from datetime import datetime, timezone
from typing import Optional

FRENCH_MONTHS = {
    'janv': 1, 'janvier': 1,
    'fevr': 2, 'fevrier': 2, 'févr': 2, 'février': 2,
    'mars': 3,
    'avril': 4, 'avr': 4,
    'mai': 5,
    'juin': 6,
    'juil': 7, 'juillet': 7,
    'aout': 8, 'août': 8,
    'sept': 9, 'septembre': 9,
    'oct': 10, 'octobre': 10,
    'nov': 11, 'novembre': 11,
    'dec': 12, 'decembre': 12, 'décr': 12, 'décembre': 12
}


def parse_offer_age_days(date_str: Optional[str]) -> int:
    """
    Parses any raw publication date string from Moroccan and international job boards
    (ISO format, relative days/weeks/months in French/English, DD/MM/YYYY) into an integer
    number of days elapsed since publication.
    
    Returns:
        int: Number of days since publication (0 for today, 1 for yesterday, etc.).
             Returns 999 if the date string is empty or unrecognized.
    """
    if not date_str:
        return 999

    s = date_str.strip().lower()
    now = datetime.now()

    # 1. ISO format (e.g. 2026-10-22T15:37:18+00:00 or 2026-10-22)
    iso_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', s)
    if iso_match:
        try:
            y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
            dt = datetime(y, m, d)
            return max(0, (now - dt).days)
        except ValueError:
            pass

    # 2. DD/MM/YYYY, DD-MM-YYYY, or DD.MM.YYYY
    dmy_match = re.search(r'(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})', s)
    if dmy_match:
        try:
            d, m, y = int(dmy_match.group(1)), int(dmy_match.group(2)), int(dmy_match.group(3))
            dt = datetime(y, m, d)
            return max(0, (now - dt).days)
        except ValueError:
            pass

    # 3. Relative hours / minutes / today
    if any(w in s for w in ['aujourd', 'today', 'heure', 'hour', 'minute', 'instant', 'min']):
        return 0

    # 4. Yesterday
    if any(w in s for w in ['hier', 'yesterday']):
        return 1

    # 5. Relative days (e.g. 'il y a 3 jours', '3 days ago')
    days_match = re.search(r'(\d+)\s*(?:jour|day)', s)
    if days_match:
        return int(days_match.group(1))

    # 6. Relative weeks (e.g. 'il y a 2 semaines', '1 week ago')
    weeks_match = re.search(r'(\d+)\s*(?:semaine|week)', s)
    if weeks_match:
        return int(weeks_match.group(1)) * 7

    # 7. Relative months (e.g. 'il y a 1 mois', '2 months ago')
    months_match = re.search(r'(\d+)\s*(?:mois|month)', s)
    if months_match:
        return int(months_match.group(1)) * 30

    # 8. Day + Month name (e.g. '21 Octobre 18:00', '15 sept')
    for mname, mnum in FRENCH_MONTHS.items():
        if mname in s:
            day_match = re.search(r'(\d{1,2})\s*' + mname, s)
            if day_match:
                d = int(day_match.group(1))
                y = now.year
                try:
                    dt = datetime(y, mnum, d)
                    if dt > now:
                        dt = datetime(y - 1, mnum, d)
                    return max(0, (now - dt).days)
                except ValueError:
                    pass

    return 999


def is_recent_offer(date_str: Optional[str], max_days: int = 14) -> bool:
    """
    Returns True if the offer was published within max_days.
    If date_str is unknown/absent, returns True so offers without visible date are not blindly dropped.
    """
    if not date_str:
        return True
    age = parse_offer_age_days(date_str)
    if age == 999:
        return True
    return age <= max_days
