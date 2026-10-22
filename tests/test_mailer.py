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

