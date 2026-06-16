"""GoldenPark.pt sportsbook integration coverage."""

from pathlib import Path

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.models import LibraryConfig, MatchPredictionRequest, ScanRequest, SiteType
from src.api.routes import get_scrapers as get_api_scrapers
from src.cli.main import cli
from src.cli.main import get_scrapers as get_cli_scrapers
from src.config import BETTING_SITES
from src.library import BettingInsights
from src.scrapers import GoldenParkScraper

FIXTURES = Path(__file__).parent / "fixtures" / "scrapers"


def _read_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_config_and_api_models_include_goldenpark():
    assert "goldenpark" in BETTING_SITES
    assert BETTING_SITES["goldenpark"]["name"] == "GoldenPark.pt"
    assert BETTING_SITES["goldenpark"]["url"] == "https://www.goldenpark.pt"
    assert BETTING_SITES["goldenpark"]["enabled"] is True

    assert SiteType.GOLDENPARK.value == "goldenpark"
    assert (
        MatchPredictionRequest(
            home_team="Portugal", away_team="Brazil", site="goldenpark"
        ).site
        is SiteType.GOLDENPARK
    )
    assert ScanRequest(site="goldenpark").site is SiteType.GOLDENPARK
    assert "goldenpark" in LibraryConfig().enabled_sites


def test_goldenpark_parser_normalizes_fixture_payload_shape():
    scraper = GoldenParkScraper()

    matches = scraper.parse_upcoming_matches_json(
        _read_text("goldenpark_upcoming_matches.json")
    )

    assert len(matches) == 2
    first = matches[0]
    assert first.match_id == "GOLDENPARK-4001"
    assert first.site == "goldenpark"
    assert first.site_name == "GoldenPark.pt"
    assert first.home_team == "Portugal"
    assert first.away_team == "Brazil"
    assert first.match_date.isoformat().startswith("2026-06-15T20:00:00")
    assert first.home_win == pytest.approx(2.18)
    assert first.draw == pytest.approx(3.35)
    assert first.away_win == pytest.approx(3.10)
    assert first.over_2_5 == pytest.approx(1.82)
    assert first.under_2_5 == pytest.approx(1.92)
    assert first.btts_yes == pytest.approx(1.74)
    assert first.btts_no == pytest.approx(2.02)
    assert first.has_1x2() is True
    assert first.has_ou25() is True
    assert first.has_btts() is True
    assert first.market_name == "1x2"
    assert first.league == "International"
    assert first.competition == "World Cup"
    assert first.status == "ok"
    assert first.error is None
    assert first.url == (
        "https://www.goldenpark.pt/pt/apostas-desportivas/futebol/"
        "portugal-brasil/GOLDENPARK-4001"
    )
    assert first.source_url == first.url
    assert first.scrape_timestamp is not None


def test_goldenpark_match_lookup_uses_fixture_parser_when_request_succeeds(monkeypatch):
    scraper = GoldenParkScraper()
    payload = _read_text("goldenpark_upcoming_matches.json")

    def fake_request(_url, method="GET", params=None, data=None, timeout=30):
        class Response:
            text = payload

        return Response()

    monkeypatch.setattr(scraper, "_make_request", fake_request)

    odds = scraper.get_match_odds("Portugal", "Brazil")

    assert odds is not None
    assert odds.match_id == "GOLDENPARK-4001"
    assert odds.site == "goldenpark"
    assert odds.home_win == pytest.approx(2.18)


def test_goldenpark_fallback_semantics_return_tagged_mock_odds(monkeypatch):
    scraper = GoldenParkScraper()

    def fail_request(*_args, **_kwargs):
        raise RuntimeError("live scraping disabled in test")

    monkeypatch.setattr(scraper, "_make_request", fail_request)

    odds = scraper.get_match_odds("Portugal", "Brazil")

    assert odds is not None
    assert odds.site == "goldenpark"
    assert odds.site_name == "GoldenPark.pt"
    assert odds.has_1x2() is True
    assert odds.market_name == "1x2"
    assert odds.status == "fallback"
    assert odds.competition == "GoldenPark fallback"
    assert odds.error == (
        "Live GoldenPark.pt scrape unavailable; deterministic fallback odds used."
    )
    assert odds.url.startswith("https://www.goldenpark.pt")
    assert odds.source_url == odds.url


def test_goldenpark_is_wired_into_cli_api_and_library():
    assert [s.__class__.__name__ for s in get_cli_scrapers("goldenpark")] == [
        "GoldenParkScraper"
    ]
    assert any(
        s.__class__.__name__ == "GoldenParkScraper" for s in get_cli_scrapers("all")
    )
    assert [s.__class__.__name__ for s in get_api_scrapers("goldenpark")] == [
        "GoldenParkScraper"
    ]

    insights = BettingInsights(enabled_sites=["goldenpark"], cache_enabled=False)
    assert [s.__class__.__name__ for s in insights.scrapers] == ["GoldenParkScraper"]

    insights.update_config(enabled_sites=["goldenpark"])
    assert [s.__class__.__name__ for s in insights.scrapers] == ["GoldenParkScraper"]


def test_api_config_and_bookmakers_expose_goldenpark(monkeypatch):
    monkeypatch.setenv("DEV_MODE", "true")
    client = TestClient(create_app())

    bookmakers = client.get("/api/v1/bookmakers").json()
    assert any(
        bookmaker["site_key"] == "goldenpark"
        and bookmaker["site_name"] == "GoldenPark.pt"
        for bookmaker in bookmakers
    )

    config = client.get("/api/v1/config").json()
    assert "goldenpark" in config["enabled_sites"]


def test_cli_accepts_goldenpark_site_choice_for_prediction(monkeypatch):
    class FakeScraper:
        site_name = "GoldenPark.pt"

        def get_match_odds(self, home_team, away_team):
            return None

    monkeypatch.setattr("src.cli.main.get_scrapers", lambda site: [FakeScraper()])

    result = CliRunner().invoke(
        cli, ["predict", "Portugal vs Brazil", "--site", "goldenpark"]
    )

    assert result.exit_code == 1
    assert "Invalid value for '--site'" not in result.output
    assert "No odds available" in result.output
