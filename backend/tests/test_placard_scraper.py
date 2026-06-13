"""Tests for Placard.pt scraper integration."""

import json
from datetime import datetime, timezone
from pathlib import Path

from click.testing import CliRunner

from src.api import routes
from src.cli.main import cli, get_scrapers as get_cli_scrapers
from src.library import BettingInsights
from src.scrapers import PlacardScraper


FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "scrapers" / "placard_upcoming_matches.json"
)


def test_placard_parser_normalizes_widget_json_fixture():
    scraper = PlacardScraper()
    matches = scraper.parse_upcoming_matches_json(FIXTURE_PATH.read_text())

    assert len(matches) == 2
    first = matches[0]
    assert first.site == "placard"
    assert first.site_name == "Placard.pt"
    assert first.match_id == "plc-1001"
    assert first.home_team == "FC Porto"
    assert first.away_team == "SL Benfica"
    assert first.match_date == datetime(2026, 6, 15, 20, 0, tzinfo=timezone.utc)
    assert first.home_win == 2.15
    assert first.draw == 3.35
    assert first.away_win == 3.10
    assert first.market_name == "Resultado do Jogo"
    assert first.competition == "Liga Portugal"
    assert first.league is None
    assert first.status == "upcoming"
    assert first.source_url == (
        "https://apostas.placard.pt/apostas/futebol/liga-portugal/fc-porto-sl-benfica"
    )
    assert first.scrape_timestamp is not None
    assert first.has_1x2()
    assert first.url == first.source_url

    second = matches[1]
    assert second.market_name == "1X2"
    assert second.competition == "Sporting CP - SC Braga"
    assert second.league == "Liga Portugal"
    assert second.status == "upcoming"


def test_placard_match_lookup_uses_fixture_data_when_live_request_fails(monkeypatch):
    scraper = PlacardScraper()
    fixture_payload = FIXTURE_PATH.read_text()

    def fake_make_request(_url):
        class Response:
            text = fixture_payload

        return Response()

    monkeypatch.setattr(scraper, "_make_request", fake_make_request)

    odds = scraper.get_match_odds("sporting cp", "sc braga")

    assert odds is not None
    assert odds.site == "placard"
    assert odds.home_team == "Sporting CP"
    assert odds.away_team == "SC Braga"
    assert odds.home_win == 1.80
    assert odds.draw == 3.60
    assert odds.away_win == 4.20


def test_placard_export_and_scraper_routing_are_active():
    assert PlacardScraper().site_key == "placard"

    api_scrapers = routes.get_scrapers("placard")
    assert [scraper.site_key for scraper in api_scrapers] == ["placard"]

    cli_scrapers = get_cli_scrapers("placard")
    assert [scraper.site_key for scraper in cli_scrapers] == ["placard"]

    insights = BettingInsights(enabled_sites=["placard"], cache_enabled=False)
    assert [scraper.site_key for scraper in insights.scrapers] == ["placard"]

    insights.update_config(enabled_sites=["placard"])
    assert [scraper.site_key for scraper in insights.scrapers] == ["placard"]


def test_cli_site_choices_include_placard_for_predict_and_scan():
    runner = CliRunner()

    predict_help = runner.invoke(cli, ["predict", "--help"])
    scan_help = runner.invoke(cli, ["scan", "--help"])

    assert predict_help.exit_code == 0
    assert scan_help.exit_code == 0
    assert "placard" in predict_help.output
    assert "placard" in scan_help.output


def test_api_health_includes_placard_bookmaker_status():
    import asyncio

    response = asyncio.run(routes.health_check())
    site_keys = [bookmaker.site_key for bookmaker in response.bookmakers]

    assert "placard" in site_keys
