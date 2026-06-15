"""
Placard.pt Scraper - guarded live integration with parser-backed fallback.

Placard's public casino shell is reachable at www.placard.pt, while the sports
betting experience is served through apostas.placard.pt and a JavaScript sports
widget. Direct access to the sports host can return Cloudflare/anti-bot 403s, so
this scraper provides:
1. Parser helpers for representative sports widget/JSON payloads.
2. A conservative live request attempt against the configured sports URL.
3. Deterministic fixture-style mock odds when live scraping is unavailable.

Production live scraping must respect Placard/SRIJ legal and site terms. This
module does not attempt to bypass access controls, sessions, or anti-bot checks.
"""

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin

from ..config import BETTING_SITES
from .base_scraper import BaseScraper, OddsData, ScraperError


class PlacardScraper(BaseScraper):
    """Scraper for Placard.pt football odds."""

    def __init__(self):
        config = BETTING_SITES.get("placard", {})
        super().__init__(
            site_key="placard",
            site_name=config.get("name", "Placard.pt"),
            base_url=config.get("url", "https://apostas.placard.pt"),
            rate_limit_seconds=config.get("rate_limit_seconds", 5),
        )
        self.sports_url = config.get(
            "sports_url", "https://apostas.placard.pt/apostas-desportivas/futebol/"
        )

    def get_match_odds(
        self, home_team: str, away_team: str, match_date: Optional[datetime] = None
    ) -> Optional[OddsData]:
        """Get odds for a specific match, falling back to deterministic data."""
        try:
            matches = self.get_upcoming_matches(days_ahead=7)
            candidate = self._find_match(matches, home_team, away_team, match_date)
            if candidate:
                return candidate
        except ScraperError:
            pass

        return self._create_mock_odds(home_team, away_team, match_date)

    def get_upcoming_matches(self, days_ahead: int = 7) -> List[OddsData]:
        """Get upcoming football odds from Placard, or fixture-style fallback odds."""
        try:
            response = self._make_request(self.sports_url)
            matches = self.parse_upcoming_matches_json(response.text)
            if matches:
                return matches
        except (ScraperError, ValueError, json.JSONDecodeError) as e:
            print(f"⚠️  Placard live scraping unavailable, using fallback: {e}")
        except Exception as e:
            print(f"⚠️  Placard scraping failed, using fallback: {str(e)}")

        return self._get_mock_upcoming_matches(days_ahead)

    def parse_upcoming_matches_json(self, payload: str) -> List[OddsData]:
        """
        Parse representative Placard football JSON into normalized OddsData rows.

        Supported shapes include widget-like payloads with `events[*].participants`
        and `events[*].markets[*].selections`, plus already-flattened payloads with
        `homeTeam`, `awayTeam`, and `odds` fields. Unknown or incomplete events are
        skipped instead of raising so live payload changes degrade safely.
        """
        data = json.loads(payload)
        events = self._extract_events(data)
        matches: List[OddsData] = []

        for event in events:
            if not isinstance(event, dict):
                continue

            home_team, away_team = self._extract_teams(event)
            match_date = self._extract_match_date(event)
            home_win, draw, away_win, market_name = self._extract_1x2_odds(event)

            if not home_team or not away_team or not match_date:
                continue

            competition, league = self._extract_competition(event)
            event_name = self._extract_event_name(event, home_team, away_team)
            source_url = self._extract_event_url(event)

            match_id = self._build_match_id(home_team, away_team, match_date)
            match = OddsData(
                match_id=str(event.get("id") or event.get("eventId") or match_id),
                home_team=home_team,
                away_team=away_team,
                match_date=match_date,
                site="placard",
                site_name=self.site_name,
                home_win=home_win,
                draw=draw,
                away_win=away_win,
                url=source_url,
                source_url=source_url,
                market_name=market_name,
                league=league,
                competition=competition,
                status=str(event.get("status") or event.get("state") or "upcoming"),
                error=None,
            )
            if event_name and not match.competition:
                match.competition = event_name
            if match.has_1x2():
                matches.append(match)

        return matches

    def _extract_events(self, data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if not isinstance(data, dict):
            return []

        for key in ("events", "matches", "items", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                nested = self._extract_events(value)
                if nested:
                    return nested
        return []

    def _extract_teams(
        self, event: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        home = event.get("homeTeam") or event.get("home_team")
        away = event.get("awayTeam") or event.get("away_team")
        if home and away:
            return str(home), str(away)

        participants = event.get("participants") or event.get("contestants") or []
        if isinstance(participants, dict):
            home = participants.get("home") or participants.get("HOME")
            away = participants.get("away") or participants.get("AWAY")
            if home and away:
                return self._participant_name(home), self._participant_name(away)
        elif isinstance(participants, list):
            home = self._find_participant(participants, ("HOME", "home", "1"))
            away = self._find_participant(participants, ("AWAY", "away", "2"))
            if home and away:
                return home, away
            if len(participants) >= 2:
                return self._participant_name(participants[0]), self._participant_name(
                    participants[1]
                )

        name = event.get("name") or event.get("eventName") or event.get("title")
        if isinstance(name, str):
            for separator in (" v ", " vs ", " - ", " – "):
                if separator in name:
                    home_part, away_part = name.split(separator, 1)
                    return home_part.strip(), away_part.strip()

        return None, None

    def _participant_name(self, participant: Any) -> Optional[str]:
        if isinstance(participant, dict):
            value = (
                participant.get("name")
                or participant.get("label")
                or participant.get("title")
            )
            return str(value) if value else None
        return str(participant) if participant else None

    def _find_participant(
        self, participants: Iterable[Dict[str, Any]], accepted_types: Tuple[str, ...]
    ) -> Optional[str]:
        accepted = {value.lower() for value in accepted_types}
        for participant in participants:
            if not isinstance(participant, dict):
                continue
            participant_type = str(
                participant.get("type")
                or participant.get("side")
                or participant.get("position")
                or ""
            ).lower()
            if participant_type in accepted:
                return self._participant_name(participant)
        return None

    def _extract_match_date(self, event: Dict[str, Any]) -> Optional[datetime]:
        raw_value = (
            event.get("startTime")
            or event.get("starts_at")
            or event.get("kickoff")
            or event.get("date")
            or event.get("matchDate")
        )
        if not raw_value:
            return None
        if isinstance(raw_value, (int, float)):
            return datetime.fromtimestamp(
                raw_value / 1000 if raw_value > 10_000_000_000 else raw_value,
                tz=timezone.utc,
            )
        if isinstance(raw_value, str):
            value = raw_value.replace("Z", "+00:00")
            try:
                parsed = datetime.fromisoformat(value)
            except ValueError:
                return None
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        return None

    def _extract_1x2_odds(
        self, event: Dict[str, Any]
    ) -> Tuple[Optional[float], Optional[float], Optional[float], Optional[str]]:
        odds = event.get("odds")
        if isinstance(odds, dict):
            home = self._to_float(
                odds.get("home") or odds.get("home_win") or odds.get("1")
            )
            draw = self._to_float(odds.get("draw") or odds.get("x") or odds.get("X"))
            away = self._to_float(
                odds.get("away") or odds.get("away_win") or odds.get("2")
            )
            if home and draw and away:
                return (
                    home,
                    draw,
                    away,
                    str(event.get("marketName") or event.get("market") or "1X2"),
                )

        for market in event.get("markets", []) or []:
            if not isinstance(market, dict):
                continue
            market_name = str(
                market.get("name") or market.get("marketName") or ""
            ).strip()
            market_name_lower = market_name.lower()
            market_type = str(
                market.get("marketType") or market.get("type") or ""
            ).lower()
            if not (
                "1x2" in market_type
                or "resultado" in market_name_lower
                or "match winner" in market_name_lower
            ):
                continue
            selections = market.get("selections") or market.get("outcomes") or []
            home, draw, away = self._extract_selection_odds(selections)
            if home and draw and away:
                return home, draw, away, market_name or market_type or "1X2"

        return None, None, None, None

    def _extract_selection_odds(
        self, selections: Iterable[Any]
    ) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        home = draw = away = None
        for selection in selections:
            if not isinstance(selection, dict):
                continue
            selection_type = str(
                selection.get("type")
                or selection.get("outcomeType")
                or selection.get("id")
                or ""
            ).lower()
            name = str(selection.get("name") or selection.get("label") or "").lower()
            price = self._to_float(
                selection.get("odds")
                or selection.get("price")
                or selection.get("decimalOdds")
                or selection.get("value")
            )
            if price is None:
                continue
            if selection_type in {"home", "1"}:
                home = price
            elif selection_type in {"draw", "x"} or name in {"empate", "draw", "x"}:
                draw = price
            elif selection_type in {"away", "2"}:
                away = price
        return home, draw, away

    def _extract_competition(
        self, event: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        competition = event.get("competition")
        if isinstance(competition, dict):
            competition_name = competition.get("name")
        else:
            competition_name = competition

        league = event.get("league")
        if isinstance(league, dict):
            league_name = league.get("name")
        else:
            league_name = league

        if not league_name and not competition_name:
            tournament = event.get("tournament")
            if isinstance(tournament, dict):
                league_name = tournament.get("name")
            elif tournament:
                league_name = tournament

        return (
            str(competition_name) if competition_name else None,
            str(league_name) if league_name else None,
        )

    def _extract_event_name(
        self, event: Dict[str, Any], home_team: str, away_team: str
    ) -> str:
        return str(
            event.get("name")
            or event.get("eventName")
            or event.get("title")
            or f"{home_team} vs {away_team}"
        )

    def _build_match_id(
        self, home_team: str, away_team: str, match_date: datetime
    ) -> str:
        safe_home = self.normalize_team_name(home_team).replace(" ", "-")
        safe_away = self.normalize_team_name(away_team).replace(" ", "-")
        return f"placard-{safe_home}-{safe_away}-{match_date.strftime('%Y%m%d%H%M')}"

    def _to_float(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        try:
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return None

    def _extract_event_url(self, event: Dict[str, Any]) -> str:
        source = event.get("sourceUrl") or event.get("url") or event.get("path") or ""
        if not source:
            return self.sports_url
        return urljoin(self.base_url, str(source))

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
        """Create deterministic fallback odds for development/testing only."""
        if match_date is None:
            match_date = datetime.now(timezone.utc) + timedelta(days=3)

        base_home = 1.58 + (len(home_team) % 8) * 0.10
        base_away = 1.78 + (len(away_team) % 8) * 0.10

        return OddsData(
            match_id=f"placard_{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}",
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            site="placard",
            site_name=self.site_name,
            home_win=round(base_home, 2),
            draw=3.05,
            away_win=round(base_away, 2),
            over_2_5=1.72,
            under_2_5=1.86,
            btts_yes=1.63,
            btts_no=1.93,
            url=f"{self.base_url}/apostas/futebol/{home_team}-{away_team}",
        )

    def _get_mock_upcoming_matches(self, days_ahead: int) -> List[OddsData]:
        teams = [
            ("FC Porto", "SL Benfica"),
            ("Sporting CP", "SC Braga"),
            ("Portugal", "Brazil"),
            ("Spain", "Germany"),
            ("France", "Argentina"),
            ("England", "Italy"),
            ("Netherlands", "Belgium"),
            ("Croatia", "Uruguay"),
        ]
        today = datetime.now(timezone.utc)
        return [
            self._create_mock_odds(home, away, today + timedelta(days=i + 1))
            for i, (home, away) in enumerate(
                teams[: max(1, min(days_ahead, len(teams)))]
            )
        ]
