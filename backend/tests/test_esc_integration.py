"""Integration tests proving ESC is wired into public scraper entry points."""

import asyncio

from click.testing import CliRunner

from src.api.models import SiteType
from src.api.routes import get_scrapers as get_api_scrapers, health_check
from src.cli.main import cli, get_scrapers as get_cli_scrapers
from src.library import BettingInsights
from src.scrapers.esc_scraper import EscScraper


def _site_keys(scrapers):
    return [scraper.site_key for scraper in scrapers]


def test_api_get_scrapers_includes_esc_for_all_and_direct_selection():
    assert "esc" in _site_keys(get_api_scrapers("all"))
    assert _site_keys(get_api_scrapers("esc")) == ["esc"]


def test_api_site_type_allows_esc():
    assert SiteType("esc") is SiteType.ESC


def test_cli_get_scrapers_includes_esc_for_all_and_direct_selection():
    assert "esc" in _site_keys(get_cli_scrapers("all"))
    assert _site_keys(get_cli_scrapers("esc")) == ["esc"]


def test_cli_site_choice_accepts_esc():
    predict_help = CliRunner().invoke(cli, ["predict", "--help"])

    assert predict_help.exit_code == 0
    assert "esc" in predict_help.output


def test_library_initializes_and_updates_esc_scraper():
    insights = BettingInsights(enabled_sites=["esc"], cache_enabled=False)
    assert len(insights.scrapers) == 1
    assert isinstance(insights.scrapers[0], EscScraper)

    insights.update_config(enabled_sites=["betano", "esc"])
    assert "esc" in _site_keys(insights.scrapers)


def test_bookmaker_health_includes_esc():
    response = asyncio.run(health_check())
    statuses = {bookmaker.site_key: bookmaker for bookmaker in response.bookmakers}

    assert "esc" in statuses
    assert statuses["esc"].site_name == "ESC Online / Estoril Sol Casinos"
