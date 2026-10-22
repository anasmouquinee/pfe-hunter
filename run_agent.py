"""Main orchestrator for PFE Auto-Hunter & Application Agent."""

import argparse
import sys
from typing import List, Optional

# Ensure UTF-8 output encoding across Windows shells and GitHub Actions runners
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from src.config import config
from src.models.offer import JobOffer
from src.scrapers.rekrute_scraper import ReKruteScraper
from src.scrapers.emploima_scraper import EmploiMaScraper
from src.scrapers.linkedin_guest_scraper import LinkedInGuestScraper
from src.scrapers.dreamjob_scraper import DreamJobScraper
from src.scrapers.marocannonces_scraper import MarocAnnoncesScraper
from src.scrapers.talent_scraper import TalentScraper
from src.scrapers.joblia_scraper import JobliaScraper
from src.matcher.evaluator import OfferEvaluator
from src.storage.state_manager import StateManager
from src.mailer.email_sender import EmailSender
from src.notifier.telegram_notifier import TelegramNotifier
from src.notifier.discord_notifier import DiscordNotifier
from src.utils.logger import logger
from src.utils.date_parser import parse_offer_age_days


def test_notifications() -> int:
    """Sends a verification card to configured notification channels (Telegram & Discord)."""
    print("\n🔔 Test des canaux de notification...")
    dummy_offer = JobOffer(
        title="Stage PFE -- Test de Validation Agent",
        company="EMSI Innovation Lab",
        location="Casablanca, Maroc",
        url="https://github.com/anasmouquinee",
        description="Vérification de la connectivité Telegram Bot et Discord Webhook pour Anas Mouqine.",
        source="system_test",
        contact_email="test.rh@example.com",
        linkedin_url="https://www.linkedin.com/in/anas-mouqine-329207304/",
        hr_name="Test Recruteur",
        hr_linkedin_url="https://www.linkedin.com/in/anas-mouqine-329207304/",
        is_remunerated=True,
        score=99,
        matched_skills=["Intelligence Artificielle", "Python", "RAG", "Lakehouse"],
    )

    telegram = TelegramNotifier()
    discord = DiscordNotifier()

    t_ok = telegram.send_alert(dummy_offer, email_sent=False)
    d_ok = discord.send_alert(dummy_offer, email_sent=False)

    print(f"   - Telegram : {'✅ Succès' if t_ok else '❌ Échec ou non configuré'}")
    print(f"   - Discord  : {'✅ Succès' if d_ok else '❌ Échec ou non configuré'}\n")
    return 0 if (t_ok or d_ok) else 1


def display_stats() -> int:
    """Displays statistics of tracked applications and opportunities."""
    state_manager = StateManager()
    stats = state_manager.get_statistics()

    print("\n" + "=" * 60)
    print("📊 STATISTIQUES PFE HUNTER AGENT")
    print("=" * 60)
    print(f"Total offres enregistrées  : {stats['total_offers']}")
    print(f"Candidatures envoyées (Live): {stats['applied']}")
    print(f"Simulations (Dry-Run)       : {stats['simulated']}")
    print(f"Alertes notifiées           : {stats['notified']}")
    print(f"Offres rémunérées           : {stats['remunerated']}")
    print("\nRépartition par source :")
    for src, count in stats["sources"].items():
        print(f"   - {src.upper():<16} : {count} offre(s)")
    print(f"Dernière mise à jour        : {stats['last_updated'] or 'Aucune'}")
    print("=" * 60 + "\n")
    return 0


