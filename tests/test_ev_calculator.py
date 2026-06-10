"""
Unit tests for EV Calculator utilities

Tests all functions in src/utils/ev_calculator.py
"""

import pytest
import numpy as np

from src.utils.ev_calculator import (
    calculate_ev,
    calculate_implied_probability,
    calculate_market_average,
    calculate_odds_discrepancy,
    is_value_bet,
    analyze_bet,
    find_best_value_bets,
    format_ev_display,
    calculate_confidence_from_variance,
    BetRecommendation,
)


class TestCalculateEV:
    """Tests for calculate_ev function"""
    
    def test_positive_ev(self):
        """Test positive expected value calculation"""
        # EV = (0.50 × 2.20) - 1 = 0.10 = 10%
        ev = calculate_ev(probability=0.50, decimal_odds=2.20)
        assert ev == pytest.approx(10.0, rel=0.01)
    
    def test_negative_ev(self):
        """Test negative expected value calculation"""
        # EV = (0.40 × 2.00) - 1 = -0.20 = -20%
        ev = calculate_ev(probability=0.40, decimal_odds=2.00)
        assert ev == pytest.approx(-20.0, rel=0.01)
    
    def test_zero_ev(self):
        """Test break-even EV (zero)"""
        # EV = (0.50 × 2.00) - 1 = 0 = 0%
        ev = calculate_ev(probability=0.50, decimal_odds=2.00)
        assert ev == pytest.approx(0.0, rel=0.01)
    
    def test_high_probability_low_odds(self):
        """Test high probability with low odds"""
        # EV = (0.80 × 1.30) - 1 = 0.04 = 4%
        ev = calculate_ev(probability=0.80, decimal_odds=1.30)
        assert ev == pytest.approx(4.0, rel=0.01)
    
    def test_edge_case_probability_1(self):
        """Test with probability = 1 (certainty)"""
        ev = calculate_ev(probability=1.0, decimal_odds=1.50)
        assert ev == pytest.approx(50.0, rel=0.01)
    
    def test_edge_case_probability_0(self):
        """Test with probability = 0 (impossible)"""
        ev = calculate_ev(probability=0.0, decimal_odds=10.0)
        assert ev == pytest.approx(-100.0, rel=0.01)


class TestCalculateImpliedProbability:
    """Tests for calculate_implied_probability function"""
    
    def test_standard_odds(self):
        """Test standard odds conversion"""
        # Implied prob = 1 / 2.00 = 0.50
        prob = calculate_implied_probability(decimal_odds=2.00)
        assert prob == pytest.approx(0.50, rel=0.01)
    
    def test_high_odds(self):
        """Test high odds conversion"""
        # Implied prob = 1 / 4.00 = 0.25
        prob = calculate_implied_probability(decimal_odds=4.00)
        assert prob == pytest.approx(0.25, rel=0.01)
    
    def test_low_odds(self):
        """Test low odds conversion"""
        # Implied prob = 1 / 1.50 = 0.667
        prob = calculate_implied_probability(decimal_odds=1.50)
        assert prob == pytest.approx(0.667, rel=0.01)
    
    def test_invalid_odds_below_1(self):
        """Test odds below 1.0 returns 1.0"""
        prob = calculate_implied_probability(decimal_odds=0.50)
        assert prob == 1.0
    
    def test_invalid_odds_equal_1(self):
        """Test odds equal to 1.0 returns 1.0"""
        prob = calculate_implied_probability(decimal_odds=1.0)
        assert prob == 1.0


class TestCalculateMarketAverage:
    """Tests for calculate_market_average function"""
    
    def test_simple_average(self):
        """Test simple average calculation"""
        odds = [2.00, 2.10, 2.05]
        avg = calculate_market_average(odds)
        assert avg == pytest.approx(2.05, rel=0.01)
    
    def test_single_value(self):
        """Test with single value"""
        odds = [2.50]
        avg = calculate_market_average(odds)
        assert avg == pytest.approx(2.50, rel=0.01)
    
    def test_empty_list(self):
        """Test with empty list returns 0"""
        avg = calculate_market_average([])
        assert avg == 0.0
    
    def test_two_values(self):
        """Test with two values"""
        odds = [1.80, 2.20]
        avg = calculate_market_average(odds)
        assert avg == pytest.approx(2.00, rel=0.01)


