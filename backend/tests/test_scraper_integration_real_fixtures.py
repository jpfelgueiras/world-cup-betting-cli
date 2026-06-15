"""Fixture-driven integration tests for the real scraper implementations.

These tests exercise the production scraper classes and their parser-backed
normalization logic against captured fixture payloads. That gives us stable CI
coverage without relying on live bookmaker availability or layout timing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Type

import pytest

from src.scrapers.betano_scraper import BetanoScraper
from src.scrapers.betclic_scraper import BetclicScraper
from src.scrapers.bwin_scraper import BwinScraper
from src.scrapers.lebull_scraper import LeBullScraper
from src.scrapers.solverde_scraper import SolverdeScraper

FIXTURES = Path(__file__).parent / "fixtures" / "scrapers"


def _read_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_betano_parser_extracts_realistic_match_cards():
    scraper = BetanoScraper()

    matches = scraper.parse_upcoming_matches_html(
        _read_text("betano_upcoming_matches.html")
    )

    assert len(matches) == 2
    first = matches[0]
    assert first.match_id == "BETANO-1001"
    assert first.home_team == "Portugal"
    assert first.away_team == "Brazil"
    assert first.home_win == pytest.approx(2.25)
    assert first.draw == pytest.approx(3.30)
    assert first.away_win == pytest.approx(3.05)
    assert first.has_ou25() is True
    assert first.has_btts() is True
    assert (
        first.url == "https://www.betano.pt/sport/futebol/portugal-brasil/BETANO-1001"
    )


def test_lebull_parser_extracts_representative_api_payload():
    scraper = LeBullScraper()

    matches = scraper.parse_upcoming_matches_json(
        _read_text("lebull_upcoming_matches.json")
    )

    assert len(matches) == 2
    first = matches[0]
    assert first.match_id == "LEBULL-5001"
    assert first.site == "lebull"
    assert first.site_name == "LeBull.pt"
    assert first.home_team == "Portugal"
    assert first.away_team == "Brazil"
    assert first.home_win == pytest.approx(2.24)
    assert first.draw == pytest.approx(3.35)
    assert first.away_win == pytest.approx(3.00)
    assert first.has_ou25() is True
    assert first.has_btts() is True
    assert (
        first.url
        == "https://www.lebull.pt/desporto/futebol/portugal-brasil/LEBULL-5001"
    )


@pytest.mark.parametrize(
    ("scraper_cls", "fixture_name", "match_id", "site_key"),
    [
        (BetclicScraper, "betclic_upcoming_matches.json", "BETCLIC-2001", "betclic"),
        (BwinScraper, "bwin_upcoming_matches.json", "BWIN-4001", "bwin"),
        (LeBullScraper, "lebull_upcoming_matches.json", "LEBULL-5001", "lebull"),
        (
            SolverdeScraper,
            "solverde_upcoming_matches.json",
            "SOLVERDE-3001",
            "solverde",
        ),
    ],
)
def test_json_backed_scrapers_parse_fixture_payloads(
    scraper_cls: Type[BetclicScraper | SolverdeScraper],
    fixture_name: str,
    match_id: str,
    site_key: str,
):
    scraper = scraper_cls()
    matches = scraper.parse_upcoming_matches_json(_read_text(fixture_name))

    assert len(matches) == 2
    first = matches[0]
    assert first.match_id == match_id
    assert first.site == site_key
    assert first.home_team == "Portugal"
    assert first.away_team == "Brazil"
    assert first.has_1x2() is True
    assert first.has_ou25() is True
    assert first.has_btts() is True
    assert first.url.startswith(scraper.base_url)


@pytest.mark.parametrize(
    ("scraper_cls", "fixture_name", "loader_name"),
    [
        (BetanoScraper, "betano_upcoming_matches.html", "parse_upcoming_matches_html"),
        (
            BetclicScraper,
            "betclic_upcoming_matches.json",
            "parse_upcoming_matches_json",
        ),
        (
            BwinScraper,
            "bwin_upcoming_matches.json",
            "parse_upcoming_matches_json",
        ),
        (
            LeBullScraper,
            "lebull_upcoming_matches.json",
            "parse_upcoming_matches_json",
        ),
        (
            SolverdeScraper,
            "solverde_upcoming_matches.json",
            "parse_upcoming_matches_json",
        ),
    ],
)
def test_get_match_odds_uses_real_scraper_matching_logic(
    monkeypatch,
    scraper_cls,
    fixture_name: str,
    loader_name: str,
):
    scraper = scraper_cls()
    payload = _read_text(fixture_name)

    def fake_request(_url, method="GET", params=None, data=None, timeout=30):
        class Response:
            text = payload

        return Response()

    monkeypatch.setattr(scraper, "_make_request", fake_request)

    odds = scraper.get_match_odds("Portugal", "Brazil")

    assert odds is not None
    assert odds.home_team == "Portugal"
    assert odds.away_team == "Brazil"
    assert odds.site == scraper.site_key
    assert odds.home_win is not None
    assert odds.url is not None
    assert "portugal" in odds.url.lower()


@pytest.mark.parametrize(
    ("scraper_cls", "fixture_name", "method_name"),
    [
        (BetanoScraper, "betano_upcoming_matches.html", "parse_upcoming_matches_html"),
        (
            BetclicScraper,
            "betclic_upcoming_matches.json",
            "parse_upcoming_matches_json",
        ),
        (
            BwinScraper,
            "bwin_upcoming_matches.json",
            "parse_upcoming_matches_json",
        ),
        (
            LeBullScraper,
            "lebull_upcoming_matches.json",
            "parse_upcoming_matches_json",
        ),
        (
            SolverdeScraper,
            "solverde_upcoming_matches.json",
            "parse_upcoming_matches_json",
        ),
    ],
)
def test_fixture_contract_contains_complete_markets(
    scraper_cls, fixture_name, method_name
):
    scraper = scraper_cls()
    parser = getattr(scraper, method_name)
    matches = parser(_read_text(fixture_name))

    for match in matches:
        assert (
            match.has_1x2()
        ), f"{scraper.site_key} missing 1X2 data for {match.match_id}"
        assert (
            match.has_ou25()
        ), f"{scraper.site_key} missing O/U data for {match.match_id}"
        assert (
            match.has_btts()
        ), f"{scraper.site_key} missing BTTS data for {match.match_id}"
