"""
Solverde.pt scraper

Solverde is a Portuguese casino and betting operator.
"""

from datetime import datetime, timedelta
from typing import List, Optional

from .base_scraper import BaseScraper, OddsData, ScraperError
from ..config import BETTING_SITES


class SolverdeScraper(BaseScraper):
    """Scraper for Solverde.pt"""

    def __init__(self):
        config = BETTING_SITES.get('solverde', {})
        super().__init__(
            site_key='solverde',
            site_name=config.get('name', 'Solverde.pt'),
            base_url=config.get('url', 'https://www.solverde.pt'),
            rate_limit_seconds=config.get('rate_limit_seconds', 5)
        )

        self.sports_url = config.get('sports_url', 'https://www.solverde.pt/apostas-desportivas/futebol/')

    def get_match_odds(
        self,
        home_team: str,
        away_team: str,
        match_date: Optional[datetime] = None
    ) -> Optional[OddsData]:
        """Get odds for a specific match"""
        try:
            return self._create_mock_odds(home_team, away_team, match_date)
        except ScraperError:
            raise
        except Exception as e:
            raise ScraperError(f"Error scraping Solverde for {home_team} vs {away_team}: {str(e)}")

    def get_upcoming_matches(self, days_ahead: int = 7) -> List[OddsData]:
        """Get odds for all upcoming matches"""
        try:
            return self._get_mock_upcoming_matches(days_ahead)
        except ScraperError as e:
            print(f"Solverde scraping failed, using mock: {e}")
            return self._get_mock_upcoming_matches(days_ahead)
        except Exception as e:
            raise ScraperError(f"Error getting upcoming matches from Solverde: {str(e)}")

    def _create_mock_odds(
        self,
        home_team: str,
        away_team: str,
        match_date: Optional[datetime] = None
    ) -> OddsData:
        """Create mock odds with Solverde-style variations"""
        import random

        if match_date is None:
            match_date = datetime.now() + timedelta(days=3)

        # Solverde odds patterns
        base_home = random.uniform(1.78, 3.55)
        base_draw = random.uniform(3.05, 4.1)
        base_away = random.uniform(1.78, 3.55)

        total_implied = (1/base_home + 1/base_draw + 1/base_away)
        margin = 1.055
        home_win = round((1/base_home) / total_implied * margin, 2)
        draw = round((1/base_draw) / total_implied * margin, 2)
        away_win = round((1/base_away) / total_implied * margin, 2)

        return OddsData(
            match_id=f"solverde_{home_team}_{away_team}_{match_date.strftime('%Y%m%d')}",
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            site='solverde',
            site_name=self.site_name,
            home_win=home_win,
            draw=draw,
            away_win=away_win,
            over_2_5=round(random.uniform(1.68, 2.12), 2),
            under_2_5=round(random.uniform(1.68, 2.12), 2),
            btts_yes=round(random.uniform(1.58, 2.08), 2),
            btts_no=round(random.uniform(1.68, 2.22), 2),
            url=f"{self.base_url}/apostas/futebol/{home_team}-{away_team}",
        )

    def _get_mock_upcoming_matches(self, days_ahead: int) -> List[OddsData]:
        """Generate mock upcoming matches"""
        import random

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
