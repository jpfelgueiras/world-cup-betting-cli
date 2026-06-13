"""
ESCOnline / Estoril Sol Casinos scraper integration.

The SRIJ-listed sports-betting domain is www.estorilsolcasinos.pt. Live
pages are protected and may be JavaScript-rendered, so this scraper keeps
live HTTP best-effort and falls back to explicit fixture-shaped demo data
when access is blocked. Parser helpers support representative ESC JSON and
HTML shapes so production endpoints can be enabled safely once verified.
"""

import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from ..config import BETTING_SITES
from .base_scraper import BaseScraper, OddsData, ScraperError


class EscScraper(BaseScraper):
    """Scraper for ESCOnline / Estoril Sol Casinos football odds."""

    def __init__(self):
        config = BETTING_SITES.get("esc", {})
        super().__init__(
            site_key="esc",
            site_name=config.get("name", "ESC Online / Estoril Sol Casinos"),
            base_url=config.get("url", "https://www.estorilsolcasinos.pt"),
            rate_limit_seconds=config.get("rate_limit_seconds", 5),
        )
        self.sports_url = config.get(
            "sports_url",
            "https://www.estorilsolcasinos.pt/pt/betting/sport/844/matches/date-0",
        )

    def get_match_odds(
        self, home_team: str, away_team: str, match_date: Optional[datetime] = None
    ) -> Optional[OddsData]:
        """Return ESC odds for a fixture, using fallback semantics if live fails."""
        try:
            matches = self.get_upcoming_matches(days_ahead=7)
            candidate = self._find_match(matches, home_team, away_team, match_date)
            if candidate:
                return candidate
        except ScraperError:
            pass

        return self._create_fallback_odds(home_team, away_team, match_date)

    def get_upcoming_matches(self, days_ahead: int = 7) -> List[OddsData]:
        """Get upcoming ESC football matches or explicit fallback rows."""
        try:
            response = self._make_request(self.sports_url)
            matches = self.parse_upcoming_matches_json(response.text)
            if not matches:
                matches = self.parse_upcoming_matches_html(response.text)
            if matches:
                return matches
        except (ScraperError, ValueError, json.JSONDecodeError) as exc:
            print(f"⚠️  ESC live scraping unavailable, using fallback: {exc}")
        except Exception as exc:
            print(f"⚠️  ESC live scraping failed, using fallback: {exc}")

        return self._get_fallback_upcoming_matches(days_ahead)

    def parse_upcoming_matches_json(self, payload: str) -> List[OddsData]:
        """Parse representative ESC JSON into normalized OddsData rows."""
        data = json.loads(payload)
        events = self._extract_events(data)
        matches: List[OddsData] = []

        for event in events:
            match = self._parse_json_event(event)
            if match and match.has_1x2():
                matches.append(match)

        return matches

    def parse_upcoming_matches_html(self, html: str) -> List[OddsData]:
        """Parse representative ESC HTML match cards into OddsData rows."""
        soup = BeautifulSoup(html, "lxml")
        cards = soup.select('[data-esc-fixture="match"], .match-card, .event-card')
        matches: List[OddsData] = []

        for card in cards:
            home = self._text(card, ".home-team, [data-home-team]")
            away = self._text(card, ".away-team, [data-away-team]")
            if not home or not away:
                continue

            time_elem = card.select_one("time[datetime], [data-start-time]")
            starts_at = ""
            if time_elem:
                starts_at = time_elem.get("datetime") or time_elem.get("data-start-time", "")
            match_date = self._parse_datetime(starts_at)
            if not match_date:
                continue

            odds = self._extract_html_1x2_odds(card)
            if not all(odds.values()):
                continue

            match_id = card.get("data-match-id") or card.get("id") or self._match_id(
                home, away, match_date
            )
            url = card.get("data-url") or card.get("href") or self.sports_url
            competition = card.get("data-competition") or self._text(
                card, ".competition, [data-competition-name]"
            )

            matches.append(
                OddsData(
                    match_id=match_id,
                    home_team=home,
                    away_team=away,
                    match_date=match_date,
                    site="esc",
                    site_name=self.site_name,
                    home_win=odds.get("home"),
                    draw=odds.get("draw"),
                    away_win=odds.get("away"),
                    url=urljoin(self.base_url, url),
                    market_name=self._extract_html_market_name(card),
                    league=competition or None,
                    competition=competition or None,
                    status="ok",
                )
            )

        return matches

    def _extract_events(self, data: Any) -> List[Dict[str, Any]]:
        if isinstance(data, list):
            return [event for event in data if isinstance(event, dict)]
        if not isinstance(data, dict):
            return []
        for key in ("events", "matches", "fixtures", "data"):
            value = data.get(key)
            if isinstance(value, list):
                return [event for event in value if isinstance(event, dict)]
            if isinstance(value, dict):
                nested = self._extract_events(value)
                if nested:
                    return nested
        return []

    def _parse_json_event(self, event: Dict[str, Any]) -> Optional[OddsData]:
        participants = event.get("participants") or event.get("contestants") or {}
        home = event.get("home_team") or participants.get("home")
        away = event.get("away_team") or participants.get("away")
        if not home or not away:
            teams = event.get("teams")
            if isinstance(teams, list) and len(teams) >= 2:
                home, away = teams[0], teams[1]
        if not home or not away:
            return None

        starts_at = event.get("starts_at") or event.get("startTime") or event.get("date")
        match_date = self._parse_datetime(starts_at)
        if not match_date:
            return None

        odds = self._extract_json_1x2_odds(event.get("markets", {}))
        if not all(odds.values()):
            return None

        match_id = str(event.get("id") or self._match_id(home, away, match_date))
        competition = event.get("competition") or event.get("tournament")
        league = event.get("league") or competition
        return OddsData(
            match_id=match_id,
            home_team=str(home),
            away_team=str(away),
            match_date=match_date,
            site="esc",
            site_name=self.site_name,
            home_win=odds.get("home"),
            draw=odds.get("draw"),
            away_win=odds.get("away"),
            url=urljoin(self.base_url, str(event.get("url") or self.sports_url)),
            market_name=self._extract_json_market_name(event.get("markets", {})),
            league=str(league) if league else None,
            competition=str(competition) if competition else None,
            status="ok",
        )

    def _extract_json_1x2_odds(self, markets: Any) -> Dict[str, Optional[float]]:
        odds: Dict[str, Optional[float]] = {"home": None, "draw": None, "away": None}
        if isinstance(markets, dict):
            one_x_two = markets.get("1x2") or markets.get("1X2")
            if isinstance(one_x_two, dict):
                odds["home"] = self._parse_float(one_x_two.get("home"))
                odds["draw"] = self._parse_float(one_x_two.get("draw"))
                odds["away"] = self._parse_float(one_x_two.get("away"))
                return odds
            markets_iter = markets.values()
        elif isinstance(markets, list):
            markets_iter = markets
        else:
            return odds

        for market in markets_iter:
            if not isinstance(market, dict):
                continue
            market_name = str(market.get("type") or market.get("name") or "").lower()
            if market_name not in {"1x2", "resultado final", "match winner"}:
                continue
            selections = market.get("selections") or market.get("outcomes") or []
            for selection in selections:
                if not isinstance(selection, dict):
                    continue
                key = str(
                    selection.get("name") or selection.get("type") or selection.get("label")
                ).lower()
                value = self._parse_float(selection.get("odds") or selection.get("price"))
                if key in {"1", "home", "casa"}:
                    odds["home"] = value
                elif key in {"x", "draw", "empate"}:
                    odds["draw"] = value
                elif key in {"2", "away", "fora"}:
                    odds["away"] = value
            if all(odds.values()):
                return odds
        return odds

    def _extract_html_1x2_odds(self, card: Any) -> Dict[str, Optional[float]]:
        odds: Dict[str, Optional[float]] = {"home": None, "draw": None, "away": None}
        selectors = {
            "home": '[data-selection="1"], [data-outcome="home"], .odds-home',
            "draw": '[data-selection="X"], [data-outcome="draw"], .odds-draw',
            "away": '[data-selection="2"], [data-outcome="away"], .odds-away',
        }
        for key, selector in selectors.items():
            elem = card.select_one(selector)
            if elem:
                odds[key] = self._parse_float(elem.get("data-odds") or elem.get_text(" "))
        return odds

    def _extract_json_market_name(self, markets: Any) -> Optional[str]:
        if isinstance(markets, dict):
            if any(key in markets for key in ("1x2", "1X2")):
                return "1X2"
            markets_iter = markets.values()
        elif isinstance(markets, list):
            markets_iter = markets
        else:
            return None

        for market in markets_iter:
            if not isinstance(market, dict):
                continue
            market_name = market.get("name") or market.get("type")
            if market_name:
                return str(market_name)
        return None

    def _extract_html_market_name(self, card: Any) -> Optional[str]:
        market = card.select_one("[data-market], [aria-label], .market-name")
        if not market:
            return None
        return (
            market.get("aria-label")
            or market.get("data-market-label")
            or market.get("data-market")
            or market.get_text(" ", strip=True)
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
                and (match_date is None or match.match_date.date() == match_date.date())
            ):
                return match
        return None

    def _create_fallback_odds(
        self, home_team: str, away_team: str, match_date: Optional[datetime] = None
    ) -> OddsData:
        if match_date is None:
            match_date = datetime.now() + timedelta(days=3)
        base_home = 1.70 + (len(home_team) % 7) * 0.12
        base_away = 1.85 + (len(away_team) % 7) * 0.12
        return OddsData(
            match_id=self._match_id(home_team, away_team, match_date),
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            site="esc",
            site_name=self.site_name,
            home_win=round(base_home, 2),
            draw=3.15,
            away_win=round(base_away, 2),
            url=f"{self.base_url}/pt/betting/fallback/{home_team}-{away_team}",
            market_name="1X2",
            status="fallback",
        )

    def _get_fallback_upcoming_matches(self, days_ahead: int) -> List[OddsData]:
        teams = [
            ("Portugal", "Brazil"),
            ("Benfica", "Porto"),
            ("Sporting", "Braga"),
            ("Spain", "Germany"),
        ]
        today = datetime.now()
        return [
            self._create_fallback_odds(home, away, today + timedelta(days=index + 1))
            for index, (home, away) in enumerate(teams[: max(1, min(days_ahead, len(teams)))])
        ]

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        if not value:
            return None
        text = str(value).replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None

    def _parse_float(self, value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        match = re.search(r"\d+(?:[,.]\d+)?", str(value))
        if not match:
            return None
        return float(match.group(0).replace(",", "."))

    def _text(self, element: Any, selector: str) -> str:
        found = element.select_one(selector)
        if not found:
            return ""
        return found.get("data-home-team") or found.get("data-away-team") or found.get_text(
            " ", strip=True
        )

    def _match_id(self, home_team: str, away_team: str, match_date: datetime) -> str:
        return f"esc_{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}"
