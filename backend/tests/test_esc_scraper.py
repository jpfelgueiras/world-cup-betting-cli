"""Tests for the ESCOnline / Estoril Sol scraper integration."""

from pathlib import Path

import pytest

from src.config import BETTING_SITES
from src.scrapers.esc_scraper import EscScraper
from src.scrapers import EscScraper as ExportedEscScraper
from src.scrapers.base_scraper import OddsData, ScraperError

FIXTURES = Path(__file__).parent / "fixtures" / "scrapers"


def test_esc_config_uses_srij_listed_estorilsolcasinos_domain():
    config = BETTING_SITES["esc"]

    assert config["name"] == "ESC Online / Estoril Sol Casinos"
    assert config["url"] == "https://www.estorilsolcasinos.pt"
    assert config["sports_url"] == (
        "https://www.estorilsolcasinos.pt/pt/betting/sport/844/matches/date-0"
    )


def test_esc_scraper_is_exported_and_configured():
    scraper = EscScraper()

    assert ExportedEscScraper is EscScraper
    assert scraper.site_key == "esc"
    assert scraper.site_name == "ESC Online / Estoril Sol Casinos"
    assert scraper.base_url == "https://www.estorilsolcasinos.pt"
    assert scraper.sports_url.endswith("/pt/betting/sport/844/matches/date-0")


def test_parse_upcoming_matches_json_fixture_normalizes_1x2_data():
    payload = (FIXTURES / "esc_upcoming_matches.json").read_text(encoding="utf-8")
    scraper = EscScraper()

    matches = scraper.parse_upcoming_matches_json(payload)

    assert len(matches) == 2
    first = matches[0]
    assert isinstance(first, OddsData)
    assert first.match_id == "ESC-1001"
    assert first.site == "esc"
    assert first.site_name == "ESC Online / Estoril Sol Casinos"
    assert first.home_team == "Portugal"
    assert first.away_team == "Brazil"
    assert first.match_date.isoformat() == "2026-06-15T20:00:00+00:00"
    assert first.home_win == pytest.approx(2.35)
    assert first.draw == pytest.approx(3.20)
    assert first.away_win == pytest.approx(2.95)
    assert first.market_name == "Resultado Final"
    assert first.competition == "World Cup"
    assert first.league == "International"
    assert first.status == "ok"
    assert first.error is None
    assert first.source_url == first.url
    assert first.scrape_timestamp == first.last_updated
    assert first.has_1x2() is True
    assert first.url == "https://www.estorilsolcasinos.pt/pt/betting/event/ESC-1001"


def test_parse_upcoming_matches_html_fixture_normalizes_1x2_data():
    html = (FIXTURES / "esc_upcoming_matches.html").read_text(encoding="utf-8")
    scraper = EscScraper()

    matches = scraper.parse_upcoming_matches_html(html)

    assert len(matches) == 2
    first = matches[0]
    assert first.match_id == "ESC-H-2001"
    assert first.home_team == "Benfica"
    assert first.away_team == "Porto"
    assert first.home_win == pytest.approx(1.92)
    assert first.draw == pytest.approx(3.45)
    assert first.away_win == pytest.approx(3.85)
    assert first.market_name == "Resultado Final"
    assert first.competition == "Liga Portugal"
    assert first.league == "Liga Portugal"
    assert first.status == "ok"
    assert first.error is None
    assert first.source_url == first.url
    assert first.scrape_timestamp == first.last_updated
    assert first.url == "https://www.estorilsolcasinos.pt/pt/betting/event/ESC-H-2001"


def test_get_upcoming_matches_uses_explicit_fallback_when_live_scraping_blocked(monkeypatch):
    scraper = EscScraper()

    def blocked_request(_url):
        raise ScraperError("Access forbidden by ESC Online / Estoril Sol Casinos")

    monkeypatch.setattr(scraper, "_make_request", blocked_request)

    matches = scraper.get_upcoming_matches(days_ahead=3)

    assert matches
    assert all(match.site == "esc" for match in matches)
    assert all(match.has_1x2() for match in matches)
    assert all("fallback" in (match.url or "") for match in matches)


def test_get_match_odds_finds_fixture_or_returns_fallback(monkeypatch):
    scraper = EscScraper()
    payload = (FIXTURES / "esc_upcoming_matches.json").read_text(encoding="utf-8")

    class Response:
        text = payload

    monkeypatch.setattr(scraper, "_make_request", lambda _url: Response())

    odds = scraper.get_match_odds("Portugal", "Brazil")

    assert odds is not None
    assert odds.match_id == "ESC-1001"
    assert odds.site == "esc"
    assert odds.has_1x2() is True
