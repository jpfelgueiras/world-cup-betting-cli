"""CasinoPortugal.pt scraper and integration coverage."""

from pathlib import Path

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient

from src.api.app import app
from src.api.models import SiteType
from src.api.routes import get_scrapers as api_get_scrapers
from src.cli.main import cli
from src.cli.main import get_scrapers as cli_get_scrapers
from src.config import BETTING_SITES
from src.library import BettingInsights
from src.scrapers.base_scraper import OddsData, ScraperError
from src.scrapers.casinoportugal_scraper import CasinoPortugalScraper

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "scrapers"
    / "casinoportugal_upcoming_matches.json"
)


class TestCasinoPortugalConfig:
    def test_betting_sites_metadata_includes_casinoportugal(self):
        config = BETTING_SITES["casinoportugal"]

        assert config["name"] == "Casino Portugal"
        assert config["url"] == "https://www.casinoportugal.pt"
        assert config["sports_url"] == "https://www.casinoportugal.pt/desporto"
        assert config["enabled"] is True

    def test_site_type_enum_includes_casinoportugal(self):
        assert SiteType.CASINOPORTUGAL.value == "casinoportugal"


class TestCasinoPortugalScraper:
    @pytest.fixture
    def scraper(self):
        return CasinoPortugalScraper()

    def test_init_configures_correctly(self, scraper):
        assert scraper.site_key == "casinoportugal"
        assert scraper.site_name == "Casino Portugal"
        assert scraper.base_url == "https://www.casinoportugal.pt"
        assert scraper.sports_url == "https://www.casinoportugal.pt/desporto"
        assert (
            scraper.offer_api_url == "https://aio-offer-distribution.de-2.nsoft.cloud"
        )
        assert scraper.tenant_uuid == "10ca03ad-9dc4-4320-bbc2-c93a42194d08"

    def test_parse_fixture_normalizes_nsoft_offer_shape(self, scraper):
        matches = scraper.parse_upcoming_matches_json(
            FIXTURE.read_text(encoding="utf-8")
        )

        assert len(matches) == 1
        match = matches[0]
        assert isinstance(match, OddsData)
        assert match.match_id == "casinoportugal_808583"
        assert match.site == "casinoportugal"
        assert match.site_name == "Casino Portugal"
        assert match.home_team == "Portugal"
        assert match.away_team == "República Democrática do Congo"
        assert match.match_date.isoformat() == "2026-06-17T17:00:00+00:00"
        assert match.home_win == pytest.approx(1.25)
        assert match.draw == pytest.approx(5.20)
        assert match.away_win == pytest.approx(9.40)
        assert match.over_2_5 == pytest.approx(1.62)
        assert match.under_2_5 == pytest.approx(2.07)
        assert match.btts_yes == pytest.approx(2.12)
        assert match.btts_no == pytest.approx(1.59)
        assert match.has_1x2() is True
        assert match.has_ou25() is True
        assert match.has_btts() is True
        assert (
            match.url == "https://www.casinoportugal.pt/desporto/d_all/ctg_678/e_808583"
        )

    def test_parse_fixture_preserves_status_metadata(self, scraper):
        match = scraper.parse_upcoming_matches_json(
            FIXTURE.read_text(encoding="utf-8")
        )[0]
        data = match.to_dict()

        assert data["site"] == "casinoportugal"
        assert data["market_name"] == "1x2"
        assert data["league"] == "Campeonato do Mundo FIFA"
        assert data["competition"] == "Internacional"
        assert data["status"] == "ok"
        assert data["error"] is None
        assert data["source_url"] == match.url
        assert data["scrape_timestamp"] == data["last_updated"]

    def test_get_upcoming_matches_falls_back_when_live_unavailable(
        self, scraper, monkeypatch
    ):
        def fail_request(*args, **kwargs):
            raise ScraperError("live blocked")

        monkeypatch.setattr(scraper, "_make_request", fail_request)

        matches = scraper.get_upcoming_matches(days_ahead=7)

        assert len(matches) > 0
        assert all(match.site == "casinoportugal" for match in matches)
        assert all(match.has_1x2() for match in matches)

    def test_get_match_odds_finds_fixture_match(self, scraper, monkeypatch):
        monkeypatch.setattr(
            scraper,
            "get_upcoming_matches",
            lambda days_ahead=7: scraper.parse_upcoming_matches_json(
                FIXTURE.read_text(encoding="utf-8")
            ),
        )

        odds = scraper.get_match_odds("Portugal", "República Democrática do Congo")

        assert odds is not None
        assert odds.site == "casinoportugal"
        assert odds.home_win == pytest.approx(1.25)


class TestCasinoPortugalWiring:
    def test_backend_scraper_exports_casinoportugal(self):
        from src.scrapers import CasinoPortugalScraper as ExportedScraper

        assert ExportedScraper is CasinoPortugalScraper

    def test_api_get_scrapers_includes_casinoportugal_for_all_and_specific(self):
        all_site_keys = {scraper.site_key for scraper in api_get_scrapers("all")}
        specific = api_get_scrapers("casinoportugal")

        assert "casinoportugal" in all_site_keys
        assert len(specific) == 1
        assert specific[0].site_key == "casinoportugal"

    def test_api_bookmakers_endpoint_includes_casinoportugal(self, monkeypatch):
        monkeypatch.setenv("DEV_MODE", "true")
        monkeypatch.setenv("VALID_API_KEYS", "test-key")
        client = TestClient(app)

        response = client.get("/api/v1/bookmakers", headers={"X-API-Key": "test-key"})

        assert response.status_code == 200
        bookmakers = response.json()
        assert any(
            bookmaker["site_key"] == "casinoportugal" for bookmaker in bookmakers
        )

    def test_cli_get_scrapers_includes_casinoportugal_for_all_and_specific(self):
        all_site_keys = [scraper.site_key for scraper in cli_get_scrapers("all")]
        specific = cli_get_scrapers("casinoportugal")

        assert "casinoportugal" in all_site_keys
        assert len(specific) == 1
        assert specific[0].site_key == "casinoportugal"

    def test_cli_accepts_casinoportugal_site_choice(self):
        runner = CliRunner()
        result = runner.invoke(cli, ["sites"])

        assert result.exit_code == 0
        assert "Casino Portugal" in result.output

    def test_library_initializes_casinoportugal_when_enabled(self):
        insights = BettingInsights(
            enabled_sites=["casinoportugal"], cache_enabled=False
        )

        assert len(insights.scrapers) == 1
        assert insights.scrapers[0].site_key == "casinoportugal"

    def test_library_update_config_can_select_casinoportugal(self):
        insights = BettingInsights(enabled_sites=["betano"], cache_enabled=False)

        insights.update_config(enabled_sites=["casinoportugal"])

        assert len(insights.scrapers) == 1
        assert insights.scrapers[0].site_key == "casinoportugal"

    def test_library_bookmakers_include_casinoportugal_metadata(self):
        insights = BettingInsights(
            enabled_sites=["casinoportugal"], cache_enabled=False
        )

        bookmakers = insights.get_bookmakers()

        assert any(bookmaker["key"] == "casinoportugal" for bookmaker in bookmakers)
