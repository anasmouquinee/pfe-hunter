"""Unit tests for text extraction, URL cleaning, and regex normalization."""

from src.utils.text_extractor import clean_url, extract_emails, extract_linkedin_urls, extract_recruiter_profile


def test_clean_url_removes_tracking_and_fragments():
    url_with_tracking = "https://ma.linkedin.com/jobs/view/stage-pfe-data-123456?trk=public_jobs_topcard-title&refId=abcde#details"
    cleaned = clean_url(url_with_tracking)
    assert cleaned == "https://ma.linkedin.com/jobs/view/stage-pfe-data-123456"
    assert "?" not in cleaned
    assert "#" not in cleaned


def test_extract_emails_ignores_media_assets():
    text = (
        "Envoyez vos CVs à stages@techcorp.ma ou rh.recrutement@societe.com. "
        "Logo téléchargeable sur image@logo.png ou banner@hero.jpg. Contact direct: anas@emsi.ma. "
        "Pour réclamations écrivez à contact@joblia.ma ou support@dreamjob.ma."
    )
    emails = extract_emails(text)
    assert "stages@techcorp.ma" in emails
    assert "rh.recrutement@societe.com" in emails
    assert "anas@emsi.ma" in emails
    assert "image@logo.png" not in emails
    assert "banner@hero.jpg" not in emails
    assert "contact@joblia.ma" not in emails
    assert "support@dreamjob.ma" not in emails

    text_system = "Contactez rh@company.ma mais pas noreply@company.ma ou support@emploi.ma ou <admin@company.ma>."
    emails_system = extract_emails(text_system)
    assert "rh@company.ma" in emails_system
    assert "noreply@company.ma" not in emails_system
    assert "support@emploi.ma" not in emails_system



def test_extract_recruiter_profile():
    text = (
        "Offre publiée par Sarah Alami, Talent Acquisition Specialist. "
        "Contactez-la sur https://ma.linkedin.com/in/sarah-alami-recruteur?trk=share "
        "ou consultez l'entreprise sur https://linkedin.com/company/tech-corp"
    )
    recruiter_url = extract_recruiter_profile(text)
    assert recruiter_url == "https://ma.linkedin.com/in/sarah-alami-recruteur"
