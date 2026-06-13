"""
GoldenPark.pt Scraper - parser-backed fallback implementation.

This module provides GoldenPark Portugal sportsbook coverage using the same
safe semantics as the existing Portuguese bookmaker integrations:
1. JSON parser helpers for representative sportsbook API payloads.
2. Best-effort HTTP retrieval from the configured football sports URL.
3. Deterministic mock fallback data when live scraping is blocked, unavailable,
   JavaScript-rendered, or otherwise unsafe for production automation.

Live endpoint details should be re-verified against GoldenPark.pt before using
this scraper as an authoritative production odds source.
"""

import json
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urljoin

from ..config import BETTING_SITES
from .base_scraper import BaseScraper, OddsData, ScraperError


class GoldenParkScraper(BaseScraper):
    """Scraper/parser integration for GoldenPark.pt football odds."""

    def __init__(self):
        config = BETTING_SITES.get("goldenpark", {})
        super().__init__(
            site_key="goldenpark",
            site_name=config.get("name", "GoldenPark.pt"),
            base_url=config.get("url", "https://www.goldenpark.pt"),
            rate_limit_seconds=config.get("rate_limit_seconds", 5),
        )
        self.sports_url = config.get(
            "sports_url",
            "https://www.goldenpark.pt/pt/apostas-desportivas/futebol/",
        )

    def get_match_odds(
        self, home_team: str, away_team: str, match_date: Optional[datetime] = None
    ) -> Optional[OddsData]:
        """Get odds for a specific match, falling back to tagged mock odds."""
        try:
            matches = self.get_upcoming_matches(days_ahead=7)
            candidate = self._find_match(matches, home_team, away_team, match_date)
            if candidate:
                return candidate
        except ScraperError:
            pass

        return self._create_mock_odds(home_team, away_team, match_date)

    def get_upcoming_matches(self, days_ahead: int = 7) -> List[OddsData]:
        """Get upcoming GoldenPark football odds or deterministic fallback rows."""
        try:
            response = self._make_request(self.sports_url)
            matches = self.parse_upcoming_matches_json(response.text)
            if matches:
                return matches
        except (ScraperError, ValueError, json.JSONDecodeError) as e:
            print(f"⚠️  GoldenPark scraping unavailable, using mock: {e}")
        except Exception as e:
            print(f"⚠️  GoldenPark scraping failed, using mock: {str(e)}")

        return self._get_mock_upcoming_matches(days_ahead)

    def parse_upcoming_matches_json(self, payload: str) -> List[OddsData]:
        """
        Parse a GoldenPark-like football odds JSON payload into OddsData rows.

        Supported fixture shape mirrors the current parser-helper convention:
        {"events": [{"id", "starts_at", "contestants", "markets", "url"}]}.
        Only rows with complete 1X2 odds are returned.
        """
        data = json.loads(payload)
        events = data.get("events", [])
        matches: List[OddsData] = []

        for event in events:
            contestants = event.get("contestants", {})
            markets = event.get("markets", {})
            one_x_two = markets.get("1x2", {})
            ou25 = markets.get("ou25", {})
            btts = markets.get("btts", {})

            try:
                match_date = datetime.fromisoformat(event["starts_at"])
            except (KeyError, ValueError, TypeError):
                continue

            if not contestants.get("home") or not contestants.get("away"):
                continue

            matches.append(
                OddsData(
                    match_id=event.get("id", ""),
                    home_team=contestants["home"],
                    away_team=contestants["away"],
                    match_date=match_date,
                    site="goldenpark",
                    site_name=self.site_name,
                    home_win=one_x_two.get("home"),
                    draw=one_x_two.get("draw"),
                    away_win=one_x_two.get("away"),
                    over_2_5=ou25.get("over"),
                    under_2_5=ou25.get("under"),
                    btts_yes=btts.get("yes"),
                    btts_no=btts.get("no"),
                    url=urljoin(self.base_url, event.get("url", "")),
                    market_name="1x2",
                    league=event.get("league"),
                    competition=event.get("competition"),
                    status="ok",
                    error=None,
                )
            )

        return [match for match in matches if match.has_1x2()]

    def _find_match(
        self,
        matches: List[OddsData],
        home_team: str,
        away_team: str,
        match_date: Optional[datetime],
    ) -> Optional[OddsData]:
        home_norm = self.normalize_team_name(home_team)
        away_norm = self.normalize_team_name(away_team)
        for match in matches:
            if (
                self.normalize_team_name(match.home_team) == home_norm
                and self.normalize_team_name(match.away_team) == away_norm
            ):
                if match_date is None or match.match_date.date() == match_date.date():
                    return match
        return None

    def _create_mock_odds(
        self, home_team: str, away_team: str, match_date: Optional[datetime] = None
    ) -> OddsData:
        """Create GoldenPark-tagged fallback odds when live scraping is unsafe."""
        if match_date is None:
            match_date = datetime.now() + timedelta(days=3)

        base_home = 1.60 + (len(home_team) % 8) * 0.10
        base_away = 1.82 + (len(away_team) % 8) * 0.10
        base_draw = 3.05

        return OddsData(
            match_id=f"goldenpark_{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}",
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            site="goldenpark",
            site_name=self.site_name,
            home_win=round(base_home, 2),
            draw=round(base_draw, 2),
            away_win=round(base_away, 2),
            over_2_5=1.82,
            under_2_5=1.92,
            btts_yes=1.74,
            btts_no=2.02,
            url=f"{self.base_url}/pt/apostas-desportivas/futebol/{home_team}-{away_team}",
            market_name="1x2",
            league="International",
            competition="GoldenPark fallback",
            status="fallback",
            error="Live GoldenPark.pt scrape unavailable; deterministic fallback odds used.",
        )

    def _get_mock_upcoming_matches(self, days_ahead: int) -> List[OddsData]:
        """Generate GoldenPark-tagged fallback fixtures for scans/tests."""
        teams = [
            ("Portugal", "Brazil"),
            ("Spain", "Germany"),
            ("France", "Argentina"),
            ("England", "Italy"),
            ("Netherlands", "Belgium"),
            ("Croatia", "Uruguay"),
            ("Morocco", "Japan"),
            ("USA", "Mexico"),
        ]
        matches = []
        today = datetime.now()
        for i, (home, away) in enumerate(teams[: max(days_ahead, 0)]):
            match_date = today + timedelta(days=i + 1)
            matches.append(self._create_mock_odds(home, away, match_date))
        return matches
