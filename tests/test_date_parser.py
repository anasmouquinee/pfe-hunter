"""Unit tests for date parser and offer freshness evaluator."""

from src.models.offer import JobOffer
from src.matcher.evaluator import OfferEvaluator
from src.utils.date_parser import parse_offer_age_days, is_recent_offer


def test_parse_offer_age_days():
    # ISO date from today/yesterday
    assert parse_offer_age_days("2026-10-22T10:00:00+00:00") <= 1
    assert parse_offer_age_days("Aujourd'hui à 15:30") == 0
    assert parse_offer_age_days("Hier à 10:00") == 1
    assert parse_offer_age_days("il y a 3 jours") == 3
    assert parse_offer_age_days("il y a 2 semaines") == 14
    assert parse_offer_age_days("il y a 1 mois") == 30
    assert parse_offer_age_days("") == 999
    assert parse_offer_age_days(None) == 999


def test_is_recent_offer():
    assert is_recent_offer("Aujourd'hui", max_days=14) is True
    assert is_recent_offer("il y a 3 jours", max_days=14) is True
    assert is_recent_offer("il y a 2 semaines", max_days=14) is True
    assert is_recent_offer("il y a 3 semaines", max_days=14) is False
    assert is_recent_offer("il y a 2 mois", max_days=14) is False
    # If no date was found on the job board, do not discard blindly
    assert is_recent_offer(None, max_days=14) is True
    assert is_recent_offer("", max_days=14) is True


def test_evaluator_is_recent_enough():
    evaluator = OfferEvaluator()

    recent_offer = JobOffer(
        title="Stage PFE IA",
        company="Capgemini",
        url="https://example.com/1",
        source="joblia",
        posted_date="il y a 2 jours"
    )
    assert evaluator.is_recent_enough(recent_offer, max_days=14) is True

    old_offer = JobOffer(
        title="Stage PFE IA",
        company="Orange",
        url="https://example.com/2",
        source="joblia",
        posted_date="il y a 2 mois"
    )
    assert evaluator.is_recent_enough(old_offer, max_days=14) is False
