"""
CasinoPortugal.pt scraper - NSoft offer API parser with safe fallback.

Casino Portugal serves its sportsbook through NSoft's sports web application.
The public page at https://www.casinoportugal.pt/desporto bootstraps tenant
10ca03ad-9dc4-4320-bbc2-c93a42194d08 and reads football offers from
https://aio-offer-distribution.de-2.nsoft.cloud. This scraper uses that public
JSON shape when reachable and falls back to deterministic tagged rows when live
scraping is blocked or the upstream schema changes.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from ..config import BETTING_SITES
from .base_scraper import BaseScraper, OddsData, ScraperError


class CasinoPortugalScraper(BaseScraper):
    """Scraper/parser integration for CasinoPortugal.pt football odds."""

    TENANT_UUID = "10ca03ad-9dc4-4320-bbc2-c93a42194d08"
    OFFER_API_URL = "https://aio-offer-distribution.de-2.nsoft.cloud"
    LANGUAGE = "pt"
    GAME_IDS = "1,2"

    def __init__(self):
        config = BETTING_SITES.get("casinoportugal", {})
        super().__init__(
            site_key="casinoportugal",
            site_name=config.get("name", "Casino Portugal"),
            base_url=config.get("url", "https://www.casinoportugal.pt"),
            rate_limit_seconds=config.get("rate_limit_seconds", 5),
        )
        self.sports_url = config.get(
            "sports_url", "https://www.casinoportugal.pt/desporto"
        )
        self.offer_api_url = config.get("offer_api_url", self.OFFER_API_URL)
        self.tenant_uuid = config.get("tenant_uuid", self.TENANT_UUID)

    def get_match_odds(
        self, home_team: str, away_team: str, match_date: Optional[datetime] = None
    ) -> Optional[OddsData]:
        """Get odds for a specific match, using fallback semantics if needed."""
        try:
            matches = self.get_upcoming_matches(days_ahead=7)
            candidate = self._find_match(matches, home_team, away_team, match_date)
            if candidate:
                return candidate
        except ScraperError:
            pass

        return self._create_mock_odds(home_team, away_team, match_date)

    def get_upcoming_matches(self, days_ahead: int = 7) -> List[OddsData]:
        """Get upcoming Casino Portugal football odds or deterministic fallback rows."""
        try:
            response = self._make_request(self._offer_url(days_ahead))
            matches = self.parse_upcoming_matches_json(response.text)
            if matches:
                return matches
        except (ScraperError, ValueError, json.JSONDecodeError) as e:
            print(f"⚠️  Casino Portugal scraping unavailable, using mock: {e}")
        except Exception as e:
            print(f"⚠️  Casino Portugal scraping failed, using mock: {str(e)}")

        return self._get_mock_upcoming_matches(days_ahead)

    def parse_upcoming_matches_json(self, payload: str) -> List[OddsData]:
        """Parse NSoft offer-distribution JSON into normalized OddsData rows."""
        data = json.loads(payload)
        markets_meta = {market.get("id"): market for market in data.get("markets", [])}
        outcome_meta: Dict[int, Dict[str, Any]] = {}
        for market in markets_meta.values():
            for outcome in market.get("outcomes", []):
                outcome_meta[outcome.get("id")] = outcome

        categories = {
            category.get("id"): category for category in data.get("categories", [])
        }
        tournaments = {
            tournament.get("id"): tournament
            for tournament in data.get("tournaments", [])
        }

        matches: List[OddsData] = []
        for event in data.get("events", []):
            competitors = sorted(
                event.get("competitors", []), key=lambda item: item.get("ordinal", 0)
            )
            if len(competitors) < 2:
                continue

            try:
                match_date = self._parse_datetime(event["startsAt"])
            except (KeyError, ValueError, TypeError):
                continue

            tournament = tournaments.get(event.get("tournamentId"), {})
            category = categories.get(tournament.get("categoryId"), {})
            parsed_markets = self._parse_event_markets(
                event, markets_meta, outcome_meta
            )
            one_x_two = parsed_markets.get("1x2", {})
            if not {"home", "draw", "away"}.issubset(one_x_two):
                continue

            event_id = event.get("id", "")
            source_url = (
                f"{self.sports_url}/d_all/ctg_{category.get('id', 'all')}/e_{event_id}"
            )
            matches.append(
                OddsData(
                    match_id=f"casinoportugal_{event_id}",
                    home_team=competitors[0].get("teamName", ""),
                    away_team=competitors[1].get("teamName", ""),
                    match_date=match_date,
                    site="casinoportugal",
                    site_name=self.site_name,
                    home_win=one_x_two.get("home"),
                    draw=one_x_two.get("draw"),
                    away_win=one_x_two.get("away"),
                    over_2_5=parsed_markets.get("ou25", {}).get("over"),
                    under_2_5=parsed_markets.get("ou25", {}).get("under"),
                    btts_yes=parsed_markets.get("btts", {}).get("yes"),
                    btts_no=parsed_markets.get("btts", {}).get("no"),
                    url=source_url,
                    market_name=markets_meta.get(1708, {}).get("name", "1x2"),
                    league=tournament.get("name"),
                    competition=category.get("name"),
                    status="ok",
                    error=None,
                    source_url=source_url,
                )
            )

        return [match for match in matches if match.has_1x2()]

    def _parse_event_markets(
        self,
        event: Dict[str, Any],
        markets_meta: Dict[int, Dict[str, Any]],
        outcome_meta: Dict[int, Dict[str, Any]],
    ) -> Dict[str, Dict[str, float]]:
        parsed: Dict[str, Dict[str, float]] = {}
        for market in event.get("markets", []):
            market_id = market.get("marketId")
            market_meta = markets_meta.get(market_id, {})
            market_name = (market_meta.get("name") or "").lower()
            outcomes = market.get("outcomes", [])

            if market_id == 1708 or market_name == "1x2":
                parsed["1x2"] = self._parse_1x2(outcomes, outcome_meta)
            elif market_id == 1682 or "total de golos" in market_name:
                parsed["ou25"] = self._parse_total_goals_25(outcomes, outcome_meta)
            elif market_id == 1411 or "duas equipas marcam" in market_name:
                parsed["btts"] = self._parse_btts(outcomes, outcome_meta)
        return parsed

    def _parse_1x2(
        self, outcomes: List[Dict[str, Any]], outcome_meta: Dict[int, Dict[str, Any]]
    ) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for outcome in outcomes:
            name = (
                outcome_meta.get(outcome.get("outcomeId"), {}).get("name") or ""
            ).lower()
            odd = self._decimal_odds(outcome.get("odds"))
            if odd is None:
                continue
            if name in {"casa", "home"}:
                result["home"] = odd
            elif name in {"empate", "x", "draw"}:
                result["draw"] = odd
            elif name in {"fora", "away"}:
                result["away"] = odd
        return result

    def _parse_total_goals_25(
        self, outcomes: List[Dict[str, Any]], outcome_meta: Dict[int, Dict[str, Any]]
    ) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for outcome in outcomes:
            if not any(
                str(specifier.get("value")) == "2.5"
                for specifier in outcome.get("specifiers", [])
            ):
                continue
            name = (
                outcome_meta.get(outcome.get("outcomeId"), {}).get("name") or ""
            ).lower()
            odd = self._decimal_odds(outcome.get("odds"))
            if odd is None:
                continue
            if name in {"acima", "over"}:
                result["over"] = odd
            elif name in {"abaixo", "under"}:
                result["under"] = odd
        return result

    def _parse_btts(
        self, outcomes: List[Dict[str, Any]], outcome_meta: Dict[int, Dict[str, Any]]
    ) -> Dict[str, float]:
        result: Dict[str, float] = {}
        for outcome in outcomes:
            meta = outcome_meta.get(outcome.get("outcomeId"), {})
            name = (meta.get("info") or meta.get("name") or "").lower()
            odd = self._decimal_odds(outcome.get("odds"))
            if odd is None:
                continue
            if name in {"sim", "yes"}:
                result["yes"] = odd
            elif name in {"não", "nao", "no"}:
                result["no"] = odd
        return result

    def _offer_url(self, days_ahead: int) -> str:
        starts_at_to = (
            datetime.now(timezone.utc) + timedelta(days=days_ahead)
        ).strftime("%Y-%m-%dT%H:%M:%S")
        return (
            f"{self.offer_api_url}/tenants/{self.tenant_uuid}/games/{self.GAME_IDS}"
            f"/languages/{self.LANGUAGE}/offer/cursors"
            "?expectedNumberOfEvents=20&numberOfMarketsPerSport=20"
            "&marketTypes=1&eventTypes=1"
            f"&startsAtTo={starts_at_to}"
        )

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

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _decimal_odds(value: Any) -> Optional[float]:
        if value is None:
            return None
        return round(float(value) / 10000, 2)

    def _create_mock_odds(
        self, home_team: str, away_team: str, match_date: Optional[datetime] = None
    ) -> OddsData:
        """Create Casino Portugal-tagged fallback odds when live scraping is unsafe."""
        if match_date is None:
            match_date = datetime.now() + timedelta(days=3)

        base_home = 1.58 + (len(home_team) % 8) * 0.10
        base_away = 1.80 + (len(away_team) % 8) * 0.10
        base_draw = 3.10
        source_url = f"{self.sports_url}/{home_team}-{away_team}"

        return OddsData(
            match_id=f"casinoportugal_{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}",
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            site="casinoportugal",
            site_name=self.site_name,
            home_win=round(base_home, 2),
            draw=round(base_draw, 2),
            away_win=round(base_away, 2),
            over_2_5=1.83,
            under_2_5=1.93,
            btts_yes=1.76,
            btts_no=2.00,
            url=source_url,
            market_name="1x2",
            status="fallback",
            error="Live Casino Portugal scrape unavailable; deterministic fallback odds used.",
            source_url=source_url,
        )

    def _get_mock_upcoming_matches(self, days_ahead: int) -> List[OddsData]:
        """Generate Casino Portugal-tagged fallback fixtures for scans/tests."""
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
            matches.append(
                self._create_mock_odds(home, away, today + timedelta(days=i + 1))
            )
        return matches