class TestCalculateOddsDiscrepancy:
    """Tests for calculate_odds_discrepancy function"""
    
    def test_better_than_market(self):
        """Test odds better than market average"""
        discrepancy = calculate_odds_discrepancy(site_odds=2.20, market_average=2.00)
        assert discrepancy == pytest.approx(10.0, rel=0.01)
    
    def test_worse_than_market(self):
        """Test odds worse than market average"""
        discrepancy = calculate_odds_discrepancy(site_odds=1.80, market_average=2.00)
        assert discrepancy == pytest.approx(-10.0, rel=0.01)
    
    def test_equal_to_market(self):
        """Test odds equal to market average"""
        discrepancy = calculate_odds_discrepancy(site_odds=2.00, market_average=2.00)
        assert discrepancy == pytest.approx(0.0, rel=0.01)
    
    def test_zero_market_average(self):
        """Test with zero market average returns 0"""
        discrepancy = calculate_odds_discrepancy(site_odds=2.00, market_average=0.0)
        assert discrepancy == 0.0


class TestIsValueBet:
    """Tests for is_value_bet function"""
    
    def test_qualifies_as_value_bet(self):
        """Test bet that qualifies as value bet"""
        result = is_value_bet(ev_percentage=8.0, confidence=70.0)
        assert result is True
    
    def test_ev_too_low(self):
        """Test bet with EV below threshold"""
        result = is_value_bet(ev_percentage=3.0, confidence=70.0)
        assert result is False
    
    def test_confidence_too_low(self):
        """Test bet with confidence below threshold"""
        result = is_value_bet(ev_percentage=8.0, confidence=50.0)
        assert result is False
    
    def test_both_below_threshold(self):
        """Test bet with both metrics below threshold"""
        result = is_value_bet(ev_percentage=3.0, confidence=50.0)
        assert result is False
    
    def test_custom_thresholds(self):
        """Test with custom thresholds"""
        result = is_value_bet(
            ev_percentage=6.0,
            confidence=65.0,
            min_ev=5.0,
            min_confidence=60.0
        )
        assert result is True
    
    def test_exactly_at_threshold(self):
        """Test values exactly at threshold (should not qualify, needs to be >)"""
        result = is_value_bet(ev_percentage=5.0, confidence=60.0)
        assert result is False  # Must be GREATER than threshold


class TestAnalyzeBet:
    """Tests for analyze_bet function"""
    
    def test_analyze_value_bet(self):
        """Test analyzing a value bet"""
        rec = analyze_bet(
            market="1X2 - Home Win",
            site="betano",
            site_name="Betano.pt",
            odds=2.25,
            model_probability=0.48,
            confidence=72.0,
            reasoning=["Team in good form"],
            min_ev=5.0,
            min_confidence=60.0
        )
        
        assert rec.market == "1X2 - Home Win"
        assert rec.site == "betano"
        assert rec.odds == 2.25
        assert rec.probability == 0.48
        assert rec.confidence == 72.0
        assert rec.is_value_bet is True
        # EV = (0.48 × 2.25) - 1 = 0.08 = 8.0%
        assert rec.ev_percentage == pytest.approx(8.0, rel=0.1)
    
    def test_analyze_non_value_bet(self):
        """Test analyzing a non-value bet"""
        rec = analyze_bet(
            market="1X2 - Away Win",
            site="betclic",
            site_name="Betclic.pt",
            odds=1.80,
            model_probability=0.45,
            confidence=65.0,
            reasoning=[],
            min_ev=5.0,
            min_confidence=60.0
        )
        
        assert rec.is_value_bet is False
        # EV = (0.45 × 1.80) - 1 = -0.19 = -19%
        assert rec.ev_percentage == pytest.approx(-19.0, rel=0.1)
    
    def test_analyze_with_custom_thresholds(self):
        """Test analysis with custom thresholds"""
        rec = analyze_bet(
            market="Over 2.5",
            site="solverde",
            site_name="Solverde.pt",
            odds=1.95,
            model_probability=0.55,
            confidence=68.0,
            reasoning=["High scoring teams"],
            min_ev=3.0,
            min_confidence=65.0
        )
        
        # EV = (0.55 × 1.95) - 1 = 0.0725 = 7.25%
        assert rec.ev_percentage == pytest.approx(7.25, rel=0.1)
        assert rec.is_value_bet is True  # Meets custom thresholds


