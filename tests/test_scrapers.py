"""Unit tests for scrapers and HTML parsing."""

from bs4 import BeautifulSoup
from src.scrapers.rekrute_scraper import ReKruteScraper
from src.scrapers.emploima_scraper import EmploiMaScraper
from src.scrapers.linkedin_guest_scraper import LinkedInGuestScraper


MOCK_REKRUTE_HTML = """
<div class="holder">
    <div class="section post-id">
        <h2><a class="titreJob" href="/offre-stage-pfe-data-casablanca.html">Stage PFE -- Data Engineer (Rémunéré)</a></h2>
        <a class="company" href="/company/tech-maroc">Tech Solutions Maroc</a>
        <em class="date">05/01/2026</em>
        <div class="info">
            Recherche stagiaire PFE pour conception de pipelines ETL sous Apache Airflow et Kafka.
            Stage rémunéré avec gratification mensuelle. Envoyez votre CV à rh@techmaroc.ma ou contactez-nous sur https://linkedin.com/in/rh-techmaroc.
        </div>
    </div>
</div>
"""

MOCK_EMPLOIMA_HTML = """
<div class="job-description-wrapper">
    <article class="job-ad">
        <h5><a class="job-title" href="/job/stage-pfe-ia-machine-learning-123">Stagiaire PFE en Intelligence Artificielle</a></h5>
        <div class="company-name">DataCorp Casablanca</div>
        <div class="job-location">Casablanca, Maroc</div>
        <div class="job-description">
            Projet de fin d'études autour des modèles LLM et agents autonomes.
            Contact direct : recrutement@datacorp.ma
        </div>
    </article>
</div>
"""

MOCK_LINKEDIN_HTML = """
<ul class="jobs-search__results-list">
    <li>
        <div class="base-card">
            <h3 class="base-search-card__title">Stage PFE Data & Cloud Architecture</h3>
            <h4 class="base-search-card__subtitle">Cloud Maroc SA</h4>
            <span class="job-search-card__location">Casablanca-Settat, Morocco</span>
            <a class="base-card__full-link" href="https://ma.linkedin.com/jobs/view/stage-pfe-data-123456?refId=abc"></a>
        </div>
    </li>
</ul>
"""


def test_rekrute_parsing():
    scraper = ReKruteScraper()
    soup = BeautifulSoup(MOCK_REKRUTE_HTML, "html.parser")
    offers = scraper.parse_html(soup)

    assert len(offers) == 1
    offer = offers[0]
    assert "Data Engineer" in offer.title
    assert offer.company == "Tech Solutions Maroc"
    assert offer.contact_email == "rh@techmaroc.ma"
    assert offer.linkedin_url == "https://linkedin.com/in/rh-techmaroc"
    assert "rekrute.com" in offer.url


def test_emploima_parsing():
    scraper = EmploiMaScraper()
    soup = BeautifulSoup(MOCK_EMPLOIMA_HTML, "html.parser")
    offers = scraper.parse_html(soup)

    assert len(offers) == 1
    offer = offers[0]
    assert "Intelligence Artificielle" in offer.title
    assert offer.company == "DataCorp Casablanca"
    assert offer.contact_email == "recrutement@datacorp.ma"


def test_linkedin_guest_parsing():
    scraper = LinkedInGuestScraper()
    soup = BeautifulSoup(MOCK_LINKEDIN_HTML, "html.parser")
    offers = scraper.parse_html(soup)

    assert len(offers) == 1
    offer = offers[0]
    assert "Stage PFE" in offer.title
    assert offer.company == "Cloud Maroc SA"
    assert "linkedin.com/jobs/view/stage-pfe-data-123456" in offer.linkedin_url
    assert "?" not in offer.linkedin_url  # Tracking params stripped


def test_linkedin_guest_detail_extraction(monkeypatch):
    scraper = LinkedInGuestScraper()
    mock_detail_html = """
    <div class="decorated-job-posting__details">
        <div class="show-more-less-html__markup">
            Stage PFE Data Engineer. Envoyez votre CV directement à notre équipe RH: stages.maroc@cloudcorp.com.
            Rémunération: 3500 DH/mois.
        </div>
        <div class="message-the-recruiter">
            <a href="https://ma.linkedin.com/in/sarah-recruteur-rh?trk=job_posting">Sarah Alami</a>
        </div>
    </div>
    """

    class MockResponse:
        status_code = 200
        text = mock_detail_html

    monkeypatch.setattr(scraper.session, "get", lambda url, timeout: MockResponse())

    desc, email, hr_link, hr_name = scraper._fetch_job_details(
        "https://ma.linkedin.com/jobs/view/123456", "Stage PFE Data"
    )

    assert email == "stages.maroc@cloudcorp.com"
    assert hr_link == "https://ma.linkedin.com/in/sarah-recruteur-rh"
    assert hr_name == "Sarah Alami"
    assert "3500 DH/mois" in desc


