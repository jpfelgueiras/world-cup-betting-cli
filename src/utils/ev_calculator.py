"""
Expected Value (EV) Calculator and utilities
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class BetRecommendation:
    """Represents a betting recommendation with EV analysis"""
    market: str
    site: str
    site_name: str
    odds: float
    probability: float
    ev_percentage: float
    confidence: float
    reasoning: List[str]
    is_value_bet: bool = True


def calculate_ev(probability: float, decimal_odds: float) -> float:
    """
    Calculate Expected Value (EV) for a bet.
    
    EV = (Probability × Decimal Odds) - 1
    
    Returns EV as a percentage (e.g., 0.085 = 8.5%)
    """
    ev = (probability * decimal_odds) - 1
    return ev * 100  # Return as percentage


def calculate_implied_probability(decimal_odds: float) -> float:
    """
    Calculate implied probability from decimal odds.
    
    Implied Probability = 1 / Decimal Odds
    """
    if decimal_odds <= 1.0:
        return 1.0
    return 1.0 / decimal_odds


def calculate_market_average(odds_list: List[float]) -> float:
    """Calculate average odds across multiple bookmakers"""
    if not odds_list:
        return 0.0
    return sum(odds_list) / len(odds_list)


def calculate_odds_discrepancy(site_odds: float, market_average: float) -> float:
    """
    Calculate percentage discrepancy between site odds and market average.
    
    Positive = site offers better odds than average
    """
    if market_average == 0:
        return 0.0
    return ((site_odds - market_average) / market_average) * 100


def is_value_bet(
    ev_percentage: float,
    confidence: float,
    min_ev: float = 5.0,
    min_confidence: float = 60.0
) -> bool:
    """
    Determine if a bet qualifies as a value bet.
    
    Criteria:
    - EV > minimum threshold (default 5%)
    - Confidence > minimum threshold (default 60%)
    """
    return ev_percentage > min_ev and confidence > min_confidence


def analyze_bet(
    market: str,
    site: str,
    site_name: str,
    odds: float,
    model_probability: float,
    confidence: float,
    reasoning: List[str],
    min_ev: float = 5.0,
    min_confidence: float = 60.0
) -> BetRecommendation:
    """
    Perform complete EV analysis for a single bet.
    
    Returns a BetRecommendation with all calculated metrics.
    """
    ev_percentage = calculate_ev(model_probability, odds)
    is_value = is_value_bet(ev_percentage, confidence, min_ev, min_confidence)
    
    return BetRecommendation(
        market=market,
        site=site,
        site_name=site_name,
        odds=odds,
        probability=model_probability,
        ev_percentage=ev_percentage,
        confidence=confidence,
        reasoning=reasoning,
        is_value_bet=is_value
    )


def find_best_value_bets(
    recommendations: List[BetRecommendation],
    min_ev: float = 5.0,
    min_confidence: float = 60.0
) -> List[BetRecommendation]:
    """
    Filter and sort recommendations by EV (highest first).
    
    Only returns bets that meet the value criteria.
    """
    value_bets = [
        rec for rec in recommendations
        if is_value_bet(rec.ev_percentage, rec.confidence, min_ev, min_confidence)
    ]
    
    # Sort by EV descending
    return sorted(value_bets, key=lambda x: x.ev_percentage, reverse=True)


def format_ev_display(ev_percentage: float) -> str:
    """Format EV percentage for display with color indicator"""
    if ev_percentage >= 10:
        return f"+{ev_percentage:.1f}%"  # High value
    elif ev_percentage >= 5:
        return f"+{ev_percentage:.1f}%"  # Good value
    elif ev_percentage >= 0:
        return f"+{ev_percentage:.1f}%"  # Slight value
    else:
        return f"{ev_percentage:.1f}%"  # Negative value


def calculate_confidence_from_variance(
    predictions: List[float],
    sample_size: int
) -> float:
    """
    Calculate model confidence based on prediction variance and sample size.
    
    Lower variance + larger sample = higher confidence
    
    Returns confidence as percentage (0-100)
    """
    import numpy as np
    
    if len(predictions) < 2:
        return 50.0  # Default confidence with insufficient data
    
    variance = np.var(predictions)
    std_dev = np.std(predictions)
    
    # Base confidence from sample size (logarithmic scaling)
    size_factor = min(100, 30 + (10 * np.log10(max(1, sample_size))))
    
    # Reduce confidence based on variance (higher variance = lower confidence)
    variance_penalty = min(40, std_dev * 100)
    
    confidence = max(0, min(100, size_factor - variance_penalty))
    return confidence
