"""Unit tests for OfferEvaluator with strict AI relevance verification."""

from src.models.offer import JobOffer
from src.matcher.evaluator import OfferEvaluator


def test_evaluator_pfe_and_remunerated():
    evaluator = OfferEvaluator()
    offer = JobOffer(
        title="Stage PFE -- Data Engineer & IA",
        company="Smart Analytics Casablanca",
        location="Casablanca, Maroc",
        url="https://example.com/pfe-data",
        description="Recherche stagiaire PFE pour projet IA et Big Data (Python, Apache Airflow, Kafka). Stage rémunéré avec gratification.",
        source="rekrute"
    )

    evaluated = evaluator.evaluate(offer)
    assert evaluator.is_ai_offer(evaluated) is True
    assert evaluator.is_pfe_offer(evaluated) is True
    assert evaluated.is_remunerated is True
    assert "Python" in evaluated.matched_skills
    assert "Apache Airflow" in evaluated.matched_skills
    assert evaluated.score >= 80


def test_evaluator_disqualify_cdi_senior():
    evaluator = OfferEvaluator()
    offer = JobOffer(
        title="Ingénieur Senior CDI (5 ans d'expérience)",
        company="OldCorp",
        location="Casablanca",
        url="https://example.com/senior-cdi",
        description="Poste CDI pour ingénieur confirmé avec au moins 5 ans d'expérience.",
        source="emploima"
    )

    assert evaluator.is_pfe_offer(offer) is False
    evaluated = evaluator.evaluate(offer)
    assert evaluated.score < 50


def test_evaluator_rejects_non_ai_offers():
    evaluator = OfferEvaluator()

    # Case 1: SAP Hybris
    offer_sap = JobOffer(
        title="Stagiaire PFE en SAP HYBRIS",
        company="Inetum",
        location="Casablanca",
        url="https://example.com/pfe-sap",
        description="Stage PFE pour intégration ERP et modules SAP Hybris e-commerce.",
        source="linkedin_guest"
    )
    assert evaluator.is_ai_offer(offer_sap) is False
    assert evaluator.is_pfe_offer(offer_sap) is False
    assert evaluator.evaluate(offer_sap).score < 50

    # Case 2: IT Support / Helpdesk
    offer_support = JobOffer(
        title="Stagiaire Support Technique & Helpdesk IT",
        company="TelecomCorp",
        location="Casablanca",
        url="https://example.com/stage-support",
        description="Support utilisateurs niveau 1, gestion de parc informatique et ticketing.",
        source="emploima"
    )
    assert evaluator.is_ai_offer(offer_support) is False
    assert evaluator.is_pfe_offer(offer_support) is False

    # Case 3: ServiceNow
    offer_servicenow = JobOffer(
        title="Stagiaire PFE – Reporting IT ServiceNow & Support",
        company="Inetum",
        location="Casablanca",
        url="https://example.com/pfe-servicenow",
        description="Conception de dashboards ServiceNow pour le suivi d'incidents IT.",
        source="linkedin_guest"
    )
    assert evaluator.is_ai_offer(offer_servicenow) is False


def test_evaluator_accepts_core_ai_topics():
    evaluator = OfferEvaluator()

    # Case 1: Generative AI & LLM / RAG
    offer_genai = JobOffer(
        title="Stage PFE: Agentic AI & LLMs",
        company="AI Innovation Lab Casablanca",
        location="Casablanca",
        url="https://example.com/pfe-llm",
        description="Développement d'agents intelligents basés sur LangChain, RAG et modèles d'IA générative.",
        source="linkedin_guest"
    )
    assert evaluator.is_ai_offer(offer_genai) is True
    assert evaluator.is_pfe_offer(offer_genai) is True
    assert evaluator.evaluate(offer_genai).score >= 70

    # Case 2: Computer Vision / Deep Learning
    offer_cv = JobOffer(
        title="Stage PFE - Computer Vision & Deep Learning",
        company="VisionTech Maroc",
        location="Casablanca",
        url="https://example.com/pfe-cv",
        description="Entraînement de modèles de détection d'objets avec PyTorch et OpenCV.",
        source="rekrute"
    )
    assert evaluator.is_ai_offer(offer_cv) is True
    assert evaluator.is_pfe_offer(offer_cv) is True


