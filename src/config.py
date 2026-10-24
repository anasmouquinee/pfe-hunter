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
    
    # Core technical keywords for scoring -- AI, Data & Full IT Software Engineering
    core_skills: list[str] = [
        "Intelligence Artificielle", "IA", "AI", "Machine Learning", "Deep Learning",
        "LLM", "RAG", "LangChain", "Multi-Agent", "Data Science", "Data Engineering",
        "Python", "PyTorch", "TensorFlow", "Computer Vision", "NLP",
        "Apache Airflow", "Kafka", "Lakehouse", "Docker", "FastAPI", "SQL", "Neo4j",
        "Java", "Spring Boot", "JavaScript", "TypeScript", "React", "Angular", "Node.js",
        "Full Stack", "Backend", "Frontend", "DevOps", "Cloud", "Kubernetes", "CI/CD",
        "PostgreSQL", "MongoDB", "C#", ".NET", "PHP", "Laravel", "Flutter"
    ]


class AgentConfig(BaseModel):
    """Global configuration for scraping, email dispatch, and alerting."""
    candidate: CandidateProfile = Field(default_factory=CandidateProfile)

    # Search parameters -- covering all IT, Software Engineering & Data/AI PFE domains
    target_cities: list[str] = ["Casablanca", "Casablanca-Settat", "Mohammedia", "Rabat", "Remote", "Télétravail"]
    target_roles: list[str] = [
        "Stage PFE Intelligence Artificielle", "Stage PFE IA", "Stage PFE Machine Learning",
        "Stage PFE Data Science", "Stage PFE Data Engineering",
        "Stage PFE Développeur Full Stack", "Stage PFE Développeur Web",
        "Stage PFE Développeur Backend", "Stage PFE Développeur Python",
        "Stage PFE Développeur Java", "Stage PFE Génie Logiciel",
        "Stage PFE Cloud & DevOps", "Stage PFE Informatique"
    ]
    search_keywords: list[str] = [
        "stage pfe data",
        "stage pfe ia",
        "stage pfe intelligence artificielle",
        "stage pfe machine learning",
        "stage pfe data science",
        "stage pfe data engineer",
        "stage pfe developpeur",
        "stage pfe informatique",
        "stage pfe web",
        "stage pfe fullstack",
        "stage pfe backend",
        "stage pfe python",
        "stage pfe java",
        "stage pfe react",
        "stage pfe devops",
        "stage pfe cloud",
        "stagiaire data",
        "stagiaire developpeur",
        "stagiaire informatique",
    ]
    remuneration_keywords: list[str] = [
        "rémunéré", "remunere", "gratification", "indemnité",
        "indemnite", "bourse", "payé", "paye", "stipend"
    ]

    # Email & Safety Controls
    dry_run: bool = Field(default_factory=lambda: os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes"))
    gmail_user: str = Field(default_factory=lambda: os.getenv("GMAIL_USER", "anasmouqine@gmail.com"))
    gmail_app_password: str = Field(default_factory=lambda: os.getenv("GMAIL_APP_PASSWORD", ""))
    resend_api_key: str = Field(default_factory=lambda: os.getenv("RESEND_API_KEY", ""))
    resend_from_email: str = Field(default_factory=lambda: os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev"))
    linkedin_li_at: str = Field(default_factory=lambda: os.getenv("LINKEDIN_LI_AT", ""))
    auto_easy_apply: bool = Field(
        default_factory=lambda: os.getenv(
            "AUTO_EASY_APPLY",
            "true" if os.getenv("LINKEDIN_LI_AT") else "false",
        ).lower() in ("true", "1", "yes")
    )
    
    # Platform Accounts & Multi-Site Auto-Apply
    rekrute_email: str = Field(default_factory=lambda: os.getenv("REKRUTE_EMAIL", os.getenv("GMAIL_USER", "anasmouqine@gmail.com")))
    rekrute_password: str = Field(default_factory=lambda: os.getenv("REKRUTE_PASSWORD", ""))
    auto_platform_apply: bool = Field(
        default_factory=lambda: os.getenv(
            "AUTO_PLATFORM_APPLY",
            "true" if (os.getenv("LINKEDIN_LI_AT") or os.getenv("REKRUTE_PASSWORD")) else "false",
        ).lower() in ("true", "1", "yes")
    )

    max_emails_per_run: int = Field(default_factory=lambda: int(os.getenv("MAX_EMAILS_PER_RUN", "20")))
    max_offer_age_days: int = Field(default_factory=lambda: int(os.getenv("MAX_OFFER_AGE_DAYS", "14")))

    # Notification Webhooks
    telegram_bot_token: str = Field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", ""))
    telegram_chat_id: str = Field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    discord_webhook_url: str = Field(default_factory=lambda: os.getenv("DISCORD_WEBHOOK_URL", ""))

    # AI / LLM Evaluation (Optional)
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))

    # Data Persistence & Outputs
    base_dir: Path = BASE_DIR
    letters_dir: Path = BASE_DIR / "letters"
    data_dir: Path = BASE_DIR / "data"
    state_file: Path = BASE_DIR / "data" / "applied_offers.json"

    @property
    def BASE_DIR(self) -> Path:
        return self.base_dir


# Singleton instance
config = AgentConfig()

