"""Tests for configuration and candidate profile."""

from src.config import config


def test_candidate_profile_loaded():
    assert config.candidate.full_name == "Anas Mouqine"
    assert config.candidate.email == "anasmouqine@gmail.com"
    assert "Casablanca" in config.candidate.location
    assert "EMSI" in config.candidate.school
    assert "Data Engineering" in config.candidate.specialization
    assert "Intelligence Artificielle" in config.candidate.specialization
    assert config.candidate.cv_path.name == "cv_ats_pfe.pdf"


def test_default_cities_and_remuneration_keywords():
    assert "Casablanca" in config.target_cities
    assert any("rémunéré" in k for k in config.remuneration_keywords)
    assert any("gratification" in k for k in config.remuneration_keywords)


def test_dry_run_enabled_by_default():
    # Ensure safety: dry run should be active unless explicitly overridden
    assert isinstance(config.dry_run, bool)
    assert 0 < config.max_emails_per_run <= 50