def test_evaluator_rejects_french_jai_false_positive():
    """Ensures French expressions like 'j'ai' do not falsely match the AI keyword."""
    evaluator = OfferEvaluator()
    offer = JobOffer(
        title="Stage PFE en Administration & Secrétariat",
        company="Société Casablancaise",
        location="Casablanca",
        url="https://example.com/pfe-admin",
        description="Nous cherchons un stagiaire. J'ai le plaisir de partager cette opportunité de stage.",
        source="rekrute"
    )

    assert evaluator.is_ai_offer(offer) is False
    assert evaluator.is_pfe_offer(offer) is False
    assert evaluator.evaluate(offer).score == 15
    assert "AI" not in offer.matched_skills
    assert "IA" not in offer.matched_skills


def test_evaluator_matches_cased_ai_acronym_and_ia_context():
    """Verifies uppercase AI/IA and context-bound 'stage en ia' match correctly."""
    evaluator = OfferEvaluator()

    # Uppercase AI in title
    offer_ai = JobOffer(
        title="Stage PFE - Python & AI Engineer",
        company="Lab Casablanca",
        url="https://example.com/ai",
        source="rekrute",
        description="Stage PFE pour ingénieur développeur."
    )
    assert evaluator.is_ai_offer(offer_ai) is True

    # Lowercase context-bound 'stage en ia'
    offer_ia_context = JobOffer(
        title="Stage PFE Ingénieur",
        company="Lab Casablanca",
        url="https://example.com/ia",
        source="rekrute",
        description="Projet de fin d'études : stage en ia pour la modélisation prédictive."
    )
    assert evaluator.is_ai_offer(offer_ia_context) is True


def test_evaluator_accepts_broad_tech_offers():
    """Verifies that all IT/Dev/Cloud domains are accepted under the broadened tech scope."""
    evaluator = OfferEvaluator()

    # 1. Full Stack Web Developer (React / Node / TypeScript)
    offer_web = JobOffer(
        title="Stage PFE Développeur Full Stack (React / Node.js)",
        company="TechStudio Casablanca",
        location="Casablanca",
        url="https://example.com/pfe-web",
        description="Stage PFE pour le développement d'une application web moderne avec React, TypeScript, Docker et PostgreSQL.",
        source="rekrute"
    )
    assert evaluator.is_tech_offer(offer_web) is True
    assert evaluator.is_pfe_offer(offer_web) is True
    evaluated_web = evaluator.evaluate(offer_web)
    assert evaluated_web.score >= 50
    assert "React" in evaluated_web.matched_skills or "TypeScript" in evaluated_web.matched_skills

    # 2. DevOps / Cloud Engineer
    offer_devops = JobOffer(
        title="Stage PFE Ingénieur DevOps & Cloud AWS",
        company="CloudOps Rabat",
        location="Rabat",
        url="https://example.com/pfe-devops",
        description="Mise en place de pipelines CI/CD, conteneurisation Docker, orchestration Kubernetes et infrastructure Terraform sur AWS.",
        source="rekrute"
    )
    assert evaluator.is_tech_offer(offer_devops) is True
    assert evaluator.is_pfe_offer(offer_devops) is True
    evaluated_devops = evaluator.evaluate(offer_devops)
    assert evaluated_devops.score >= 50

    # 3. Non-tech role should be rejected
    offer_compta = JobOffer(
        title="Stage PFE Comptabilité & Gestion Financière",
        company="FinanceCorp",
        location="Casablanca",
        url="https://example.com/stage-compta",
        description="Tenue des journaux comptables, rapprochements bancaires et déclarations fiscales.",
        source="emploima"
    )
    assert evaluator.is_tech_offer(offer_compta) is False
    assert evaluator.is_pfe_offer(offer_compta) is False
    assert evaluator.evaluate(offer_compta).score < 50


def test_company_directory_auto_email_resolution():
    """Verifies that known Moroccan tech employers have their recruitment email auto-resolved."""
    # Capgemini without email
    offer_cap = JobOffer(
        title="Stage PFE Ingénieur Logiciel",
        company="Capgemini Engineering Maroc",
        location="Casablanca",
        url="https://example.com/capgemini",
        source="rekrute"
    )
    assert offer_cap.contact_email == "recrutementmaroc.ceg@capgemini.com"

    # Alten without email
    offer_alten = JobOffer(
        title="Stage PFE Développeur Java",
        company="Alten Delivery Center Maroc",
        location="Fès",
        url="https://example.com/alten",
        source="rekrute"
    )
    assert offer_alten.contact_email == "recrutement.maroc@alten.com"

    # Existing explicit email should not be overwritten
    offer_explicit = JobOffer(
        title="Stage PFE Python",
        company="Capgemini",
        location="Casablanca",
        url="https://example.com/cap-custom",
        contact_email="custom.recruiter@capgemini.com",
        source="rekrute"
    )
    assert offer_explicit.contact_email == "custom.recruiter@capgemini.com"

