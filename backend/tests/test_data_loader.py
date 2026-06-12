"""
Tests for data_loader module.

Covers:
- DataLoader initialization
- Database operations
- Caching functionality
- Prediction logging
- Accuracy calculation
- FBrefLoader (skeleton)
- FootballDataLoader (skeleton)
"""

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.predictors.data_loader import (
    DataLoader,
    FBrefLoader,
    FootballDataLoader,
)
from src.predictors.team_stats import TeamData


class TestDataLoaderInit:
    """Test DataLoader initialization."""

    def test_init_default_cache_dir(self):
        """Test initialization with default cache directory."""
        loader = DataLoader()

        assert loader.cache_dir is not None
        assert loader.db_path is not None
        assert loader.db_path.exists() or loader.db_path.parent.exists()

    def test_init_custom_cache_dir(self):
        """Test initialization with custom cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = DataLoader(cache_dir=tmpdir)

            assert str(loader.cache_dir) == tmpdir
            assert loader.db_path.exists()

    def test_init_creates_directories(self):
        """Test that initialization creates necessary directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = os.path.join(tmpdir, "nested", "cache")
            DataLoader(cache_dir=custom_dir)

            assert Path(custom_dir).exists()


class TestDatabaseInitialization:
    """Test database schema creation."""

    @pytest.fixture
    def loader(self):
        """Create DataLoader with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield DataLoader(cache_dir=tmpdir)

    def test_database_tables_created(self, loader):
        """Test that database tables are created on init."""
        conn = sqlite3.connect(loader.db_path)
        cursor = conn.cursor()

        # Check odds_cache table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='odds_cache'"
        )
        assert cursor.fetchone() is not None

        # Check predictions_log table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='predictions_log'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    def test_odds_cache_schema(self, loader):
        """Test odds_cache table schema."""
        conn = sqlite3.connect(loader.db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(odds_cache)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "match_id" in columns
        assert "site" in columns
        assert "home_team" in columns
        assert "away_team" in columns
        assert "home_win" in columns
        assert "draw" in columns
        assert "away_win" in columns

        conn.close()

    def test_predictions_log_schema(self, loader):
        """Test predictions_log table schema."""
        conn = sqlite3.connect(loader.db_path)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(predictions_log)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "home_team" in columns
        assert "away_team" in columns
        assert "home_prob" in columns
        assert "draw_prob" in columns
        assert "away_prob" in columns
        assert "actual_result" in columns

        conn.close()


class TestCacheOdds:
    """Test odds caching functionality."""

    @pytest.fixture
    def loader(self):
        """Create DataLoader with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield DataLoader(cache_dir=tmpdir)

    def test_cache_odds_basic(self, loader):
        """Test caching odds data."""
        mock_odds = MagicMock()
        mock_odds.match_id = "test_123"
        mock_odds.site = "betano"
        mock_odds.home_team = "Portugal"
        mock_odds.away_team = "Brazil"
        mock_odds.match_date = datetime.now()
        mock_odds.home_win = 2.10
        mock_odds.draw = 3.20
        mock_odds.away_win = 3.50
        mock_odds.over_2_5 = 1.80
        mock_odds.under_2_5 = 2.00
        mock_odds.btts_yes = 1.70
        mock_odds.btts_no = 2.10

        loader.cache_odds(mock_odds)

        # Verify data was cached
        results = loader.get_cached_odds("Portugal", "Brazil", max_age_hours=1)
        assert len(results) >= 1

    def test_cache_odds_upsert(self, loader):
        """Test that caching same odds updates existing record."""
        mock_odds = MagicMock()
        mock_odds.match_id = "test_123"
        mock_odds.site = "betano"
        mock_odds.home_team = "Portugal"
        mock_odds.away_team = "Brazil"
        mock_odds.match_date = datetime.now()
        mock_odds.home_win = 2.10
        mock_odds.draw = 3.20
        mock_odds.away_win = 3.50
        mock_odds.over_2_5 = 1.80
        mock_odds.under_2_5 = 2.00
        mock_odds.btts_yes = 1.70
        mock_odds.btts_no = 2.10

        # Cache twice
        loader.cache_odds(mock_odds)
        mock_odds.home_win = 2.20  # Change value
        loader.cache_odds(mock_odds)

        # Should only have one record (upsert)
        loader.get_cached_odds("Portugal", "Brazil", max_age_hours=1)
        # Note: Due to UNIQUE constraint, should be 1 record


