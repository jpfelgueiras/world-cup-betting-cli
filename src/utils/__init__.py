"""Utilities package"""
from .ev_calculator import (
    calculate_ev,
    calculate_implied_probability,
    calculate_market_average,
    calculate_odds_discrepancy,
    is_value_bet,
    analyze_bet,
    find_best_value_bets,
    format_ev_display,
    BetRecommendation,
)

__all__ = [
    'calculate_ev',
    'calculate_implied_probability',
    'calculate_market_average',
    'calculate_odds_discrepancy',
    'is_value_bet',
    'analyze_bet',
    'find_best_value_bets',
    'format_ev_display',
    'BetRecommendation',
]
