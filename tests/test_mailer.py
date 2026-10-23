"""Unit tests for CoverLetterGenerator and EmailSender."""

from src.models.offer import JobOffer
from src.mailer.cover_letter_generator import CoverLetterGenerator
from src.mailer.email_sender import EmailSender


def test_cover_letter_generator():
    offer = JobOffer(
        title="Stage PFE Data & IA",
        company="Orange Maroc",
        url="https://example.com/orange-pfe",
        source="rekrute",
        contact_email="recrutement@orange.com",
        matched_skills=["Python", "Apache Airflow"]
    )

    subject = CoverLetterGenerator.generate_subject(offer)
    body = CoverLetterGenerator.generate_body(offer)

    assert "Anas Mouqine" in subject
    assert "Orange Maroc" in body
    assert "EMSI Casablanca" in body
    assert "COSUMAR" in body
    assert "SEWS-CABINET" in body
    assert "cv_ats_pfe" not in body  # It should mention CV cleanly, not raw filename
    assert "Curriculum Vitae" in body


def test_email_sender_dry_run():
    offer = JobOffer(
        title="Stage PFE Data Engineering",
        company="Inwi",
        url="https://example.com/inwi",
        source="rekrute",
        contact_email="rh@inwi.ma"
    )

    sender = EmailSender()
    sender.dry_run = True  # Ensure dry-run
    success = sender.send_application(offer)

    assert success is True


def test_cover_letter_html_generation():
    offer = JobOffer(
        title="Stage PFE Data & Intelligence Artificielle",
        company="Capgemini Engineering",
        url="https://example.com/capgemini",
        source="linkedin_guest",
        matched_skills=["Python", "Apache Airflow", "Kafka"]
    )

    html_body = CoverLetterGenerator.generate_html_body(offer)
    assert "<!DOCTYPE html>" in html_body
    assert "Capgemini Engineering" in html_body
    assert "EMSI Casablanca" in html_body
    assert "COSUMAR" in html_body
    assert "SEWS-CABINET" in html_body
    assert "Enterprise Media Lakehouse" in html_body
    assert "anasmouqine@gmail.com" in html_body


def test_formal_cover_letter_coface_datalab(tmp_path):
    offer = JobOffer(
        title="Stages PFE 2026/2027 - DataLab (Pré-Embauche)",
        company="Coface",
        location="Casablanca, Maroc",
        url="https://example.com/coface-pfe-datalab",
        source="rekrute",
        description="Stages PFE 2026/2027 - DataLab (Pré-Embauche) à Casablanca. Modélisation prédictive, scoring et big data.",
        matched_skills=["Python", "Machine Learning", "Data Engineering", "SQL"]
    )

    text_letter = CoverLetterGenerator.generate_formal_letter_text(offer)
    html_letter = CoverLetterGenerator.generate_formal_letter_html(offer)

    # Assert key personalization for Coface DataLab & Pre-embauche
    assert "Anas Mouqine" in text_letter or "Anas MOUQINE" in text_letter
    assert "Coface" in text_letter
    assert "DataLab" in text_letter
    assert "Pré-Embauche" in text_letter or "pré-embauche" in text_letter
    assert "EMSI Casablanca" in text_letter
    assert "COSUMAR" in text_letter
    assert "SEWS-CABINET" in text_letter
    assert "Enterprise Media Lakehouse" in text_letter

    assert "<!DOCTYPE html>" in html_letter
    assert "Coface" in html_letter
    assert "DataLab" in html_letter
    assert "window.print()" in html_letter
    assert "copyLetterText()" in html_letter

    # Test saving to disk
    paths = CoverLetterGenerator.save_letter_for_offer(
        offer,
        output_dir=tmp_path,
        custom_slug="Lettre_Motivation_Coface_DataLab_Anas_Mouqine"
    )
    assert paths["html"].exists()
    assert paths["txt"].exists()
    assert paths["html"].stat().st_size > 500
    assert paths["txt"].stat().st_size > 500


