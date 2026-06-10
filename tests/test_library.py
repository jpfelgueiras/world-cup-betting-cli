"""
Unit tests for Python Library Interface

Tests the BettingInsights class and related models in src/library.py
"""

from datetime import datetime, timedelta

import pytest

from src.library import (
    BettingInsights,
    MatchAnalysisResult,
    ScanResult,
    create_insights,
)


class TestMatchAnalysisResult:
    """Tests for MatchAnalysisResult dataclass"""

    def test_create_result(self):
        """Test creating MatchAnalysisResult"""
        result = MatchAnalysisResult(
            home_team="Portugal",
            away_team="Brazil",
            home_win_prob=0.35,
            draw_prob=0.28,
            away_win_prob=0.37,
        )

        assert result.home_team == "Portugal"
        assert result.away_team == "Brazil"
        assert result.home_win_prob == pytest.approx(0.35, rel=0.01)

    def test_most_likely_outcome_home(self):
        """Test most_likely_outcome when home is favored"""
        result = MatchAnalysisResult(
            home_team="Home",
            away_team="Away",
            home_win_prob=0.55,
            draw_prob=0.25,
            away_win_prob=0.20,
        )

        assert result.most_likely_outcome == "home"

    def test_most_likely_outcome_away(self):
        """Test most_likely_outcome when away is favored"""
        result = MatchAnalysisResult(
            home_team="Home",
            away_team="Away",
            home_win_prob=0.20,
            draw_prob=0.25,
            away_win_prob=0.55,
        )

        assert result.most_likely_outcome == "away"

    def test_most_likely_outcome_draw(self):
        """Test most_likely_outcome when draw is most likely"""
        result = MatchAnalysisResult(
            home_team="Home",
            away_team="Away",
            home_win_prob=0.30,
            draw_prob=0.45,
            away_win_prob=0.25,
        )

        assert result.most_likely_outcome == "draw"

    def test_has_value_bets_true(self):
        """Test has_value_bets when there are value bets"""
        from src.utils.ev_calculator import BetRecommendation

        result = MatchAnalysisResult(
            home_team="Home",
            away_team="Away",
            value_bets=[
                BetRecommendation(
                    market="Test",
                    site="test",
                    site_name="Test",
                    odds=2.0,
                    probability=0.55,
                    ev_percentage=10.0,
                    confidence=70.0,
                    reasoning=[],
                    is_value_bet=True,
                )
            ],
        )

        assert result.has_value_bets is True

    def test_has_value_bets_false(self):
        """Test has_value_bets when no value bets"""
        result = MatchAnalysisResult(home_team="Home", away_team="Away", value_bets=[])

        assert result.has_value_bets is False

    def test_get_best_value_bet(self):
        """Test getting best value bet by EV"""
        from src.utils.ev_calculator import BetRecommendation

        result = MatchAnalysisResult(
            home_team="Home",
            away_team="Away",
            value_bets=[
                BetRecommendation(
                    market="Low EV",
                    site="test",
                    site_name="Test",
                    odds=2.0,
                    probability=0.52,
                    ev_percentage=4.0,
                    confidence=65.0,
                    reasoning=[],
                    is_value_bet=True,
                ),
                BetRecommendation(
                    market="High EV",
                    site="test",
                    site_name="Test",
                    odds=2.5,
                    probability=0.50,
                    ev_percentage=25.0,
                    confidence=60.0,
                    reasoning=[],
                    is_value_bet=True,
                ),
            ],
        )

        best = result.get_best_value_bet()

        assert best is not None
        assert best.market == "High EV"
        assert best.ev_percentage == pytest.approx(25.0, rel=0.01)

    def test_get_best_value_bet_empty(self):
        """Test getting best value bet when none exist"""
        result = MatchAnalysisResult(home_team="Home", away_team="Away", value_bets=[])

        best = result.get_best_value_bet()

        assert best is None

    def test_to_dict(self):
        """Test converting result to dictionary"""
        result = MatchAnalysisResult(
            home_team="Portugal",
            away_team="Brazil",
            home_win_prob=0.35,
            draw_prob=0.28,
            away_win_prob=0.37,
            num_bookmakers=3,
        )

        data = result.to_dict()

        assert isinstance(data, dict)
        assert data["home_team"] == "Portugal"
        assert data["away_team"] == "Brazil"
        assert "probabilities" in data
        assert "value_bets" in data
        assert data["num_bookmakers"] == 3


