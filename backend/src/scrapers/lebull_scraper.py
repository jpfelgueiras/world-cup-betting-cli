"""
LeBull.pt Scraper - PARSER-BACKED FALLBACK IMPLEMENTATION

This module provides LeBull Portugal support in the same safe mode as the existing
bookmaker scrapers:
1. JSON parser helpers for representative LeBull sportsbook payload shapes.
2. Conservative fallback mock data when live scraping is unavailable.

Live production scraping is intentionally not guaranteed here because LeBull.pt may
serve dynamic JavaScript, require regional/session state, and enforce anti-bot
controls. Enable production scraping only after legal/TOS review and endpoint
verification.
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urljoin

from ..config import BETTING_SITES
from .base_scraper import BaseScraper, OddsData, ScraperError


class LeBullScraper(BaseScraper):
    """Scraper for LeBull.pt with parser helpers and safe fallback semantics."""

    def __init__(self):
        config = BETTING_SITES.get("lebull", {})
        super().__init__(
            site_key="lebull",
            site_name=config.get("name", "LeBull.pt"),
            base_url=config.get("url", "https://www.lebull.pt"),
            rate_limit_seconds=config.get("rate_limit_seconds", 5),
        )
        self.sports_url = config.get(
            "sports_url", "https://www.lebull.pt/desporto/futebol"
        )

    def get_match_odds(
        self, home_team: str, away_team: str, match_date: Optional[datetime] = None
    ) -> Optional[OddsData]:
        """Get odds for a specific match, falling back to deterministic mock data."""
        try:
            matches = self.get_upcoming_matches(days_ahead=7)
            candidate = self._find_match(matches, home_team, away_team, match_date)
            if candidate:
                return candidate
        except ScraperError:
            pass

        return self._create_mock_odds(home_team, away_team, match_date)

    def get_upcoming_matches(self, days_ahead: int = 7) -> List[OddsData]:
        """Get upcoming LeBull matches or deterministic fallback matches."""
        try:
            response = self._make_request(self.sports_url)
            matches = self.parse_upcoming_matches_json(response.text)
            if matches:
                return matches
        except (ScraperError, ValueError, json.JSONDecodeError) as e:
            print(f"⚠️  LeBull scraping not available, using mock: {e}")
        except Exception as e:
            print(f"⚠️  LeBull scraping failed, using mock: {str(e)}")

        return self._get_mock_upcoming_matches(days_ahead)

    def parse_upcoming_matches_json(self, payload: str) -> List[OddsData]:
        """
        Parse representative LeBull sportsbook JSON into normalized OddsData rows.

        Supports event lists nested under keys commonly seen in sportsbook state
        payloads (events, fixtures, items, widgets) and extracts 1X2, O/U 2.5,
        and BTTS markets when present.
        """
        data = json.loads(payload)
        matches: List[OddsData] = []

        for event in self._iter_event_nodes(data):
            odds = self._parse_event(event)
            if odds and odds.has_1x2():
                matches.append(odds)

        # Deduplicate events reachable through multiple container keys.
        unique: Dict[str, OddsData] = {}
        for match in matches:
            unique.setdefault(match.match_id, match)
        return list(unique.values())

    def _iter_event_nodes(self, node: Any) -> Iterable[Dict[str, Any]]:
        """Yield dicts that look like LeBull event nodes from nested JSON."""
        if isinstance(node, list):
            for item in node:
                yield from self._iter_event_nodes(item)
            return

        if not isinstance(node, dict):
            return

        if self._looks_like_event(node):
            yield node

        for key in ("events", "fixtures", "items", "children", "widgets", "data"):
            child = node.get(key)
            if child is not None:
                yield from self._iter_event_nodes(child)

    @staticmethod
    def _looks_like_event(node: Dict[str, Any]) -> bool:
        has_date = any(
            key in node
            for key in ("startDate", "startTime", "starts_at", "date", "kickoff")
        )
        has_market = any(
            key in node for key in ("markets", "optionMarkets", "betOffers", "odds")
        )
        has_teams = any(
            key in node
            for key in (
                "participants",
                "competitors",
                "contestants",
                "name",
                "homeTeam",
                "awayTeam",
            )
        )
        return has_date and has_market and has_teams

    def _parse_event(self, event: Dict[str, Any]) -> Optional[OddsData]:
        home_team, away_team = self._extract_teams(event)
        if not home_team or not away_team:
            return None

        match_date = self._parse_datetime(
            event.get("startDate")
            or event.get("startTime")
            or event.get("starts_at")
            or event.get("date")
            or event.get("kickoff")
        )
        if match_date is None:
            return None

        markets = (
            event.get("markets")
            or event.get("optionMarkets")
            or event.get("betOffers")
            or self._markets_from_odds_map(event.get("odds"))
            or []
        )
        home_win, draw, away_win = self._extract_1x2(markets, home_team, away_team)
        over_2_5, under_2_5 = self._extract_over_under_25(markets)
        btts_yes, btts_no = self._extract_btts(markets)

        match_id = str(
            event.get("id")
            or event.get("eventId")
            or event.get("fixtureId")
            or f"lebull_{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}"
        )
        href = event.get("url") or event.get("path") or event.get("eventUrl")

        source_url = urljoin(self.base_url, href) if href else self.sports_url

        return OddsData(
            match_id=match_id,
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            site="lebull",
            site_name=self.site_name,
            home_win=home_win,
            draw=draw,
            away_win=away_win,
            over_2_5=over_2_5,
            under_2_5=under_2_5,
            btts_yes=btts_yes,
            btts_no=btts_no,
            url=source_url,
            market_name="1x2",
            league=self._nested_name(event.get("league")) or event.get("league"),
            competition=self._nested_name(event.get("competition"))
            or event.get("competition"),
            status=event.get("status") or "ok",
            error=None,
            source_url=source_url,
        )

    def _extract_teams(
        self, event: Dict[str, Any]
    ) -> tuple[Optional[str], Optional[str]]:
        participants = event.get("participants") or event.get("competitors")
        if isinstance(participants, list) and len(participants) >= 2:
            home = (
                self._participant_by_role(participants, {"home", "1"})
                or participants[0]
            )
            away = (
                self._participant_by_role(participants, {"away", "2"})
                or participants[1]
            )
            return self._name_from(home), self._name_from(away)

        contestants = event.get("contestants")
        if isinstance(contestants, dict):
            return self._name_from(contestants.get("home")), self._name_from(
                contestants.get("away")
            )

        home_team = self._name_from(event.get("homeTeam"))
        away_team = self._name_from(event.get("awayTeam"))
        if home_team and away_team:
            return home_team, away_team

        name = event.get("name") or event.get("eventName") or ""
        for separator in (" - ", " vs ", " v "):
            if separator in name:
                home, away = name.split(separator, 1)
                return home.strip(), away.strip()
        return None, None

    @staticmethod
    def _participant_by_role(participants: List[Any], roles: set[str]) -> Optional[Any]:
        for participant in participants:
            if not isinstance(participant, dict):
                continue
            role = str(
                participant.get("type")
                or participant.get("role")
                or participant.get("position")
                or ""
            ).lower()
            if role in roles:
                return participant
        return None

    @staticmethod
    def _name_from(value: Any) -> Optional[str]:
        if isinstance(value, str):
            return value.strip() or None
        if isinstance(value, dict):
            for key in ("name", "label", "participantName"):
                if value.get(key):
                    return str(value[key]).strip()
        return None

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        if not value:
            return None
        text = str(value).replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None

    def _extract_1x2(
        self, markets: Any, home_team: str, away_team: str
    ) -> tuple[Optional[float], Optional[float], Optional[float]]:
        for market in self._market_list(markets):
            market_name = self._market_name(market)
            if not self._is_1x2_market(market_name):
                continue
            selections = self._selection_list(market)
            odds_by_name = {
                self._selection_name(s): self._selection_odds(s) for s in selections
            }
            return (
                self._first_named_odds(odds_by_name, ["1", home_team]),
                self._first_named_odds(odds_by_name, ["x", "draw", "empate"]),
                self._first_named_odds(odds_by_name, ["2", away_team]),
            )
        return None, None, None

    def _extract_over_under_25(
        self, markets: Any
    ) -> tuple[Optional[float], Optional[float]]:
        for market in self._market_list(markets):
            market_name = self._market_name(market)
            if "2.5" not in market_name and "2,5" not in market_name:
                continue
            if not any(
                token in market_name
                for token in ("over", "under", "mais", "menos", "total")
            ):
                continue
            odds_by_name = {
                self._selection_name(s): self._selection_odds(s)
                for s in self._selection_list(market)
            }
            return (
                self._first_named_odds(odds_by_name, ["over", "mais"]),
                self._first_named_odds(odds_by_name, ["under", "menos"]),
            )
        return None, None

    def _extract_btts(self, markets: Any) -> tuple[Optional[float], Optional[float]]:
        for market in self._market_list(markets):
            market_name = self._market_name(market)
            if not any(
                token in market_name
                for token in ("both", "ambas", "btts", "ambos", "marcam")
            ):
                continue
            odds_by_name = {
                self._selection_name(s): self._selection_odds(s)
                for s in self._selection_list(market)
            }
            return (
                self._first_named_odds(odds_by_name, ["yes", "sim"]),
                self._first_named_odds(odds_by_name, ["no", "não", "nao"]),
            )
        return None, None

    @staticmethod
    def _market_list(markets: Any) -> List[Dict[str, Any]]:
        if isinstance(markets, dict):
            return [m for m in markets.values() if isinstance(m, dict)]
        if isinstance(markets, list):
            return [m for m in markets if isinstance(m, dict)]
        return []

    @staticmethod
    def _market_name(market: Dict[str, Any]) -> str:
        return str(
            market.get("name")
            or market.get("marketName")
            or market.get("templateCategory")
            or market.get("type")
            or ""
        ).lower()

    @staticmethod
    def _selection_list(market: Dict[str, Any]) -> List[Dict[str, Any]]:
        selections = (
            market.get("selections")
            or market.get("outcomes")
            or market.get("options")
            or []
        )
        if isinstance(selections, dict):
            return [s for s in selections.values() if isinstance(s, dict)]
        if isinstance(selections, list):
            return [s for s in selections if isinstance(s, dict)]
        return []

    @staticmethod
    def _selection_name(selection: Dict[str, Any]) -> str:
        return str(
            selection.get("name")
            or selection.get("label")
            or selection.get("outcomeName")
            or selection.get("type")
            or ""
        ).lower()

    def _selection_odds(self, selection: Dict[str, Any]) -> Optional[float]:
        raw = (
            selection.get("odds") or selection.get("price") or selection.get("decimal")
        )
        if isinstance(raw, dict):
            raw = raw.get("decimal") or raw.get("odds") or raw.get("value")
        return self._parse_float(raw)

    def _markets_from_odds_map(self, odds: Any) -> List[Dict[str, Any]]:
        if not isinstance(odds, dict):
            return []

        markets: List[Dict[str, Any]] = []

        one_x_two = odds.get("1X2") or odds.get("1x2")
        if isinstance(one_x_two, dict):
            markets.append(
                {
                    "name": "Resultado Final",
                    "selections": [
                        {"name": "1", "odds": one_x_two.get("home")},
                        {"name": "X", "odds": one_x_two.get("draw")},
                        {"name": "2", "odds": one_x_two.get("away")},
                    ],
                }
            )

        over_under = odds.get("OU25") or odds.get("ou25")
        if isinstance(over_under, dict):
            markets.append(
                {
                    "name": "Total Golos 2.5",
                    "selections": [
                        {"name": "Over", "odds": over_under.get("over")},
                        {"name": "Under", "odds": over_under.get("under")},
                    ],
                }
            )

        btts = odds.get("BTTS") or odds.get("btts")
        if isinstance(btts, dict):
            markets.append(
                {
                    "name": "Ambas Equipas Marcam",
                    "selections": [
                        {"name": "Yes", "odds": btts.get("yes")},
                        {"name": "No", "odds": btts.get("no")},
                    ],
                }
            )

        return markets

    @staticmethod
    def _parse_float(value: Any) -> Optional[float]:
        if value in (None, ""):
            return None
        try:
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _nested_name(value: Any) -> Optional[str]:
        if isinstance(value, dict):
            nested = value.get("name") or value.get("label")
            if nested:
                return str(nested)
        if isinstance(value, str):
            return value
        return None

    @staticmethod
    def _is_1x2_market(market_name: str) -> bool:
        return any(
            token in market_name
            for token in (
                "1x2",
                "match_result",
                "match result",
                "resultado",
                "resultado final",
                "resultado do jogo",
            )
        )

    @staticmethod
    def _first_named_odds(
        odds_by_name: Dict[str, Optional[float]], names: List[str]
    ) -> Optional[float]:
        normalized_names = [name.lower() for name in names]
        for wanted in normalized_names:
            for actual, odds in odds_by_name.items():
                if odds is None:
                    continue
                if actual == wanted or wanted in actual:
                    return odds
        return None

    def _find_match(
        self,
        matches: List[OddsData],
        home_team: str,
        away_team: str,
        match_date: Optional[datetime],
    ) -> Optional[OddsData]:
        """Find matching fixture in list of odds."""
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
        """Create deterministic fallback odds data; not real LeBull.pt odds."""
        if match_date is None:
            match_date = datetime.now() + timedelta(days=3)

        base_home = 1.57 + (len(home_team) % 8) * 0.10
        base_away = 1.77 + (len(away_team) % 8) * 0.10
        base_draw = 2.88

        return OddsData(
            match_id=f"lebull_{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}",
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            site="lebull",
            site_name=self.site_name,
            home_win=round(base_home, 2),
            draw=round(base_draw, 2),
            away_win=round(base_away, 2),
            over_2_5=1.72,
            under_2_5=1.82,
            btts_yes=1.62,
            btts_no=1.92,
            url=f"{self.base_url}/desporto/futebol/{home_team}-{away_team}",
        )

    def _get_mock_upcoming_matches(self, days_ahead: int) -> List[OddsData]:
        """Generate deterministic fallback upcoming matches."""
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
        today = datetime.now()
        return [
            self._create_mock_odds(home, away, today + timedelta(days=i + 1))
            for i, (home, away) in enumerate(teams)
        ]