class TestFindBestValueBets:
    """Tests for find_best_value_bets function"""
    
    def test_filter_and_sort(self):
        """Test filtering and sorting value bets"""
        recommendations = [
            BetRecommendation(
                market="Home Win", site="betano", site_name="Betano.pt",
                odds=2.00, probability=0.55, ev_percentage=10.0,
                confidence=70.0, reasoning=[], is_value_bet=True
            ),
            BetRecommendation(
                market="Away Win", site="betclic", site_name="Betclic.pt",
                odds=1.80, probability=0.45, ev_percentage=-19.0,
                confidence=65.0, reasoning=[], is_value_bet=False
            ),
            BetRecommendation(
                market="Draw", site="solverde", site_name="Solverde.pt",
                odds=3.50, probability=0.32, ev_percentage=12.0,
                confidence=62.0, reasoning=[], is_value_bet=True
            ),
        ]
        
        value_bets = find_best_value_bets(recommendations, min_ev=5.0, min_confidence=60.0)
        
        # Should return 2 value bets, sorted by EV descending
        assert len(value_bets) == 2
        assert value_bets[0].ev_percentage == pytest.approx(12.0, rel=0.1)
        assert value_bets[1].ev_percentage == pytest.approx(10.0, rel=0.1)
    
    def test_no_value_bets(self):
        """Test when no bets qualify"""
        recommendations = [
            BetRecommendation(
                market="Home Win", site="betano", site_name="Betano.pt",
                odds=1.50, probability=0.40, ev_percentage=-40.0,
                confidence=50.0, reasoning=[], is_value_bet=False
            ),
        ]
        
        value_bets = find_best_value_bets(recommendations)
        assert len(value_bets) == 0
    
    def test_empty_list(self):
        """Test with empty recommendations list"""
        value_bets = find_best_value_bets([])
        assert len(value_bets) == 0


class TestFormatEvDisplay:
    """Tests for format_ev_display function"""
    
    def test_high_positive_ev(self):
        """Test formatting high positive EV"""
        result = format_ev_display(15.5)
        assert result == "+15.5%"
    
    def test_moderate_positive_ev(self):
        """Test formatting moderate positive EV"""
        result = format_ev_display(7.3)
        assert result == "+7.3%"
    
    def test_low_positive_ev(self):
        """Test formatting low positive EV"""
        result = format_ev_display(2.1)
        assert result == "+2.1%"
    
    def test_negative_ev(self):
        """Test formatting negative EV"""
        result = format_ev_display(-5.5)
        assert result == "-5.5%"
    
    def test_zero_ev(self):
        """Test formatting zero EV"""
        result = format_ev_display(0.0)
        assert result == "+0.0%"


class TestCalculateConfidenceFromVariance:
    """Tests for calculate_confidence_from_variance function"""
    
    def test_low_variance_large_sample(self):
        """Test low variance with large sample size = high confidence"""
        predictions = [0.50, 0.51, 0.49, 0.50, 0.51, 0.50, 0.49, 0.50, 0.51, 0.50]
        confidence = calculate_confidence_from_variance(predictions, sample_size=100)
        assert confidence > 45  # Should be moderate-high confidence (variance is very low)
    
    def test_high_variance_small_sample(self):
        """Test high variance with small sample = low confidence"""
        predictions = [0.20, 0.80, 0.15, 0.85, 0.30]
        confidence = calculate_confidence_from_variance(predictions, sample_size=5)
        assert confidence < 50  # Should be low confidence
    
    def test_insufficient_data(self):
        """Test with insufficient data (less than 2 predictions)"""
        predictions = [0.50]
        confidence = calculate_confidence_from_variance(predictions, sample_size=1)
        assert confidence == 50.0  # Default confidence
    
    def test_medium_variance_medium_sample(self):
        """Test medium variance with medium sample"""
        predictions = [0.45, 0.55, 0.50, 0.48, 0.52, 0.50, 0.51, 0.49]
        confidence = calculate_confidence_from_variance(predictions, sample_size=50)
        assert 40 < confidence < 70  # Should be moderate confidence


class TestBetRecommendationDataclass:
    """Tests for BetRecommendation dataclass"""
    
    def test_create_recommendation(self):
        """Test creating a BetRecommendation instance"""
        rec = BetRecommendation(
            market="1X2",
            site="betano",
            site_name="Betano.pt",
            odds=2.25,
            probability=0.48,
            ev_percentage=8.0,
            confidence=70.0,
            reasoning=["Good form", "H2H advantage"],
            is_value_bet=True
        )
        
        assert rec.market == "1X2"
        assert rec.site == "betano"
        assert len(rec.reasoning) == 2
        assert rec.is_value_bet is True
    
    def test_default_is_value_bet(self):
        """Test default value for is_value_bet"""
        rec = BetRecommendation(
            market="Test",
            site="test",
            site_name="Test Site",
            odds=2.00,
            probability=0.50,
            ev_percentage=0.0,
            confidence=50.0,
            reasoning=[]
        )
        
        assert rec.is_value_bet is True  # Default is True
