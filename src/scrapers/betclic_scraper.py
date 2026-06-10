"""
Betclic.pt scraper

Similar structure to Betano scraper but adapted for Betclic's site structure.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from .base_scraper import BaseScraper, OddsData, ScraperError
from ..config import BETTING_SITES


class BetclicScraper(BaseScraper):
    """Scraper for Betclic.pt"""

    def __init__(self):
        config = BETTING_SITES.get('betclic', {})
        super().__init__(
            site_key='betclic',
            site_name=config.get('name', 'Betclic.pt'),
            base_url=config.get('url', 'https://www.betclic.pt'),
            rate_limit_seconds=config.get('rate_limit_seconds', 5)
        )

        self.sports_url = config.get('sports_url', 'https://www.betclic.pt/futebol-s1/')

    def get_match_odds(
        self,
        home_team: str,
        away_team: str,
        match_date: Optional[datetime] = None
    ) -> Optional[OddsData]:
        """Get odds for a specific match"""
        try:
            # Skeleton implementation - see Betano for detailed comments
            return self._create_mock_odds(home_team, away_team, match_date)
        except ScraperError:
            raise
        except Exception as e:
            raise ScraperError(f"Error scraping Betclic for {home_team} vs {away_team}: {str(e)}")

    def get_upcoming_matches(self, days_ahead: int = 7) -> List[OddsData]:
        """Get odds for all upcoming matches"""
        try:
            # Would navigate to Betclic football section and parse matches
            return self._get_mock_upcoming_matches(days_ahead)
        except ScraperError as e:
            print(f"Betclic scraping failed, using mock: {e}")
            return self._get_mock_upcoming_matches(days_ahead)
        except Exception as e:
            raise ScraperError(f"Error getting upcoming matches from Betclic: {str(e)}")

    def _create_mock_odds(
        self,
        home_team: str,
        away_team: str,
        match_date: Optional[datetime] = None
    ) -> OddsData:
        """Create mock odds data for demonstration"""
        
        if match_date is None:
            match_date = datetime.now() + timedelta(days=3)
        
        # Simple deterministic odds based on team name lengths
        # Always produces valid odds > 1.0
        base_home = 1.85 + (len(home_team) % 10) * 0.12
        base_away = 2.05 + (len(away_team) % 10) * 0.12
        base_draw = 3.25
        
        return OddsData(
            match_id=f"betclic_{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}",
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            site='betclic',
            site_name=self.site_name,
            home_win=round(base_home, 2),
            draw=round(base_draw, 2),
            away_win=round(base_away, 2),
            over_2_5=1.90,
            under_2_5=2.00,
            btts_yes=1.80,
            btts_no=2.10,
            url=f"{self.base_url}/futebol/{home_team}-{away_team}",
        )

    def _get_mock_upcoming_matches(self, days_ahead: int) -> List[OddsData]:
        """Generate mock upcoming matches"""

        teams = [
            ('Portugal', 'Brazil'),
            ('Spain', 'Germany'),
            ('France', 'Argentina'),
            ('England', 'Italy'),
            ('Netherlands', 'Belgium'),
            ('Croatia', 'Uruguay'),
            ('Morocco', 'Japan'),
            ('USA', 'Mexico'),
        ]

        matches = []
        today = datetime.now()

        for i, (home, away) in enumerate(teams):
            match_date = today + timedelta(days=i+1)
            odds = self._create_mock_odds(home, away, match_date)
            matches.append(odds)

        return matches
