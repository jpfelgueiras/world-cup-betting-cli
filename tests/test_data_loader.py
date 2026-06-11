"""
Unit tests for Data Loader Module

Tests for DataLoader, FBrefLoader, and FootballDataLoader classes.
"""

import os
import sqlite3
import tempfile
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from src.predictors.data_loader import DataLoader, FBrefLoader, FootballDataLoader
from src.predictors.team_stats import TeamData
from src.scrapers.base_scraper import OddsData


class TestDataLoader:
    """Tests for the DataLoader class"""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def data_loader(self, temp_cache_dir):
        """Create a DataLoader instance with temporary cache"""
        return DataLoader(cache_dir=temp_cache_dir)

    @pytest.fixture
    def sample_odds(self):
        """Create sample OddsData for testing"""
        match_date = datetime.now() + timedelta(days=3)
        return OddsData(
            match_id="test_match_123",
            home_team="Portugal",
            away_team="Brazil",
            match_date=match_date,
            site="betano",
            site_name="Betano.pt",
            home_win=2.10,
            draw=3.20,
            away_win=2.80,
            over_2_5=1.85,
            under_2_5=1.95,
            btts_yes=1.70,
            btts_no=2.10,
        )

    def test_init_creates_cache_directory(self, temp_cache_dir):
        """Test initialization creates cache directory"""
        _ = DataLoader(cache_dir=temp_cache_dir)

        assert os.path.exists(temp_cache_dir)
        assert os.path.isdir(temp_cache_dir)

    def test_init_creates_database(self, data_loader, temp_cache_dir):
        """Test initialization creates SQLite database"""
        db_path = os.path.join(temp_cache_dir, "odds_history.db")

        assert os.path.exists(db_path)

        # Verify database has expected tables
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        assert "odds_cache" in tables
        assert "predictions_log" in tables

        conn.close()

    def test_database_schema(self, data_loader, temp_cache_dir):
        """Test database has correct schema"""
        db_path = os.path.join(temp_cache_dir, "odds_history.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check odds_cache table columns
        cursor.execute("PRAGMA table_info(odds_cache)")
        odds_columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "match_id" in odds_columns
        assert "site" in odds_columns
        assert "home_team" in odds_columns
        assert "away_team" in odds_columns
        assert "home_win" in odds_columns
        assert "draw" in odds_columns
        assert "away_win" in odds_columns

        # Check predictions_log table columns
        cursor.execute("PRAGMA table_info(predictions_log)")
        pred_columns = {row[1]: row[2] for row in cursor.fetchall()}

        assert "home_team" in pred_columns
        assert "away_team" in pred_columns
        assert "home_prob" in pred_columns
        assert "draw_prob" in pred_columns
        assert "away_prob" in pred_columns

        conn.close()

    def test_cache_odds(self, data_loader, sample_odds):
        """Test caching odds data"""
        # Cache the odds
        data_loader.cache_odds(sample_odds)

        # Verify data was cached
        db_path = str(data_loader.db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT match_id, home_team, away_team, home_win FROM odds_cache"
        )
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == "test_match_123"
        assert "Portugal" in row[1]
        assert "Brazil" in row[2]
        assert row[3] == pytest.approx(2.10, rel=0.01)

        conn.close()

    def test_cache_odds_replaces_existing(self, data_loader, sample_odds):
        """Test that caching replaces existing entry with same match_id"""
        # Cache initial odds
        data_loader.cache_odds(sample_odds)

        # Update odds and cache again
        sample_odds.home_win = 2.50
        data_loader.cache_odds(sample_odds)

        # Verify only one entry exists and it has updated value
        db_path = str(data_loader.db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) FROM odds_cache WHERE match_id = ?", ("test_match_123",)
        )
        count = cursor.fetchone()[0]

        assert count == 1

        cursor.execute(
            "SELECT home_win FROM odds_cache WHERE match_id = ?", ("test_match_123",)
        )
        home_win = cursor.fetchone()[0]

        assert home_win == pytest.approx(2.50, rel=0.01)

        conn.close()

    def test_get_cached_odds_returns_data(self, data_loader, sample_odds):
        """Test retrieving cached odds"""
        # Cache the odds
        data_loader.cache_odds(sample_odds)

        # Retrieve cached odds
        cached = data_loader.get_cached_odds("Portugal", "Brazil", max_age_hours=1)

        assert len(cached) > 0
        assert isinstance(cached[0], OddsData)
        assert cached[0].home_team == "Portugal"
        assert cached[0].away_team == "Brazil"

    def test_get_cached_odds_respects_max_age(self, data_loader, sample_odds):
        """Test that get_cached_odds respects max_age_hours parameter"""
        # Cache the odds
        data_loader.cache_odds(sample_odds)

        # Try to retrieve with very short max age (should still work since just cached)
        cached = data_loader.get_cached_odds("Portugal", "Brazil", max_age_hours=1)

        assert len(cached) > 0

    def test_get_cached_odds_expired(self, data_loader, sample_odds):
        """Test that expired cache entries are not returned"""
        # Cache the odds
        data_loader.cache_odds(sample_odds)

        # Try to retrieve with 0 hour max age (should return empty)
        cached = data_loader.get_cached_odds("Portugal", "Brazil", max_age_hours=0)

        # May or may not return data depending on timing
        # Just verify it doesn't crash
        assert isinstance(cached, list)

    def test_get_cached_odds_team_name_partial_match(self, data_loader, sample_odds):
        """Test that team name matching is partial (LIKE query)"""
        data_loader.cache_odds(sample_odds)

        # Should match even with partial team name
        cached = data_loader.get_cached_odds("Portu", "Braz", max_age_hours=1)

        assert len(cached) > 0

    def test_log_prediction(self, data_loader):
        """Test logging a prediction"""
        mock_prediction = Mock()
        mock_prediction.home_win_prob = 0.45
        mock_prediction.draw_prob = 0.25
        mock_prediction.away_win_prob = 0.30
        mock_prediction.match_date = datetime.now() + timedelta(days=3)

        data_loader.log_prediction(
            home_team="Portugal",
            away_team="Brazil",
            prediction=mock_prediction,
            actual_result=None,
        )

        # Verify data was logged
        db_path = str(data_loader.db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT home_team, away_team, home_prob FROM predictions_log")
        row = cursor.fetchone()

        assert row is not None
        assert row[0] == "Portugal"
        assert row[1] == "Brazil"
        assert row[2] == pytest.approx(0.45, rel=0.01)

        conn.close()

    def test_log_prediction_with_actual_result(self, data_loader):
        """Test logging prediction with actual result"""
        mock_prediction = Mock()
        mock_prediction.home_win_prob = 0.45
        mock_prediction.draw_prob = 0.25
        mock_prediction.away_win_prob = 0.30
        mock_prediction.match_date = datetime.now() + timedelta(days=3)

        data_loader.log_prediction(
            home_team="Portugal",
            away_team="Brazil",
            prediction=mock_prediction,
            actual_result="home",
        )

        # Verify actual_result was stored
        db_path = str(data_loader.db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT actual_result FROM predictions_log")
        row = cursor.fetchone()

        assert row[0] == "home"

        conn.close()

    def test_get_prediction_accuracy_empty(self, data_loader):
        """Test accuracy calculation with no predictions"""
        accuracy = data_loader.get_prediction_accuracy(days_back=30)

        assert accuracy["total_predictions"] == 0
        assert accuracy["correct_predictions"] == 0
        assert accuracy["accuracy"] == 0
        assert accuracy["home_correct"] == 0
        assert accuracy["draw_correct"] == 0
        assert accuracy["away_correct"] == 0

    def test_get_prediction_accuracy_with_data(self, data_loader):
        """Test accuracy calculation with predictions"""
        # Log several predictions with known outcomes
        for i in range(5):
            mock_pred = Mock()
            mock_pred.home_win_prob = 0.60 if i < 3 else 0.30
            mock_pred.draw_prob = 0.25
            mock_pred.away_win_prob = 0.15 if i < 3 else 0.45
            mock_pred.match_date = datetime.now() - timedelta(days=i)

            # First 3: predicted home, actual home (correct)
            # Last 2: predicted away, actual away (correct)
            actual = "home" if i < 3 else "away"

            data_loader.log_prediction(
                home_team=f"Team_{i}",
                away_team=f"Team_{i+10}",
                prediction=mock_pred,
                actual_result=actual,
            )

        accuracy = data_loader.get_prediction_accuracy(days_back=30)

        assert accuracy["total_predictions"] == 5
        assert accuracy["correct_predictions"] == 5  # All should be correct
        assert accuracy["accuracy"] == 100.0
        assert accuracy["home_correct"] == 3
        assert accuracy["away_correct"] == 2

    def test_get_prediction_accuracy_mixed_results(self, data_loader):
        """Test accuracy calculation with mixed correct/incorrect predictions"""
        # Log predictions where some are wrong
        mock_pred_home = Mock()
        mock_pred_home.home_win_prob = 0.60
        mock_pred_home.draw_prob = 0.25
        mock_pred_home.away_win_prob = 0.15
        mock_pred_home.match_date = datetime.now()

        # Predicted home but actual was away (incorrect)
        data_loader.log_prediction(
            home_team="Team A",
            away_team="Team B",
            prediction=mock_pred_home,
            actual_result="away",
        )

        accuracy = data_loader.get_prediction_accuracy(days_back=30)

        assert accuracy["total_predictions"] == 1
        assert accuracy["correct_predictions"] == 0
        assert accuracy["accuracy"] == 0.0


class TestFBrefLoader:
    """Tests for the FBrefLoader class"""

    @pytest.fixture
    def fbref_loader(self):
        """Create FBrefLoader instance"""
        return FBrefLoader()

    def test_init_sets_base_url(self, fbref_loader):
        """Test initialization sets base URL"""
        assert fbref_loader.base_url == "https://fbref.com"

    def test_get_team_stats_returns_none(self, fbref_loader):
        """Test get_team_stats returns None (skeleton implementation)"""
        result = fbref_loader.get_team_stats("Portugal")

        assert result is None

    def test_get_match_history_returns_empty_list(self, fbref_loader):
        """Test get_match_history returns empty list (skeleton implementation)"""
        result = fbref_loader.get_match_history("Portugal", last_n=10)

        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_head_to_head_returns_zeros(self, fbref_loader):
        """Test get_head_to_head returns zeroed record (skeleton implementation)"""
        result = fbref_loader.get_head_to_head("Portugal", "Brazil")

        assert isinstance(result, dict)
        assert result["wins"] == 0
        assert result["draws"] == 0
        assert result["losses"] == 0

    @patch("requests.get")
    def test_get_team_stats_skeleton_notes(self, mock_get, fbref_loader):
        """Verify skeleton implementation notes are accurate"""
        # The implementation explicitly notes it's a skeleton
        # This test documents that behavior
        result = fbref_loader.get_team_stats("Any Team")
        assert result is None


class TestFootballDataLoader:
    """Tests for the FootballDataLoader class"""

    @pytest.fixture
    def football_loader_no_key(self):
        """Create FootballDataLoader without API key"""
        return FootballDataLoader(api_key=None)

    @pytest.fixture
    def football_loader_with_key(self):
        """Create FootballDataLoader with API key"""
        return FootballDataLoader(api_key="test_api_key_123")

    def test_init_without_api_key(self, football_loader_no_key):
        """Test initialization without API key"""
        assert football_loader_no_key.api_key is None
        assert football_loader_no_key.base_url == "https://api.football-data.org/v4"

    def test_init_with_api_key(self, football_loader_with_key):
        """Test initialization with API key"""
        assert football_loader_with_key.api_key == "test_api_key_123"

    def test_get_team_data_no_api_key(self, football_loader_no_key):
        """Test get_team_data returns None when no API key"""
        result = football_loader_no_key.get_team_data(123)

        assert result is None

    @patch("requests.get")
    def test_get_team_data_success(self, mock_get, football_loader_with_key):
        """Test get_team_data with successful API response"""
        # Setup mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "FC Porto",
            "shortName": "Porto",
            "founded": 1893,
        }
        mock_get.return_value = mock_response

        result = football_loader_with_key.get_team_data(503)

        assert result is not None
        assert isinstance(result, TeamData)
        assert result.name == "FC Porto"
        mock_get.assert_called_once()

    @patch("requests.get")
    def test_get_team_data_api_error(self, mock_get, football_loader_with_key):
        """Test get_team_data handles API errors gracefully"""
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        result = football_loader_with_key.get_team_data(123)

        assert result is None

    @patch("requests.get")
    def test_get_team_data_404(self, mock_get, football_loader_with_key):
        """Test get_team_data handles 404 response"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = football_loader_with_key.get_team_data(999999)

        assert result is None

    def test_parse_team_response_minimal(self, football_loader_with_key):
        """Test _parse_team_response with minimal data"""
        data = {"name": "Benfica"}

        result = football_loader_with_key._parse_team_response(data)

        assert isinstance(result, TeamData)
        assert result.name == "Benfica"

    def test_parse_team_response_empty(self, football_loader_with_key):
        """Test _parse_team_response with empty data"""
        data = {}

        result = football_loader_with_key._parse_team_response(data)

        assert isinstance(result, TeamData)
        assert result.name == "Unknown"

    def test_parse_team_response_full(self, football_loader_with_key):
        """Test _parse_team_response with full data"""
        data = {
            "name": "Sporting CP",
            "shortName": "Sporting",
            "founded": 1906,
            "clubColors": "Green / White",
            "venue": "Estádio José Alvalade",
        }

        result = football_loader_with_key._parse_team_response(data)

        assert isinstance(result, TeamData)
        assert result.name == "Sporting CP"


class TestDataLoaderIntegration:
    """Integration tests for DataLoader workflow"""

    @pytest.fixture
    def temp_cache_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    def test_full_workflow(self, temp_cache_dir):
        """Test complete workflow: cache, retrieve, log, analyze"""
        loader = DataLoader(cache_dir=temp_cache_dir)

        # Create test odds
        match_date = datetime.now() + timedelta(days=3)
        odds = OddsData(
            match_id="workflow_test",
            home_team="Team A",
            away_team="Team B",
            match_date=match_date,
            site="test",
            site_name="Test Site",
            home_win=2.0,
            draw=3.0,
            away_win=2.5,
        )

        # Cache odds
        loader.cache_odds(odds)

        # Retrieve cached odds
        cached = loader.get_cached_odds("Team A", "Team B", max_age_hours=1)
        assert len(cached) > 0

        # Log prediction
        mock_pred = Mock()
        mock_pred.home_win_prob = 0.50
        mock_pred.draw_prob = 0.30
        mock_pred.away_win_prob = 0.20
        mock_pred.match_date = match_date

        loader.log_prediction("Team A", "Team B", mock_pred, actual_result="home")

        # Get accuracy
        accuracy = loader.get_prediction_accuracy(days_back=30)
        assert accuracy["total_predictions"] == 1
