"""Scoring and filtering engine strictly tailored for Anas Mouqine's AI & Data PFE profile."""

import re
from typing import List, Optional
from src.config import config
from src.models.offer import JobOffer
from src.utils.logger import logger
from src.utils.date_parser import is_recent_offer, parse_offer_age_days


class OfferEvaluator:
    """Evaluates, filters, and scores scraped job offers strictly for AI & Data Engineering."""

    PFE_KEYWORDS = [
        r'\bpfe\b',
        r'projet de fin d[\'’]études',
        r'projet de fin d[\'’]etudes',
        r'stage pfe',
        r'stagiaire pfe',
        r'end-of-studies',
        r'graduation internship',
        r'stage de fin d[\'’]études',
        r'stage de fin d[\'’]etudes',
    ]

    # Explicit multi-word or unambiguous AI/Data Engineering terms (case-insensitive)
    AI_CORE_KEYWORDS = [
        r'intelligence artificielle',
        r'artificial intelligence',
        r'machine learning',
        r'\bml\b',
        r'deep learning',
        r'\bdl\b',
        r'data science',
        r'data scientist',
        r'data engineer',
        r'data engineering',
        r'ingénieur data',
        r'ingénieur données',
        r'ingénierie des données',
        r'llm',
        r'large language model',
        r'genai',
        r'ia générative',
        r'generative ai',
        r'\brag\b',
        r'retrieval-augmented generation',
        r'langchain',
        r'llamaindex',
        r'agentic',
        r'multi-agent',
        r'computer vision',
        r'vision par ordinateur',
        r'\bnlp\b',
        r'traitement du langage',
        r'neural network',
        r'réseaux de neurones',
        r'reseaux de neurones',
        r'pytorch',
        r'tensorflow',
        r'transformers',
        r'hugging face',
        r'scikit-learn',
        r'big data',
        r'apache airflow',
        r'apache kafka',
        r'lakehouse',
    ]

    # Acronyms that MUST be matched case-sensitively or in explicit tech contexts
    # to avoid false positives with French common words like "j'ai", "ai" (avoir), etc.
    AI_ACRONYM_PATTERN = re.compile(r'\b(?:AI|IA|A\.I\.|I\.A\.)\b')
    LOWER_IA_CONTEXT_PATTERN = re.compile(
        r'\b(?:stage|pfe|projet|ingénieur|ingenieur|engineer|solution|modele|modèle|filière|filiere)\s+(?:en\s+|de\s+)?ia\b',
        re.IGNORECASE,
    )

    NON_AI_DISQUALIFIERS = [
        r'\bsap\b',
        r'\bhybris\b',
        r'servicenow',
        r'salesforce',
        r'odoo',
        r'helpdesk',
        r'support informatique',
        r'support it',
        r'technicien support',
        r'câblage',
        r'cablage',
        r'maintenance informatique',
        r'comptable',
        r'comptabilité',
        r'commercial',
        r'téléconseiller',
        r'télévente',
        r'vendeur',
        r'community manager',
        r'graphiste',
        r'wordpress',
        r'magento',
        r'secrétariat',
        r'secretariat',
        r'assistant(?:e)? de direction',
        r'ressources humaines',
        r'recruteur',
        r'chargé(?:e)? de recrutement',
    ]

    DISQUALIFY_KEYWORDS = [
        r'\bcdi\b',
        r'\bcdd\b',
        r'senior\b',
        r'lead\b',
        r'directeur\b',
        r'5 ans d[\'’]expérience',
        r'7 ans d[\'’]expérience',
    ]

    REMUNERATION_KEYWORDS = [
        r'rémunér[ée]',
        r'remuner[ee]',
        r'gratification',
        r'indemnité',
        r'indemnite',
        r'bourse de stage',
        r'stage payé',
        r'stipend',
        r'\b\d{3,4}\s*(?:dh|mad|dirhams?)\b',
    ]

    def is_ai_offer(self, offer: JobOffer) -> bool:
        """
        Strictly verifies if the offer is focused on AI, ML, Data Science, or Data Engineering.
        Eliminates common French false-positives (e.g., 'j'ai' matching lowercase 'ai').
        """
        title_lower = offer.title.lower()
        raw_full_text = f"{offer.title} {offer.description}"
        full_text_lower = raw_full_text.lower()

        # 1. Reject if title explicitly states a non-AI enterprise role (e.g., SAP, comptable)
        for pattern in self.NON_AI_DISQUALIFIERS:
            if re.search(pattern, title_lower):
                return False

        # 2. Check for explicit AI acronyms in original casing (AI, IA, A.I., I.A.)
        has_ai_acronym = bool(self.AI_ACRONYM_PATTERN.search(raw_full_text))

        # 3. Check for lowercase context-bound 'ia' (e.g. 'stage en ia', 'projet ia')
        has_ia_context = bool(self.LOWER_IA_CONTEXT_PATTERN.search(full_text_lower))

        # 4. Check for unambiguous AI/Data core keywords
        matched_ai_keywords = [
            kw for kw in self.AI_CORE_KEYWORDS
            if re.search(kw, full_text_lower)
        ]

        total_ai_signals = len(matched_ai_keywords) + (1 if has_ai_acronym else 0) + (1 if has_ia_context else 0)

        if total_ai_signals == 0:
            return False

        # 5. If non-AI noise is present in description, require at least 2 distinct AI signals
        has_non_ai = any(re.search(pattern, full_text_lower) for pattern in self.NON_AI_DISQUALIFIERS)
        if has_non_ai and total_ai_signals < 2:
            return False

        return True

    def is_pfe_offer(self, offer: JobOffer) -> bool:
        """
        Determines if the offer is a genuine student PFE / end-of-studies internship.
        """
        text = f"{offer.title} {offer.description}".lower()

        # Reject permanent contracts and senior positions unless explicitly framed as PFE
        for pattern in self.DISQUALIFY_KEYWORDS:
            if re.search(pattern, text) and not any(re.search(pfe, text) for pfe in self.PFE_KEYWORDS):
                return False

        # Offer must be relevant to AI/Data
        if not self.is_ai_offer(offer):
            return False

        # Direct match on PFE keywords
        for pattern in self.PFE_KEYWORDS:
            if re.search(pattern, text):
                return True

        # Fallback: title contains "stage" or "intern" in an AI role
        if "stage" in text or "stagiaire" in text or "intern" in text:
            return True

        return False

    def is_target_location(self, offer: JobOffer) -> bool:
        """Checks if the offer is in Casablanca, Settat, or Remote."""
        loc = f"{offer.location} {offer.description}".lower()
        targets = [c.lower() for c in config.target_cities]
        return any(city in loc for city in targets) or "maroc" in loc

    def detect_remuneration(self, offer: JobOffer) -> bool:
        """Detects if the offer mentions remuneration, gratification, or stipend."""
        text = f"{offer.title} {offer.description}".lower()
        for pattern in self.REMUNERATION_KEYWORDS:
            if re.search(pattern, text):
                return True
        return False

    def is_recent_enough(self, offer: JobOffer, max_days: Optional[int] = None) -> bool:
        """Checks if the offer was published recently (within max_days)."""
        limit_days = max_days if max_days is not None else config.max_offer_age_days
        return is_recent_offer(offer.posted_date, max_days=limit_days)

    def evaluate(self, offer: JobOffer) -> JobOffer:
        """Enriches the offer with match score, remuneration flag, and matched skill tags."""
        raw_text = f"{offer.title} {offer.description}"
        text_lower = raw_text.lower()

        # 1. Remuneration check
        offer.is_remunerated = self.detect_remuneration(offer)

        # 2. Skill matching with strict casing for two-letter acronyms (AI, IA)
        matched_skills: List[str] = []
        for skill in config.candidate.core_skills:
            if skill in ("AI", "IA"):
                # Must be capitalized in the text to prevent French verb collisions
                if re.search(r'\b' + re.escape(skill) + r'\b', raw_text):
                    if skill not in matched_skills:
                        matched_skills.append(skill)
            else:
                if re.search(r'\b' + re.escape(skill.lower()) + r'\b', text_lower):
                    if skill not in matched_skills:
                        matched_skills.append(skill)

        offer.matched_skills = matched_skills

        # 3. Relevance & Domain Verification
        is_ai = self.is_ai_offer(offer)
        is_pfe = self.is_pfe_offer(offer)

        if not is_ai or not is_pfe:
            # Irrelevant or disqualified offer
            offer.score = 15
            return offer

        # 4. Score calculation for genuine AI PFE opportunities (50 to 100)
        base_score = 45
        skill_score = min(len(matched_skills) * 8, 40)
        remuneration_bonus = 10 if offer.is_remunerated else 0
        location_bonus = 5 if self.is_target_location(offer) else 0

        offer.score = min(base_score + skill_score + remuneration_bonus + location_bonus, 100)
        return offer