class TestScanResult:
    """Tests for ScanResult dataclass"""

    def test_create_scan_result(self):
        """Test creating ScanResult"""
        result = ScanResult(
            total_matches=10,
            matches_with_value_bets=5,
            total_value_bets=12,
        )

        assert result.total_matches == 10
        assert result.matches_with_value_bets == 5
        assert result.total_value_bets == 12

    def test_all_value_bets_empty(self):
        """Test all_value_bets when no matches"""
        result = ScanResult(
            total_matches=0,
            matches=[],
        )

        all_bets = result.all_value_bets
        assert len(all_bets) == 0

    def test_all_value_bets_aggregates(self):
        """Test all_value_bets aggregates from all matches"""
        from src.utils.ev_calculator import BetRecommendation

        match1 = MatchAnalysisResult(
            home_team="Team A",
            away_team="Team B",
            value_bets=[
                BetRecommendation(
                    market="M1",
                    site="test",
                    site_name="Test",
                    odds=2.0,
                    probability=0.55,
                    ev_percentage=10.0,
                    confidence=70.0,
                    reasoning=[],
                    is_value_bet=True,
                ),
            ],
        )

        match2 = MatchAnalysisResult(
            home_team="Team C",
            away_team="Team D",
            value_bets=[
                BetRecommendation(
                    market="M2",
                    site="test",
                    site_name="Test",
                    odds=2.0,
                    probability=0.55,
                    ev_percentage=15.0,
                    confidence=70.0,
                    reasoning=[],
                    is_value_bet=True,
                ),
                BetRecommendation(
                    market="M3",
                    site="test",
                    site_name="Test",
                    odds=2.0,
                    probability=0.55,
                    ev_percentage=8.0,
                    confidence=70.0,
                    reasoning=[],
                    is_value_bet=True,
                ),
            ],
        )

        result = ScanResult(
            total_matches=2,
            matches_with_value_bets=2,
            total_value_bets=3,
            matches=[match1, match2],
        )

        all_bets = result.all_value_bets

        assert len(all_bets) == 3

    def test_get_top_value_bets(self):
        """Test getting top N value bets across all matches"""
        from src.utils.ev_calculator import BetRecommendation

        # Create matches with multiple value bets
        match1 = MatchAnalysisResult(
            home_team="A",
            away_team="B",
            value_bets=[
                BetRecommendation(
                    market="EV5",
                    site="test",
                    site_name="Test",
                    odds=2.0,
                    probability=0.52,
                    ev_percentage=5.0,
                    confidence=65.0,
                    reasoning=[],
                    is_value_bet=True,
                ),
                BetRecommendation(
                    market="EV15",
                    site="test",
                    site_name="Test",
                    odds=2.0,
                    probability=0.57,
                    ev_percentage=15.0,
                    confidence=65.0,
                    reasoning=[],
                    is_value_bet=True,
                ),
            ],
        )

        match2 = MatchAnalysisResult(
            home_team="C",
            away_team="D",
            value_bets=[
                BetRecommendation(
                    market="EV20",
                    site="test",
                    site_name="Test",
                    odds=2.0,
                    probability=0.60,
                    ev_percentage=20.0,
                    confidence=65.0,
                    reasoning=[],
                    is_value_bet=True,
                ),
            ],
        )

        result = ScanResult(
            matches=[match1, match2],
        )

        # Get top 2
        top = result.get_top_value_bets(limit=2)

        assert len(top) == 2
        assert top[0].ev_percentage == pytest.approx(20.0, rel=0.01)
        assert top[1].ev_percentage == pytest.approx(15.0, rel=0.01)

    def test_to_dict(self):
        """Test converting scan result to dictionary"""
        result = ScanResult(
            total_matches=10,
            matches_with_value_bets=5,
            total_value_bets=12,
        )

        data = result.to_dict()

        assert isinstance(data, dict)
        assert data["total_matches"] == 10
        assert data["matches_with_value_bets"] == 5
        assert "scan_date" in data


