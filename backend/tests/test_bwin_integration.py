"""Integration coverage for the Bwin.pt bookmaker wiring."""

from click.testing import CliRunner

from src.api.models import LibraryConfig, SiteType
from src.api.routes import get_scrapers
from src.cli.main import cli, get_scrapers as get_cli_scrapers
from src.config import BETTING_SITES
from src.library import BettingInsights
from src.scrapers.bwin_scraper import BwinScraper


def test_bwin_is_in_central_bookmaker_config():
    assert "bwin" in BETTING_SITES
    assert BETTING_SITES["bwin"]["name"] == "Bwin.pt"
    assert BETTING_SITES["bwin"]["url"] == "https://www.bwin.pt"
    assert "bwin.pt" in BETTING_SITES["bwin"]["sports_url"]


def test_site_type_accepts_bwin():
    assert SiteType("bwin") is SiteType.BWIN


def test_default_library_config_exposes_bwin():
    config = LibraryConfig()
    assert "bwin" in config.enabled_sites


def test_api_scraper_factory_includes_bwin_for_all_and_specific():
    all_sites = {scraper.site_key for scraper in get_scrapers("all")}
    assert "bwin" in all_sites

    scrapers = get_scrapers("bwin")
    assert len(scrapers) == 1
    assert isinstance(scrapers[0], BwinScraper)


def test_library_initializes_bwin_when_enabled():
    insights = BettingInsights(cache_enabled=False, enabled_sites=["bwin"])
    assert [scraper.site_key for scraper in insights.scrapers] == ["bwin"]


def test_cli_scraper_factory_and_choice_include_bwin():
    scrapers = get_cli_scrapers("bwin")
    assert len(scrapers) == 1
    assert isinstance(scrapers[0], BwinScraper)

    result = CliRunner().invoke(cli, ["predict", "Portugal vs Brazil", "--site", "bwin", "--format", "json"])
    assert result.exit_code == 0
