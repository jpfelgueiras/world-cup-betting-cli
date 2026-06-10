"""
Base scraper class for betting sites

All scrapers must:
- Respect rate limits
- Rotate user agents
- Handle errors gracefully
- Return standardized odds data
"""

import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import USER_AGENTS


class ScraperError(Exception):
    """Custom exception for scraper errors"""

    pass


@dataclass
class OddsData:
    """Standardized odds data structure"""

    match_id: str
    home_team: str
    away_team: str
    match_date: datetime
    site: str
    site_name: str

    # 1X2 odds
    home_win: Optional[float] = None
    draw: Optional[float] = None
    away_win: Optional[float] = None

    # Over/Under 2.5
    over_2_5: Optional[float] = None
    under_2_5: Optional[float] = None

    # Both teams to score
    btts_yes: Optional[float] = None
    btts_no: Optional[float] = None

    # Asian handicap (optional)
    asian_handicap: Optional[float] = None
    asian_handicap_odds_home: Optional[float] = None
    asian_handicap_odds_away: Optional[float] = None

    # Metadata
    last_updated: datetime = None
    url: Optional[str] = None

    def __post_init__(self):
        if self.last_updated is None:
            self.last_updated = datetime.now()

    def has_1x2(self) -> bool:
        """Check if 1X2 odds are available"""
        return all([self.home_win, self.draw, self.away_win])

    def has_ou25(self) -> bool:
        """Check if Over/Under 2.5 odds are available"""
        return all([self.over_2_5, self.under_2_5])

    def has_btts(self) -> bool:
        """Check if BTTS odds are available"""
        return all([self.btts_yes, self.btts_no])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "match_id": self.match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "match_date": self.match_date.isoformat() if self.match_date else None,
            "site": self.site,
            "site_name": self.site_name,
            "home_win": self.home_win,
            "draw": self.draw,
            "away_win": self.away_win,
            "over_2_5": self.over_2_5,
            "under_2_5": self.under_2_5,
            "btts_yes": self.btts_yes,
            "btts_no": self.btts_no,
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
            "url": self.url,
        }


class BaseScraper(ABC):
    """
    Abstract base class for all betting site scrapers.

    Implements common functionality:
    - Rate limiting
    - Session management
    - User agent rotation
    - Error handling
    """

    def __init__(
        self, site_key: str, site_name: str, base_url: str, rate_limit_seconds: int = 5
    ):
        self.site_key = site_key
        self.site_name = site_name
        self.base_url = base_url
        self.rate_limit_seconds = rate_limit_seconds

        self._session = None
        self._last_request_time = 0
        self._request_count = 0

    @property
    def session(self) -> requests.Session:
        """Get or create requests session with retry logic"""
        if self._session is None:
            self._session = requests.Session()

            # Configure retry strategy
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["GET"],
            )

            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)

            # Set default headers
            self._session.headers.update(
                {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "pt-PT,pt;q=0.9,en;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }
            )

        return self._session

    def _rotate_user_agent(self):
        """Rotate user agent to avoid detection"""
        user_agent = random.choice(USER_AGENTS)
        self.session.headers["User-Agent"] = user_agent

    def _respect_rate_limit(self):
        """Enforce rate limiting between requests"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_seconds:
            sleep_time = self.rate_limit_seconds - elapsed
            time.sleep(sleep_time)
        self._last_request_time = time.time()
        self._request_count += 1

    def _make_request(
        self,
        url: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        timeout: int = 30,
    ) -> requests.Response:
        """
        Make HTTP request with rate limiting and error handling.
        """
        self._respect_rate_limit()
        self._rotate_user_agent()

        try:
            response = self.session.request(
                method=method, url=url, params=params, data=data, timeout=timeout
            )

            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            raise ScraperError(f"Request timed out for {self.site_name}: {url}")
        except requests.exceptions.ConnectionError:
            raise ScraperError(f"Connection error for {self.site_name}: {url}")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                raise ScraperError(
                    f"Access forbidden by {self.site_name}. May be blocked."
                )
            elif e.response.status_code == 404:
                raise ScraperError(f"Page not found: {url}")
            elif e.response.status_code == 429:
                raise ScraperError(
                    f"Rate limited by {self.site_name}. Wait longer between requests."
                )
            else:
                raise ScraperError(
                    f"HTTP error {e.response.status_code} from {self.site_name}"
                )
        except Exception as e:
            raise ScraperError(f"Unexpected error scraping {self.site_name}: {str(e)}")

    @abstractmethod
    def get_match_odds(
        self, home_team: str, away_team: str, match_date: Optional[datetime] = None
    ) -> Optional[OddsData]:
        """
        Get odds for a specific match.

        Args:
            home_team: Home team name
            away_team: Away team name
            match_date: Optional match date for disambiguation

        Returns:
            OddsData if found, None if match not available
        """
        pass

    @abstractmethod
    def get_upcoming_matches(self, days_ahead: int = 7) -> List[OddsData]:
        """
        Get odds for all upcoming matches.

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            List of OddsData for all upcoming matches
        """
        pass

    def normalize_team_name(self, team_name: str) -> str:
        """
        Normalize team name for matching across different sources.

        Handles common variations:
        - Accents/diacritics
        - Country prefixes (e.g., "Portugal" vs "Seleção Portuguesa")
        - Common abbreviations
        """
        import unicodedata

        # Remove accents
        normalized = unicodedata.normalize("NFKD", team_name)
        normalized = "".join(c for c in normalized if not unicodedata.combining(c))

        # Convert to lowercase
        normalized = normalized.lower()

        # Remove common prefixes/suffixes
        prefixes = ["selecao", "seleção", "fc", "cf", "sc", "cd", "ud"]
        for prefix in prefixes:
            if normalized.startswith(prefix + " "):
                normalized = normalized[len(prefix) + 1 :]

        # Remove country indicators
        indicators = [" portugal", " brasil", " brazil", " england", " spain"]
        for indicator in indicators:
            normalized = normalized.replace(indicator, "")

        return normalized.strip()

    def find_team_match(
        self, matches: List[OddsData], team_name: str
    ) -> Optional[OddsData]:
        """Find a match containing a specific team"""
        normalized = self.normalize_team_name(team_name)

        for match in matches:
            home_norm = self.normalize_team_name(match.home_team)
            away_norm = self.normalize_team_name(match.away_team)

            if normalized in home_norm or normalized in away_norm:
                return match

        return None

    def get_status(self) -> Dict[str, Any]:
        """Get scraper status and statistics"""
        return {
            "site": self.site_key,
            "site_name": self.site_name,
            "base_url": self.base_url,
            "rate_limit_seconds": self.rate_limit_seconds,
            "total_requests": self._request_count,
            "last_request": (
                datetime.fromtimestamp(self._last_request_time).isoformat()
                if self._last_request_time > 0
                else None
            ),
        }