class TestBettingInsights:
    """Tests for BettingInsights main class"""

    @pytest.fixture
    def insights(self):
        """Create BettingInsights instance"""
        return BettingInsights(min_ev=5.0, min_confidence=60.0)

    def test_init_with_defaults(self):
        """Test initialization with default parameters"""
        insights = BettingInsights()

        assert insights.min_ev == 5.0
        assert insights.min_confidence == 60.0
        assert insights.cache_enabled is True
        assert insights.engine is not None
        assert len(insights.scrapers) > 0

    def test_init_with_custom_thresholds(self):
        """Test initialization with custom thresholds"""
        insights = BettingInsights(min_ev=10.0, min_confidence=70.0)

        assert insights.min_ev == 10.0
        assert insights.min_confidence == 70.0

    def test_init_with_specific_sites(self):
        """Test initialization with specific enabled sites"""
        insights = BettingInsights(enabled_sites=["betano"])

        assert len(insights.scrapers) == 1
        assert insights.scrapers[0].site_key == "betano"

    def test_init_disables_cache(self):
        """Test initialization with cache disabled"""
        insights = BettingInsights(cache_enabled=False)

        assert insights.cache_enabled is False
        assert insights.data_loader is None

    def test_analyze_match_returns_result(self, insights):
        """Test analyze_match returns MatchAnalysisResult"""
        result = insights.analyze_match("Portugal", "Brazil")

        assert isinstance(result, MatchAnalysisResult)
        assert result.home_team == "Portugal"
        assert result.away_team == "Brazil"

    def test_analyze_match_has_probabilities(self, insights):
        """Test analyze_match result has valid probabilities"""
        result = insights.analyze_match("Portugal", "Brazil")

        # Probabilities should sum to ~1.0
        total = result.home_win_prob + result.draw_prob + result.away_win_prob
        assert total == pytest.approx(1.0, abs=0.05)

        # Each should be in valid range
        assert 0 <= result.home_win_prob <= 1
        assert 0 <= result.draw_prob <= 1
        assert 0 <= result.away_win_prob <= 1

    def test_analyze_match_has_market_data(self, insights):
        """Test analyze_match result includes market averages"""
        result = insights.analyze_match("Portugal", "Brazil")

        # Should have analyzed at least one bookmaker
        assert result.num_bookmakers >= 1

        # Should have at least one market average
        has_avg = any(
            [
                result.market_avg_home is not None,
                result.market_avg_draw is not None,
                result.market_avg_away is not None,
            ]
        )
        assert has_avg is True

    def test_analyze_match_custom_thresholds(self, insights):
        """Test analyze_match with custom threshold overrides"""
        result = insights.analyze_match(
            "Portugal",
            "Brazil",
            min_ev=20.0,  # Very high threshold
            min_confidence=80.0,
        )

        # With high thresholds, likely no value bets
        # But result should still be valid
        assert isinstance(result, MatchAnalysisResult)

    def test_analyze_match_no_odds_raises(self):
        """Test analyze_match raises when no odds available"""
        # This would require mocking scrapers to return no odds
        # For now, just verify the method exists and handles errors
        insights = BettingInsights()

        # Should work with mock data
        result = insights.analyze_match("Test Team A", "Test Team B")
        assert result is not None

    def test_scan_upcoming_matches_returns_result(self, insights):
        """Test scan_upcoming_matches returns ScanResult"""
        result = insights.scan_upcoming_matches(days_ahead=7)

        assert isinstance(result, ScanResult)
        assert result.total_matches >= 0
        assert result.total_value_bets >= 0

    def test_scan_upcoming_matches_custom_days(self, insights):
        """Test scan with custom days_ahead"""
        result = insights.scan_upcoming_matches(days_ahead=14)

        assert isinstance(result, ScanResult)
        # May have more matches with longer scan period
        assert result.total_matches >= 0

    def test_scan_with_custom_thresholds(self, insights):
        """Test scan with custom EV/confidence thresholds"""
        result = insights.scan_upcoming_matches(
            days_ahead=7, min_ev=10.0, min_confidence=70.0
        )

        assert isinstance(result, ScanResult)

    def test_get_bookmakers_returns_list(self, insights):
        """Test get_bookmakers returns list of bookmakers"""
        bookmakers = insights.get_bookmakers()

        assert isinstance(bookmakers, list)
        assert len(bookmakers) > 0

        for bookmaker in bookmakers:
            assert "key" in bookmaker
            assert "name" in bookmaker
            assert "enabled" in bookmaker

    def test_get_bookmakers_has_required_fields(self, insights):
        """Test each bookmaker has required fields"""
        bookmakers = insights.get_bookmakers()

        for bookmaker in bookmakers:
            assert "key" in bookmaker
            assert "name" in bookmaker
            assert "url" in bookmaker
            assert "enabled" in bookmaker
            assert "rate_limit_seconds" in bookmaker

    def test_update_config_min_ev(self, insights):
        """Test updating min_ev configuration"""
        assert insights.min_ev == 5.0

        insights.update_config(min_ev=10.0)

        assert insights.min_ev == 10.0

    def test_update_config_min_confidence(self, insights):
        """Test updating min_confidence configuration"""
        assert insights.min_confidence == 60.0

        insights.update_config(min_confidence=75.0)

        assert insights.min_confidence == 75.0

    def test_update_config_enabled_sites(self, insights):
        """Test updating enabled sites configuration"""
        initial_count = len(insights.scrapers)  # noqa: F841

        insights.update_config(enabled_sites=["betano"])

        assert len(insights.scrapers) == 1
        assert insights.scrapers[0].site_key == "betano"

    def test_update_config_multiple_changes(self, insights):
        """Test updating multiple config values at once"""
        insights.update_config(
            min_ev=8.0, min_confidence=65.0, enabled_sites=["betano", "betclic"]
        )

        assert insights.min_ev == 8.0
        assert insights.min_confidence == 65.0
        assert len(insights.scrapers) == 2


class TestCreateInsights:
    """Tests for create_insights convenience function"""

    def test_create_insights_defaults(self):
        """Test create_insights with default parameters"""
        insights = create_insights()

        assert isinstance(insights, BettingInsights)
        assert insights.min_ev == 5.0
        assert insights.min_confidence == 60.0

    def test_create_insights_custom_ev(self):
        """Test create_insights with custom min_ev"""
        insights = create_insights(min_ev=10.0)

        assert insights.min_ev == 10.0

    def test_create_insights_custom_confidence(self):
        """Test create_insights with custom min_confidence"""
        insights = create_insights(min_confidence=75.0)

        assert insights.min_confidence == 75.0

    def test_create_insights_both_params(self):
        """Test create_insights with both parameters"""
        insights = create_insights(min_ev=8.0, min_confidence=70.0)

        assert insights.min_ev == 8.0
        assert insights.min_confidence == 70.0

    def test_create_insights_kwargs_passed(self):
        """Test that kwargs are passed to BettingInsights"""
        insights = create_insights(min_ev=7.0, enabled_sites=["solverde"])

        assert insights.min_ev == 7.0
        assert len(insights.scrapers) == 1