MOCK_DREAMJOB_HTML = """
<div class="post-item">
    <article>
        <h2 class="entry-title">
            <a class="entry-title-link" href="https://www.dreamjob.ma/stage/sqorus-maroc-lance-des-stages-pfe-data/">
                SQORUS Maroc lance des stages PFE en Data et IA
            </a>
        </h2>
        <div class="entry-summary">
            SQORUS Maroc ouvre deux stages PFE en Data Science et RAG.
        </div>
    </article>
</div>
"""

MOCK_MAROCANNONCES_HTML = """
<ul class="cars-list">
    <li>
        <a href="categorie/309/Offres-emploi/annonce/999/Stage-PFE-Data-Casablanca.html">
            <h3>Stage PFE Data & Machine Learning</h3>
            <span class="used-car-city">Casablanca</span>
        </a>
        <div class="desc">Stage PFE rémunéré pour modélisation prédictive.</div>
    </li>
</ul>
"""


def test_dreamjob_parsing(monkeypatch):
    from src.scrapers.dreamjob_scraper import DreamJobScraper
    scraper = DreamJobScraper()
    soup = BeautifulSoup(MOCK_DREAMJOB_HTML, "html.parser")

    # Mock article detail page
    monkeypatch.setattr(
        scraper,
        "_fetch_article_details",
        lambda url: ("Description PFE SQORUS. Contact: rh.ma@sqorus.com", "rh.ma@sqorus.com", "https://linkedin.com/posts/sqorus", None)
    )

    offers = scraper.parse_html(soup)
    assert len(offers) == 1
    offer = offers[0]
    assert "SQORUS" in offer.company
    assert offer.contact_email == "rh.ma@sqorus.com"
    assert offer.linkedin_url == "https://linkedin.com/posts/sqorus"
    assert "dreamjob.ma" in offer.url


def test_marocannonces_parsing():
    from src.scrapers.marocannonces_scraper import MarocAnnoncesScraper
    scraper = MarocAnnoncesScraper()
    soup = BeautifulSoup(MOCK_MAROCANNONCES_HTML, "html.parser")

    offers = scraper.parse_html(soup)
    assert len(offers) == 1
    offer = offers[0]
    assert "Stage PFE Data & Machine Learning" in offer.title
    assert "Casablanca" in offer.location
    assert "marocannonces.com" in offer.url


MOCK_TALENT_HTML = """
<div class="jobs">
    <article class="JobCard_card__TSiPB">
        <h2 class="JobCard_title__X32Qk">Stage PFE Data Engineer H/F</h2>
        <span class="JobCard_company__NmRol">Devoteam Maroc</span>
        <span class="JobCard_location__nmTtw">Casablanca, MA</span>
        <p class="JobCard_snippet">Dans le cadre du PFE 2026, recherche stagiaire Data & RAG. stages@devoteam.ma. Voir plus</p>
        <a href="/view?id=987654321">Voir plus</a>
    </article>
</div>
"""


def test_talent_parsing():
    from src.scrapers.talent_scraper import TalentScraper
    scraper = TalentScraper()
    soup = BeautifulSoup(MOCK_TALENT_HTML, "html.parser")

    offers = scraper.parse_html(soup)
    assert len(offers) == 1
    offer = offers[0]
    assert "Stage PFE Data Engineer" in offer.title
    assert offer.company == "Devoteam Maroc"
    assert "Casablanca" in offer.location
    assert offer.contact_email == "stages@devoteam.ma"
    assert "https://ma.talent.com/view?id=987654321" == offer.url
    assert "Voir plus" not in offer.description


MOCK_JOBLIA_HTML = """
<div class="ast-row">
    <article class="post">
        <h2 class="entry-title">
            <a href="https://joblia.ma/offres-emploi/artefact-recrute-des-consultants-data-a-casablanca/">Artefact recrute des data engineers et consultants IA à Casablanca</a>
        </h2>
        <time class="entry-date published" datetime="2026-10-22T15:37:18+00:00">22 octobre 2026</time>
        <div class="entry-content">
            Artefact recrute à Casablanca des stagiaires PFE Data & Machine Learning.
        </div>
    </article>
</div>
"""


def test_joblia_parsing():
    from src.scrapers.joblia_scraper import JobliaScraper
    scraper = JobliaScraper()
    soup = BeautifulSoup(MOCK_JOBLIA_HTML, "html.parser")

    offers = scraper.parse_html(soup)
    assert len(offers) == 1
    offer = offers[0]
    assert "Artefact recrute" in offer.title
    assert offer.company == "Artefact"
    assert "joblia.ma/offres-emploi/artefact" in offer.url
    assert offer.source == "joblia"
    assert offer.posted_date == "22 octobre 2026"