def test_formal_cover_letter_natixis_cib_ml_research(tmp_path):
    offer = JobOffer(
        title="Stage de 6 mois à Natixis CIB : ML Research",
        company="Natixis CIB",
        location="Paris / Casablanca",
        url="mailto:baptiste.grivot-ext@natixis.com",
        source="direct_email",
        contact_email="baptiste.grivot-ext@natixis.com",
        hr_name="Baptiste Grivot",
        description="Stage de 6 mois à Natixis CIB : ML Research pour commencer début/mi janvier 2027.",
        matched_skills=["Machine Learning", "Python", "Deep Learning", "PyTorch"]
    )

    # Test email body
    email_body = CoverLetterGenerator.generate_body(offer)
    assert "Bonjour Monsieur Grivot," in email_body
    assert "début / mi-janvier 2027" in email_body
    assert "Natixis CIB" in email_body

    # Test formal letters (text & HTML)
    text_letter = CoverLetterGenerator.generate_formal_letter_text(offer)
    html_letter = CoverLetterGenerator.generate_formal_letter_html(offer)

    assert "Baptiste GRIVOT" in text_letter
    assert "ML Research" in text_letter
    assert "janvier 2027" in text_letter
    assert "Monsieur GRIVOT, Madame, Monsieur," in text_letter
    assert "PyTorch" in text_letter

    assert "<!DOCTYPE html>" in html_letter
    assert "Baptiste GRIVOT" in html_letter
    assert "ML Research" in html_letter
    assert "janvier 2027" in html_letter
    assert "window.print()" in html_letter

    # Test saving to disk
    paths = CoverLetterGenerator.save_letter_for_offer(
        offer,
        output_dir=tmp_path,
        custom_slug="Lettre_Motivation_Natixis_CIB_ML_Research_Anas_Mouqine"
    )
    assert paths["html"].exists()
    assert paths["txt"].exists()
    assert paths["html"].stat().st_size > 500
    assert paths["txt"].stat().st_size > 500


def test_resend_api_mock():
    from unittest.mock import patch, MagicMock
    sender = EmailSender()
    sender.resend_api_key = "re_mock_123"
    sender.dry_run = False

    offer = JobOffer(
        title="Stage PFE IA",
        company="TestCorp",
        url="https://example.com/test",
        source="rekrute",
        contact_email="rh@testcorp.ma"
    )

    with patch("requests.post") as mock_post, patch("time.sleep"):
        mock_post.return_value = MagicMock(status_code=200)
        success = sender.send_application(offer)
        assert success is True
        assert mock_post.called
        call_url = mock_post.call_args[0][0]
        assert "api.resend.com" in call_url


def test_linkedin_applier_initialization():
    from src.browser.linkedin_applier import LinkedInApplier
    applier = LinkedInApplier(li_at_cookie="")
    assert applier.is_configured() is False

    offer = JobOffer(
        title="Stage PFE Data",
        company="LinkedIn Corp",
        url="https://www.linkedin.com/jobs/view/123",
        source="linkedin_guest",
    )
    res = applier.apply(offer)
    assert res["applied"] is False


def test_rekrute_applier_initialization():
    from src.browser.rekrute_applier import ReKruteApplier
    applier = ReKruteApplier(email="test@example.com", password="")
    assert applier.is_configured() is True

    offer_non_rekrute = JobOffer(
        title="Stage PFE Data",
        company="Other Corp",
        url="https://example.com/other",
        source="linkedin",
    )
    res = applier.apply(offer_non_rekrute)
    assert res["status"] == "skipped"
    assert res["reason"] == "not_rekrute_url"


def test_marocannonces_applier_initialization():
    from src.browser.marocannonces_applier import MarocAnnoncesApplier
    applier = MarocAnnoncesApplier()
    assert applier.is_configured() is True

    offer_non_ma = JobOffer(
        title="Stage PFE Data",
        company="Other Corp",
        url="https://example.com/other",
        source="rekrute",
    )
    res = applier.apply(offer_non_ma)
    assert res["status"] == "skipped"
    assert res["reason"] == "not_marocannonces_url"


def test_auto_applier_router():
    from src.browser.auto_applier import AutoApplierRouter
    router = AutoApplierRouter()

    offer_rekrute = JobOffer(
        title="Stage PFE Java",
        company="TechCorp",
        url="https://www.rekrute.com/offre-emploi-123.html",
        source="rekrute"
    )
    assert router.can_apply(offer_rekrute) is True

    offer_ma = JobOffer(
        title="Stage PFE Web",
        company="DevCorp",
        url="https://www.marocannonces.com/maroc/offre-123.html",
        source="marocannonces"
    )
    assert router.can_apply(offer_ma) is True

    offer_portal = JobOffer(
        title="Stage PFE Cloud",
        company="CloudCorp",
        url="https://careers.cloudcorp.ma/apply/456",
        source="career_portal"
    )
    assert router.can_apply(offer_portal) is True