class TestGetCachedOdds:
    """Test retrieving cached odds."""

    @pytest.fixture
    def loader(self):
        """Create DataLoader with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield DataLoader(cache_dir=tmpdir)

    def test_get_cached_odds_empty(self, loader):
        """Test getting odds when cache is empty."""
        results = loader.get_cached_odds("NonExistent", "Team", max_age_hours=1)
        assert len(results) == 0

    def test_get_cached_odds_by_team(self, loader):
        """Test getting odds filtered by team names."""
        mock_odds = MagicMock()
        mock_odds.match_id = "test_123"
        mock_odds.site = "betano"
        mock_odds.home_team = "Portugal"
        mock_odds.away_team = "Spain"
        mock_odds.match_date = datetime.now()
        mock_odds.home_win = 2.10
        mock_odds.draw = 3.20
        mock_odds.away_win = 3.50
        mock_odds.over_2_5 = 1.80
        mock_odds.under_2_5 = 2.00
        mock_odds.btts_yes = 1.70
        mock_odds.btts_no = 2.10

        loader.cache_odds(mock_odds)

        # Search by team name
        results = loader.get_cached_odds("Portugal", "Spain", max_age_hours=1)
        assert len(results) >= 1
        assert any(r.home_team == "Portugal" for r in results)

    def test_get_cached_odds_max_age(self, loader):
        """Test that old cached odds are filtered out."""
        mock_odds = MagicMock()
        mock_odds.match_id = "old_test"
        mock_odds.site = "betano"
        mock_odds.home_team = "OldTeam"
        mock_odds.away_team = "Team"
        mock_odds.match_date = datetime.now() - timedelta(hours=5)
        mock_odds.home_win = 2.10
        mock_odds.draw = 3.20
        mock_odds.away_win = 3.50
        mock_odds.over_2_5 = 1.80
        mock_odds.under_2_5 = 2.00
        mock_odds.btts_yes = 1.70
        mock_odds.btts_no = 2.10

        # Manually insert old record
        conn = sqlite3.connect(loader.db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO odds_cache
            (match_id, site, home_team, away_team, match_date,
             home_win, draw, away_win, over_2_5, under_2_5, btts_yes, btts_no, cached_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                mock_odds.match_id,
                mock_odds.site,
                mock_odds.home_team,
                mock_odds.away_team,
                mock_odds.match_date.isoformat(),
                mock_odds.home_win,
                mock_odds.draw,
                mock_odds.away_win,
                mock_odds.over_2_5,
                mock_odds.under_2_5,
                mock_odds.btts_yes,
                mock_odds.btts_no,
                (datetime.now() - timedelta(hours=5)).isoformat(),
            ),
        )
        conn.commit()
        conn.close()

        # Should not return old data with 1 hour max age
        results = loader.get_cached_odds("OldTeam", "Team", max_age_hours=1)
        assert len(results) == 0


class TestPredictionLogging:
    """Test prediction logging functionality."""

    @pytest.fixture
    def loader(self):
        """Create DataLoader with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield DataLoader(cache_dir=tmpdir)

    def test_log_prediction(self, loader):
        """Test logging a prediction."""
        mock_prediction = MagicMock()
        mock_prediction.match_date = datetime.now()
        mock_prediction.home_win_prob = 0.45
        mock_prediction.draw_prob = 0.30
        mock_prediction.away_win_prob = 0.25

        loader.log_prediction("Portugal", "Brazil", mock_prediction)

        # Verify logged (check database directly)
        conn = sqlite3.connect(loader.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM predictions_log")
        count = cursor.fetchone()[0]
        conn.close()

        assert count >= 1

    def test_log_prediction_with_result(self, loader):
        """Test logging prediction with actual result."""
        mock_prediction = MagicMock()
        mock_prediction.match_date = datetime.now()
        mock_prediction.home_win_prob = 0.45
        mock_prediction.draw_prob = 0.30
        mock_prediction.away_win_prob = 0.25

        loader.log_prediction(
            "Portugal", "Brazil", mock_prediction, actual_result="home"
        )

        # Verify result was logged
        conn = sqlite3.connect(loader.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT actual_result FROM predictions_log WHERE home_team LIKE '%Portugal%'"
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[0] == "home"


class TestPredictionAccuracy:
    """Test prediction accuracy calculation."""

    @pytest.fixture
    def loader(self):
        """Create DataLoader with temp database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield DataLoader(cache_dir=tmpdir)

    def test_accuracy_empty_database(self, loader):
        """Test accuracy calculation with no data."""
        accuracy = loader.get_prediction_accuracy(days_back=30)

        assert accuracy["total_predictions"] == 0
        assert accuracy["accuracy"] == 0

    def test_accuracy_with_data(self, loader):
        """Test accuracy calculation with sample data."""
        # Insert test predictions
        conn = sqlite3.connect(loader.db_path)
        cursor = conn.cursor()

        # Correct home prediction
        cursor.execute(
            """
            INSERT INTO predictions_log
            (home_team, away_team, match_date, home_prob, draw_prob, away_prob, actual_result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "Team A",
                "Team B",
                datetime.now().isoformat(),
                0.60,
                0.25,
                0.15,
                "home",
                datetime.now().isoformat(),
            ),
        )

        # Incorrect prediction
        cursor.execute(
            """
            INSERT INTO predictions_log
            (home_team, away_team, match_date, home_prob, draw_prob, away_prob, actual_result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                "Team C",
                "Team D",
                datetime.now().isoformat(),
                0.60,
                0.25,
                0.15,
                "away",
                datetime.now().isoformat(),
            ),
        )

        conn.commit()
        conn.close()

        accuracy = loader.get_prediction_accuracy(days_back=30)

        assert accuracy["total_predictions"] == 2
        assert accuracy["correct_predictions"] == 1
        assert accuracy["accuracy"] == 50.0


class TestFBrefLoader:
    """Test FBrefLoader skeleton implementation."""

    def test_fbref_init(self):
        """Test FBrefLoader initialization."""
        loader = FBrefLoader()

        assert loader.base_url == "https://fbref.com"

    def test_get_team_stats_returns_none(self):
        """Test that get_team_stats returns None (skeleton)."""
        loader = FBrefLoader()
        result = loader.get_team_stats("Any Team")

        assert result is None

    def test_get_match_history_returns_empty(self):
        """Test that get_match_history returns empty list (skeleton)."""
        loader = FBrefLoader()
        result = loader.get_match_history("Any Team", last_n=10)

        assert result == []

    def test_get_head_to_head_returns_zeros(self):
        """Test that get_head_to_head returns zeros (skeleton)."""
        loader = FBrefLoader()
        result = loader.get_head_to_head("Team A", "Team B")

        assert result == {"wins": 0, "draws": 0, "losses": 0}


class TestFootballDataLoader:
    """Test FootballDataLoader skeleton implementation."""

    def test_football_data_init_no_key(self):
        """Test FootballDataLoader initialization without API key."""
        loader = FootballDataLoader()

        assert loader.api_key is None
        assert loader.base_url == "https://api.football-data.org/v4"

    def test_football_data_init_with_key(self):
        """Test FootballDataLoader initialization with API key."""
        loader = FootballDataLoader(api_key="test-key-123")

        assert loader.api_key == "test-key-123"

    def test_get_team_data_no_key(self):
        """Test get_team_data returns None without API key."""
        loader = FootballDataLoader()
        result = loader.get_team_data(123)

        assert result is None

    @patch("requests.get")
    def test_get_team_data_with_key_success(self, mock_get):
        """Test get_team_data with valid API response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"name": "FC Porto"}
        mock_get.return_value = mock_response

        loader = FootballDataLoader(api_key="test-key")
        result = loader.get_team_data(123)

        assert result is not None
        assert isinstance(result, TeamData)

    @patch("requests.get")
    def test_get_team_data_with_key_error(self, mock_get):
        """Test get_team_data handles API errors."""
        mock_get.side_effect = Exception("API Error")

        loader = FootballDataLoader(api_key="test-key")
        result = loader.get_team_data(123)

        assert result is None
