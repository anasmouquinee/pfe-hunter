"""Configuration module for PFE Auto-Hunter Agent."""

import os
from pathlib import Path
from pydantic import BaseModel, Field
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent


class CandidateProfile(BaseModel):
    """Pre-configured candidate profile for Anas Mouqine."""
    full_name: str = "Anas Mouqine"
    email: str = "anasmouqine@gmail.com"
    phone: str = "+212 672-104126"
    location: str = "Casablanca, Maroc"
    linkedin_url: str = "https://www.linkedin.com/in/anas-mouqine-329207304/"
    github_url: str = "https://github.com/anasmouquinee"
    portfolio_url: str = "https://anasmouquinee.github.io/port/"
    school: str = "École Marocaine des Sciences de l'Ingénieur (EMSI Casablanca)"
    education_level: str = "5ème année -- Cycle Ingénieur d'État"
    specialization: str = "Intelligence Artificielle (IA) & Data Engineering"
    internship_target: str = "Stage PFE (Projet de Fin d'Études) de 4 à 6 mois (2026)"
    cv_path: Path = BASE_DIR / "cv_ats_pfe.pdf"
    
    # Core technical keywords for scoring -- strictly focused on AI & Data
    core_skills: list[str] = [
        "Intelligence Artificielle", "IA", "AI", "Machine Learning", "Deep Learning",
        "LLM", "RAG", "LangChain", "Multi-Agent", "Data Science", "Data Engineering",
        "Python", "PyTorch", "TensorFlow", "Computer Vision", "NLP",
        "Apache Airflow", "Kafka", "Lakehouse", "Docker", "FastAPI", "SQL", "Neo4j"
    ]


class AgentConfig(BaseModel):
    """Global configuration for scraping, email dispatch, and alerting."""
    candidate: CandidateProfile = Field(default_factory=CandidateProfile)

    # Search parameters -- specialized in AI / Machine Learning / Data Engineering PFE
    target_cities: list[str] = ["Casablanca", "Casablanca-Settat", "Mohammedia", "Remote", "Télétravail"]
    target_roles: list[str] = [
        "Stage PFE Intelligence Artificielle", "Stage PFE IA", "Stage PFE Machine Learning",
        "Stage PFE Deep Learning", "Stage PFE Data Science", "Stage PFE Data Engineering",
        "Stage PFE LLM", "Stage PFE Generative AI", "Stage PFE NLP", "Stage PFE Computer Vision"
    ]
    search_keywords: list[str] = [
        "stage pfe data",
        "stage pfe ia",
        "stage pfe intelligence artificielle",
        "stage pfe machine learning",
        "stage pfe data science",
        "stage pfe data engineer",
        "stage pfe deep learning",
        "stage pfe python",
        "stagiaire data",
    ]
    remuneration_keywords: list[str] = [
        "rémunéré", "remunere", "gratification", "indemnité",
        "indemnite", "bourse", "payé", "paye", "stipend"
    ]

    # Email & Safety Controls
    dry_run: bool = Field(default_factory=lambda: os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes"))
    gmail_user: str = Field(default_factory=lambda: os.getenv("GMAIL_USER", "anasmouqine@gmail.com"))
    gmail_app_password: str = Field(default_factory=lambda: os.getenv("GMAIL_APP_PASSWORD", ""))
    max_emails_per_run: int = Field(default_factory=lambda: int(os.getenv("MAX_EMAILS_PER_RUN", "5")))
    max_offer_age_days: int = Field(default_factory=lambda: int(os.getenv("MAX_OFFER_AGE_DAYS", "14")))

    # Notification Webhooks
    telegram_bot_token: str = Field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = Field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    discord_webhook_url: str = Field(default_factory=lambda: os.getenv("DISCORD_WEBHOOK_URL", ""))

    # AI / LLM Evaluation (Optional)
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))

    # Data Persistence
    data_dir: Path = BASE_DIR / "data"
    state_file: Path = BASE_DIR / "data" / "applied_offers.json"


# Singleton instance
config = AgentConfig()
