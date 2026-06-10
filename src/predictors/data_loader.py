"""
Data loaders for team statistics and historical data

Supports multiple data sources:
- FBref (web scraping)
- Football-Data.org (API)
- Local CSV files
"""

import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from .team_stats import TeamData


class DataLoader:
    """Load team data from various sources"""

    def __init__(self, cache_dir: Optional[str] = None):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / 'data' / 'cache'

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite cache
        self.db_path = self.cache_dir / 'odds_history.db'
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for caching"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS odds_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT,
                site TEXT,
                home_team TEXT,
                away_team TEXT,
                match_date TEXT,
                home_win REAL,
                draw REAL,
                away_win REAL,
                over_2_5 REAL,
                under_2_5 REAL,
                btts_yes REAL,
                btts_no REAL,
                cached_at TEXT,
                UNIQUE(match_id, site)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                home_team TEXT,
                away_team TEXT,
                match_date TEXT,
                home_prob REAL,
                draw_prob REAL,
                away_prob REAL,
                actual_result TEXT,
                created_at TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def cache_odds(self, odds_data: Any):
        """Cache odds data to SQLite"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT OR REPLACE INTO odds_cache
            (match_id, site, home_team, away_team, match_date,
             home_win, draw, away_win, over_2_5, under_2_5, btts_yes, btts_no, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            odds_data.match_id,
            odds_data.site,
            odds_data.home_team,
            odds_data.away_team,
            odds_data.match_date.isoformat() if odds_data.match_date else None,
            odds_data.home_win,
            odds_data.draw,
            odds_data.away_win,
            odds_data.over_2_5,
            odds_data.under_2_5,
            odds_data.btts_yes,
            odds_data.btts_no,
            datetime.now().isoformat(),
        ))

        conn.commit()
        conn.close()

    def get_cached_odds(
        self,
        home_team: str,
        away_team: str,
        max_age_hours: int = 1
    ) -> List[Any]:
        """Get recently cached odds for a match"""
        from ..scrapers.base_scraper import OddsData

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()

        cursor.execute('''
            SELECT * FROM odds_cache
            WHERE home_team LIKE ? AND away_team LIKE ?
            AND cached_at > ?
            ORDER BY cached_at DESC
        ''', (f'%{home_team}%', f'%{away_team}%', cutoff))

        rows = cursor.fetchall()
        conn.close()

        results = []
        for row in rows:
            odds = OddsData(
                match_id=row[1],
                site=row[2],
                home_team=row[3],
                away_team=row[4],
                match_date=datetime.fromisoformat(row[5]) if row[5] else None,
                home_win=row[6],
                draw=row[7],
                away_win=row[8],
                over_2_5=row[9],
                under_2_5=row[10],
                btts_yes=row[11],
                btts_no=row[12],
            )
            results.append(odds)

        return results

    def log_prediction(
        self,
        home_team: str,
        away_team: str,
        prediction: Any,
        actual_result: Optional[str] = None
    ):
        """Log prediction for later accuracy tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO predictions_log
            (home_team, away_team, match_date, home_prob, draw_prob, away_prob, actual_result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            home_team,
            away_team,
            prediction.match_date.isoformat() if hasattr(prediction, 'match_date') else None,
            prediction.home_win_prob,
            prediction.draw_prob,
            prediction.away_win_prob,
            actual_result,
            datetime.now().isoformat(),
        ))

        conn.commit()
        conn.close()

    def get_prediction_accuracy(self, days_back: int = 30) -> Dict[str, float]:
        """Calculate prediction accuracy over recent period"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days_back)).isoformat()

        cursor.execute('''
            SELECT COUNT(*),
                   SUM(CASE WHEN actual_result = 'home' AND home_prob > draw_prob AND home_prob > away_prob THEN 1 ELSE 0 END),
                   SUM(CASE WHEN actual_result = 'draw' AND draw_prob > home_prob AND draw_prob > away_prob THEN 1 ELSE 0 END),
                   SUM(CASE WHEN actual_result = 'away' AND away_prob > home_prob AND away_prob > draw_prob THEN 1 ELSE 0 END)
            FROM predictions_log
            WHERE created_at > ? AND actual_result IS NOT NULL
        ''', (cutoff,))

        row = cursor.fetchone()
        conn.close()

        total = row[0] or 0
        correct = (row[1] or 0) + (row[2] or 0) + (row[3] or 0)

        return {
            'total_predictions': total,
            'correct_predictions': correct,
            'accuracy': (correct / total * 100) if total > 0 else 0,
            'home_correct': row[1] or 0,
            'draw_correct': row[2] or 0,
            'away_correct': row[3] or 0,
        }


class FBrefLoader:
    """
    Load team data from FBref.com

    Note: This is a skeleton implementation.
    Real scraping would require:
    - Proper HTML parsing
    - Rate limiting
    - Handling anti-bot measures
    """

    def __init__(self):
        self.base_url = "https://fbref.com"

    def get_team_stats(self, team_name: str) -> Optional[TeamData]:
        """
        Get team statistics from FBref.

        Returns TeamData with stats or None if not found.
        """
        # Skeleton implementation
        # In real version:
        # 1. Search for team on FBref
        # 2. Scrape season stats page
        # 3. Parse table data

        return None

    def get_match_history(
        self,
        team_name: str,
        last_n: int = 10
    ) -> List[Dict[str, Any]]:
        """Get last N matches for a team"""
        # Would scrape match history from FBref
        return []

    def get_head_to_head(
        self,
        team_a: str,
        team_b: str
    ) -> Dict[str, int]:
        """Get head-to-head record between two teams"""
        # Would find historical matchups
        return {'wins': 0, 'draws': 0, 'losses': 0}


class FootballDataLoader:
    """
    Load data from Football-Data.org API

    Requires API key from https://www.football-data.org/
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.football-data.org/v4"

    def get_team_data(self, team_id: int) -> Optional[TeamData]:
        """Get team data from API"""
        if not self.api_key:
            return None

        import requests

        try:
            response = requests.get(
                f"{self.base_url}/teams/{team_id}",
                headers={'X-Auth-Token': self.api_key}
            )

            if response.status_code == 200:
                data = response.json()
                # Parse into TeamData
                return self._parse_team_response(data)
        except Exception:
            pass

        return None

    def _parse_team_response(self, data: Dict) -> TeamData:
        """Parse API response into TeamData"""
        # Implementation depends on API structure
        return TeamData(name=data.get('name', 'Unknown'))
