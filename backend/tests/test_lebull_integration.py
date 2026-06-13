"""Integration and parser coverage for the LeBull.pt bookmaker wiring."""

from datetime import datetime, timezone
from pathlib import Path

from click.testing import CliRunner

from src.api import routes
from src.api.models import SiteType
from src.cli.main import cli, get_scrapers as get_cli_scrapers
from src.config import BETTING_SITES
from src.library import BettingInsights
from src.scrapers import LeBullScraper


FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "scrapers" / "lebull_upcoming_matches.json"
)


def test_lebull_is_in_central_bookmaker_config():
    assert "lebull" in BETTING_SITES
    assert BETTING_SITES["lebull"]["name"] == "LeBull.pt"
    assert BETTING_SITES["lebull"]["url"] == "https://www.lebull.pt"
    assert "lebull.pt" in BETTING_SITES["lebull"]["sports_url"]


def test_site_type_accepts_lebull_and_library_supports_explicit_enablement():
    assert SiteType("lebull") is SiteType.LEBULL

    insights = BettingInsights(enabled_sites=["lebull"], cache_enabled=False)
    assert [scraper.site_key for scraper in insights.scrapers] == ["lebull"]


def test_lebull_parser_normalizes_fixture_payload_shapes():
    scraper = LeBullScraper()
    matches = scraper.parse_upcoming_matches_json(FIXTURE_PATH.read_text())

    assert len(matches) == 2

    first = matches[0]
    assert first.match_id == "LEBULL-5001"
    assert first.site == "lebull"
    assert first.site_name == "LeBull.pt"
    assert first.home_team == "Portugal"
    assert first.away_team == "Brazil"
    assert first.match_date == datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc)
    assert first.home_win == 2.24
    assert first.draw == 3.35
    assert first.away_win == 3.00
    assert first.market_name == "1x2"
    assert first.competition == "World Cup"
    assert first.league is None
    assert first.status == "ok"
    assert first.source_url == (
        "https://www.lebull.pt/desporto/futebol/portugal-brasil/LEBULL-5001"
    )
    assert first.url == first.source_url
    assert first.has_1x2()
    assert first.has_ou25()
    assert first.has_btts()
    assert first.scrape_timestamp is not None

    second = matches[1]
    assert second.match_id == "LEBULL-5002"
    assert second.home_team == "Spain"
    assert second.away_team == "Germany"
    assert second.match_date == datetime(2026, 6, 16, 18, 0, tzinfo=timezone.utc)
    assert second.home_win == 2.40
    assert second.draw == 3.16
    assert second.away_win == 2.95
    assert second.league == "World Cup"
    assert second.competition is None
    assert second.source_url == (
        "https://www.lebull.pt/desporto/futebol/spain-germany/LEBULL-5002"
    )


def test_lebull_match_lookup_uses_fixture_data_when_request_succeeds(monkeypatch):
    scraper = LeBullScraper()
    fixture_payload = FIXTURE_PATH.read_text()

    def fake_make_request(_url):
        class Response:
            text = fixture_payload

        return Response()

    monkeypatch.setattr(scraper, "_make_request", fake_make_request)

    odds = scraper.get_match_odds("spain", "germany")

    assert odds is not None
    assert odds.site == "lebull"
    assert odds.home_team == "Spain"
    assert odds.away_team == "Germany"
    assert odds.home_win == 2.40
    assert odds.draw == 3.16
    assert odds.away_win == 2.95


def test_lebull_export_and_scraper_routing_are_active():
    assert LeBullScraper().site_key == "lebull"

    api_scrapers = routes.get_scrapers("lebull")
    assert [scraper.site_key for scraper in api_scrapers] == ["lebull"]

    cli_scrapers = get_cli_scrapers("lebull")
    assert [scraper.site_key for scraper in cli_scrapers] == ["lebull"]

    insights = BettingInsights(enabled_sites=["lebull"], cache_enabled=False)
    assert [scraper.site_key for scraper in insights.scrapers] == ["lebull"]

    insights.update_config(enabled_sites=["lebull"])
    assert [scraper.site_key for scraper in insights.scrapers] == ["lebull"]


def test_cli_site_choices_include_lebull_for_predict_and_scan():
    runner = CliRunner()

    predict_help = runner.invoke(cli, ["predict", "--help"])
    scan_help = runner.invoke(cli, ["scan", "--help"])

    assert predict_help.exit_code == 0
    assert scan_help.exit_code == 0
    assert "lebull" in predict_help.output
    assert "lebull" in scan_help.output


def test_api_health_includes_lebull_bookmaker_status():
    import asyncio

    response = asyncio.run(routes.health_check())
    site_keys = [bookmaker.site_key for bookmaker in response.bookmakers]

    assert "lebull" in site_keys