def run_agent(
    dry_run: bool = True,
    custom_keywords: Optional[List[str]] = None,
    location: str = "Casablanca",
    limit: Optional[int] = None,
) -> int:
    """Executes full scraping, evaluation, dispatching, and alerting pipeline."""
    config.dry_run = dry_run
    print("=" * 70)
    print(f"🚀 PFE HUNTER AGENT STARTING FOR {config.candidate.full_name.upper()}")
    print(f"📍 Cible : {config.candidate.specialization} ({config.candidate.school})")
    print(f"🛡 Mode Sécurité (DRY_RUN) : {'ACTIVÉ (Simulation - Aucun email envoyé)' if config.dry_run else 'DÉSACTIVÉ (Envois Réels)'}")
    print("=" * 70)

    # 1. Initialize Components
    state_manager = StateManager()
    evaluator = OfferEvaluator()
    mailer = EmailSender()
    telegram = TelegramNotifier()
    discord = DiscordNotifier()

    print("📡 Statut des Canaux & Secrets :")
    print(f"   - Telegram   : {'✅ Configuré (Actif)' if telegram.is_configured() else '⚠️ Non configuré (TELEGRAM_BOT_TOKEN / CHAT_ID manquant)'}")
    print(f"   - Discord    : {'✅ Configuré (Actif)' if discord.is_configured() else '⚠️ Non configuré (DISCORD_WEBHOOK_URL manquant)'}")
    print(f"   - Gmail SMTP : {'✅ Mot de passe détecté' if bool(config.gmail_app_password) else '⚠️ GMAIL_APP_PASSWORD non renseigné'}")
    print("-" * 70)

    scrapers = [
        DreamJobScraper(),
        JobliaScraper(),
        LinkedInGuestScraper(),
        ReKruteScraper(),
        TalentScraper(),
        MarocAnnoncesScraper(),
        EmploiMaScraper(),
    ]

    all_raw_offers: List[JobOffer] = []

    # 2. Scrape Job Boards for AI & Data PFE Opportunities
    keywords = custom_keywords or config.search_keywords
    seen_scraped_urls = set()

    for scraper in scrapers:
        print(f"\n🔍 Scraping source : {scraper.name.upper()}...")
        for kw in keywords:
            try:
                offers = scraper.scrape(keyword=kw, location=location)
                for off in offers:
                    if off.url not in seen_scraped_urls:
                        seen_scraped_urls.add(off.url)
                        all_raw_offers.append(off)
            except Exception as e:
                logger.warning("Erreur scraper %s sur '%s': %s", scraper.name, kw, e)
        print(f"   -> {len(all_raw_offers)} offres cumulées uniques.")

    # 3. Evaluate & Filter strictly for AI PFE & Recency
    print(f"\n🧠 Évaluation, filtrage IA et contrôle de fraîcheur de {len(all_raw_offers)} offres...")
    qualified_offers: List[JobOffer] = []

    for offer in all_raw_offers:
        evaluated = evaluator.evaluate(offer)
        # Strictly require genuine AI domain, student PFE internship, and recent publication
        if (evaluator.is_pfe_offer(evaluated) and 
            evaluator.is_ai_offer(evaluated) and 
            evaluator.is_recent_enough(evaluated) and 
            evaluated.score >= 50):
            qualified_offers.append(evaluated)

    # Sort: 1) Freshness (newest first), 2) Remuneration, 3) Match score
    qualified_offers.sort(
        key=lambda o: (
            -parse_offer_age_days(o.posted_date),
            o.is_remunerated or False,
            o.score
        ),
        reverse=True
    )
    if limit:
        qualified_offers = qualified_offers[:limit]
    print(f"   -> {len(qualified_offers)} offres PFE IA qualifiées retenues.")

    # 4. Process each qualified offer
    new_offers_count = 0
    emails_sent_count = 0

    for offer in qualified_offers:
        already_applied = state_manager.is_already_applied(offer.id)
        already_notified = state_manager.is_already_notified(offer.id)

        # In LIVE mode: skip if already applied, or if already notified and no email can be sent
        if not config.dry_run:
            if already_applied:
                continue
            if already_notified and not offer.contact_email:
                continue
        else:
            # In DRY-RUN mode: skip if already recorded
            if state_manager.is_already_seen(offer.id):
                continue

        new_offers_count += 1
        print(f"\n✨ NOUVELLE OPPORTUNITÉ : {offer.title} @ {offer.company} (Score: {offer.score}%)")
        print(f"   📍 Lieu : {offer.location} | Rémunéré : {'OUI' if offer.is_remunerated else 'Non spécifié'}")

        # A. Automated Email if Recruiter / HR email is found
        email_sent = False
        if offer.contact_email:
            print(f"   ✉️ Contact RH identifié : {offer.contact_email}")
            if not config.dry_run:
                if emails_sent_count < config.max_emails_per_run:
                    email_sent = mailer.send_application(offer)
                    if email_sent:
                        emails_sent_count += 1
                else:
                    print(f"   ⚠️ Limite d'envois atteinte pour cette session ({config.max_emails_per_run})")
            else:
                # In dry run: log simulation without actually sending
                mailer.send_application(offer)
                email_sent = False
        else:
            print("   ℹ️ Aucun email RH public dans la description -> Postulation manuelle requise.")

        # B. LinkedIn Links for Anas to apply/connect manually
        if offer.hr_linkedin_url:
            print(f"   👤 Recruteur RH LinkedIn : {offer.hr_linkedin_url}")
        if offer.linkedin_url:
            print(f"   🔗 Lien LinkedIn pour postuler manuellement : {offer.linkedin_url}")

        # C. Webhook Dispatch (Telegram / Discord) - notify if not already notified
        if not already_notified or email_sent:
            telegram.send_alert(offer, email_sent=email_sent)
            discord.send_alert(offer, email_sent=email_sent)

        # D. Save State - explicitly marking simulated vs real application
        state_manager.record_offer(
            offer,
            applied=email_sent,
            notified=True,
            simulated=config.dry_run,
        )

    # 5. Summary
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DE L'EXÉCUTION :")
    print(f"   - Total offres brutes analysées : {len(all_raw_offers)}")
    print(f"   - Offres qualifiées PFE retenues : {len(qualified_offers)}")
    print(f"   - Nouvelles opportunités traitées: {new_offers_count}")
    print(f"   - Candidatures email réelles     : {emails_sent_count}")
    print(f"   - Historique total en base       : {len(state_manager.data.get('offers', {}))}")
    print("=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PFE Auto-Hunter Agent for Anas Mouqine")
    parser.add_argument("--live", action="store_true", help="Run in LIVE mode (actually send application emails)")
    parser.add_argument("--dry-run", action="store_true", help="Run in simulation mode (default)")
    parser.add_argument("--test-notifications", action="store_true", help="Send a test notification card to Telegram and Discord")
    parser.add_argument("--stats", action="store_true", help="Display statistics of tracked offers")
    parser.add_argument("--keyword", type=str, help="Search for a specific keyword instead of default AI keywords")
    parser.add_argument("--location", type=str, default="Casablanca", help="Search location (default: Casablanca)")
    parser.add_argument("--limit", type=int, help="Limit maximum offers processed")
    args = parser.parse_args()

    if args.test_notifications:
        sys.exit(test_notifications())

    if args.stats:
        sys.exit(display_stats())

    is_live = args.live and not args.dry_run
    custom_kws = [args.keyword] if args.keyword else None

    sys.exit(run_agent(dry_run=not is_live, custom_keywords=custom_kws, location=args.location, limit=args.limit))
