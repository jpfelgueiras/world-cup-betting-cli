"""
Prediction Engine - Generates match outcome probabilities

Uses statistical modeling based on:
- Team strength (ELO, FIFA rankings)
- Recent form
- Head-to-head history
- Advanced metrics (xG, possession)
- Tournament context
"""

import numpy as np
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .team_stats import TeamStats, TeamData, MatchContext


@dataclass
class MatchPrediction:
    """Result of a match prediction"""
    home_team: str
    away_team: str

    # Probabilities (must sum to ~1.0)
    home_win_prob: float
    draw_prob: float
    away_win_prob: float

    # Confidence levels
    home_confidence: float
    draw_confidence: float
    away_confidence: float

    # Additional predictions
    over_2_5_prob: float
    btts_prob: float  # Both teams to score

    # Reasoning
    key_factors: List[str]

    @property
    def most_likely_outcome(self) -> str:
        """Return the most likely outcome"""
        outcomes = [
            ("home", self.home_win_prob),
            ("draw", self.draw_prob),
            ("away", self.away_win_prob),
        ]
        return max(outcomes, key=lambda x: x[1])[0]

    def get_probability(self, outcome: str) -> float:
        """Get probability for a specific outcome"""
        if outcome.lower() == "home" or outcome.lower() == "1":
            return self.home_win_prob
        elif outcome.lower() == "draw" or outcome.lower() == "x":
            return self.draw_prob
        elif outcome.lower() == "away" or outcome.lower() == "2":
            return self.away_win_prob
        elif outcome.lower() == "over_2_5":
            return self.over_2_5_prob
        elif outcome.lower() == "btts" or outcome.lower() == "gg":
            return self.btts_prob
        return 0.0

    def get_confidence(self, outcome: str) -> float:
        """Get confidence for a specific outcome"""
        if outcome.lower() in ["home", "1"]:
            return self.home_confidence
        elif outcome.lower() in ["draw", "x"]:
            return self.draw_confidence
        elif outcome.lower() in ["away", "2"]:
            return self.away_confidence
        # Default confidence for other markets
        return 65.0


class PredictionEngine:
    """
    Main prediction engine for match outcomes.

    Uses a combination of:
    - Poisson distribution for goal modeling
    - ELO-based strength calculations
    - Form-weighted adjustments
    - Head-to-head factors
    """

    def __init__(self):
        # Model weights (can be tuned based on backtesting)
        self.weights = {
            'elo': 0.30,
            'form': 0.25,
            'h2h': 0.15,
            'attack_defense': 0.20,
            'context': 0.10,
        }

        # Home advantage factor (in World Cup, varies by venue)
        self.default_home_advantage = 3.0  # Goals per 100 matches

    def predict_match(
        self,
        home_team: TeamData,
        away_team: TeamData,
        context: Optional[MatchContext] = None
    ) -> MatchPrediction:
        """
        Generate comprehensive match prediction.

        Returns MatchPrediction with probabilities and confidence levels.
        """
        # Compute team stats
        home_stats = TeamStats(home_team)
        away_stats = TeamStats(away_team)

        # Calculate expected goals using Poisson model
        home_xg, away_xg = self._calculate_expected_goals(
            home_stats, away_stats, context
        )

        # Convert to win/draw/loss probabilities
        home_win, draw, away_win = self._poisson_to_probabilities(
            home_xg, away_xg
        )

        # Adjust for context (must-win, rest days, etc.)
        if context:
            home_win, draw, away_win = self._apply_context_adjustments(
                home_win, draw, away_win, home_stats, away_stats, context
            )

        # Normalize probabilities
        total = home_win + draw + away_win
        home_win /= total
        draw /= total
        away_win /= total

        # Calculate over 2.5 and BTTS probabilities
        over_2_5 = self._calculate_over_2_5_probability(home_xg, away_xg)
        btts = self._calculate_btts_probability(home_xg, away_xg)

        # Calculate confidence levels
        home_conf, draw_conf, away_conf = self._calculate_confidence(
            home_stats, away_stats, [home_win, draw, away_win]
        )

        # Generate reasoning
        key_factors = self._generate_reasoning(
            home_stats, away_stats, home_xg, away_xg,
            home_win, draw, away_win
        )

        return MatchPrediction(
            home_team=home_team.name,
            away_team=away_team.name,
            home_win_prob=home_win,
            draw_prob=draw,
            away_win_prob=away_win,
            home_confidence=home_conf,
            draw_confidence=draw_conf,
            away_confidence=away_conf,
            over_2_5_prob=over_2_5,
            btts_prob=btts,
            key_factors=key_factors,
        )

    def _calculate_expected_goals(
        self,
        home_stats: TeamStats,
        away_stats: TeamStats,
        context: Optional[MatchContext]
    ) -> Tuple[float, float]:
        """
        Calculate expected goals for each team using strength metrics.
        """
        home = home_stats.team_data
        away = away_stats.team_data

        # Base expected goals from attack/defense strengths
        base_home_xg = (
            home_stats.attack_strength * 0.015 +
            (100 - away_stats.defense_strength) * 0.010
        )

        base_away_xg = (
            away_stats.attack_strength * 0.012 +
            (100 - home_stats.defense_strength) * 0.008
        )

        # Apply form factor
        form_adjustment_home = (home_stats.form_factor - 50) * 0.005
        form_adjustment_away = (away_stats.form_factor - 50) * 0.004

        # H2H adjustment
        h2h_advantage_home = home_stats.get_h2h_advantage(away_stats)
        h2h_xg_adjustment = h2h_advantage_home * 0.003

        # Combine all factors
        home_xg = base_home_xg + form_adjustment_home + h2h_xg_adjustment
        away_xg = base_away_xg + form_adjustment_away - h2h_xg_adjustment

        # Apply home advantage if applicable
        if context and context.venue != "Neutral":
            home_xg += self.default_home_advantage / 100

        # Ensure reasonable bounds
        home_xg = max(0.3, min(4.0, home_xg))
        away_xg = max(0.3, min(4.0, away_xg))

        return home_xg, away_xg

    def _poisson_to_probabilities(
        self,
        home_xg: float,
        away_xg: float
    ) -> Tuple[float, float, float]:
        """
        Convert expected goals to win/draw/loss probabilities using Poisson distribution.
        """
        # Calculate probability matrix for all scorelines up to 5-5
        max_goals = 6
        probs = np.zeros((max_goals, max_goals))

        for home_goals in range(max_goals):
            for away_goals in range(max_goals):
                # Poisson probability for this scoreline
                home_prob = self._poisson_pmf(home_goals, home_xg)
                away_prob = self._poisson_pmf(away_goals, away_xg)
                probs[home_goals, away_goals] = home_prob * away_prob

        # Sum probabilities for each outcome
        home_win = 0.0
        draw = 0.0
        away_win = 0.0

        for home_goals in range(max_goals):
            for away_goals in range(max_goals):
                prob = probs[home_goals, away_goals]
                if home_goals > away_goals:
                    home_win += prob
                elif home_goals == away_goals:
                    draw += prob
                else:
                    away_win += prob

        return home_win, draw, away_win

    def _poisson_pmf(self, k: int, lam: float) -> float:
        """Poisson probability mass function"""
        if k < 0:
            return 0.0
        return (np.exp(-lam) * (lam ** k)) / math.factorial(k)

    def _calculate_over_2_5_probability(
        self,
        home_xg: float,
        away_xg: float
    ) -> float:
        """Calculate probability of over 2.5 goals"""
        total_xg = home_xg + away_xg

        # Use Poisson cumulative distribution
        prob_under = 0.0
        for total_goals in range(3):  # 0, 1, 2 goals
            prob_under += self._poisson_pmf(total_goals, total_xg)

        return 1.0 - prob_under

    def _calculate_btts_probability(
        self,
        home_xg: float,
        away_xg: float
    ) -> float:
        """Calculate probability of both teams scoring"""
        # P(home scores) = 1 - P(home scores 0)
        prob_home_scores = 1 - self._poisson_pmf(0, home_xg)
        prob_away_scores = 1 - self._poisson_pmf(0, away_xg)

        # Assuming independence (simplification)
        return prob_home_scores * prob_away_scores

    def _apply_context_adjustments(
        self,
        home_win: float,
        draw: float,
        away_win: float,
        home_stats: TeamStats,
        away_stats: TeamStats,
        context: MatchContext
    ) -> Tuple[float, float, float]:
        """Apply tournament context adjustments"""
        adjustment = 0.0

        # Must-win situations
        if context.is_must_win_home and not context.is_must_win_away:
            adjustment += 0.05  # 5% boost to home win
        elif context.is_must_win_away and not context.is_must_win_home:
            adjustment -= 0.05  # 5% boost to away win

        # Rest days advantage
        rest_diff = home_stats.team_data.rest_days - away_stats.team_data.rest_days
        if rest_diff > 2:
            adjustment += 0.03
        elif rest_diff < -2:
            adjustment -= 0.03

        # Key players missing
        home_missing = len(home_stats.team_data.key_players_out)
        away_missing = len(away_stats.team_data.key_players_out)

        if home_missing > away_missing:
            adjustment -= 0.02 * (home_missing - away_missing)
        elif away_missing > home_missing:
            adjustment += 0.02 * (away_missing - home_missing)

        # Apply adjustments
        home_win += adjustment
        away_win -= adjustment

        # Keep in valid range
        home_win = max(0.05, min(0.90, home_win))
        away_win = max(0.05, min(0.90, away_win))

        return home_win, draw, away_win

    def _calculate_confidence(
        self,
        home_stats: TeamStats,
        away_stats: TeamStats,
        probs: List[float]
    ) -> Tuple[float, float, float]:
        """
        Calculate confidence levels for each outcome.

        Based on:
        - Data quality (sample size, variance)
        - Strength differential
        - Form consistency
        """
        # Base confidence from prediction clarity
        max_prob = max(probs)
        base_confidence = 50 + (max_prob * 40)  # 50-90 range

        # Adjust for strength differential
        strength_diff = abs(
            home_stats.overall_strength - away_stats.overall_strength
        )
        diff_bonus = min(10, strength_diff / 5)

        # Adjust for form consistency
        form_variance = abs(
            home_stats.form_factor - away_stats.form_factor
        )
        form_bonus = min(5, form_variance / 10)

        final_confidence = min(95, base_confidence + diff_bonus + form_bonus)

        # Distribute confidence across outcomes
        home_conf = final_confidence * (probs[0] / max(probs))
        draw_conf = final_confidence * (probs[1] / max(probs)) * 0.8  # Draw harder to predict
        away_conf = final_confidence * (probs[2] / max(probs))

        return (
            max(30, min(95, home_conf)),
            max(30, min(85, draw_conf)),
            max(30, min(95, away_conf)),
        )

    def _generate_reasoning(
        self,
        home_stats: TeamStats,
        away_stats: TeamStats,
        home_xg: float,
        away_xg: float,
        home_win: float,
        draw: float,
        away_win: float
    ) -> List[str]:
        """Generate human-readable reasoning for the prediction"""
        factors = []

        home = home_stats.team_data
        away = away_stats.team_data

        # Form analysis
        if home.form_percentage > 70:
            factors.append(f"{home.name} in excellent form ({home.form_percentage:.0f}% last 10)")
        elif away.form_percentage > 70:
            factors.append(f"{away.name} in excellent form ({away.form_percentage:.0f}% last 10)")

        # Strength comparison
        if home_stats.overall_strength > away_stats.overall_strength + 10:
            factors.append(f"{home.name} has superior overall strength")
        elif away_stats.overall_strength > home_stats.overall_strength + 10:
            factors.append(f"{away.name} has superior overall strength")

        # H2H history
        if home.h2h_wins > home.h2h_losses + 2:
            factors.append(f"{home.name} dominates historical H2H ({home.h2h_wins}W-{home.h2h_draws}D-{home.h2h_losses}L)")
        elif away.h2h_wins > away.h2h_losses + 2:
            factors.append(f"{away.name} dominates historical H2H")

        # Goal expectations
        total_xg = home_xg + away_xg
        if total_xg > 2.8:
            factors.append(f"High-scoring match expected ({total_xg:.1f} xG total)")
        elif total_xg < 1.8:
            factors.append(f"Low-scoring match expected ({total_xg:.1f} xG total)")

        # Key players
        if home.key_players_out:
            factors.append(f"{home.name} missing: {', '.join(home.key_players_out[:2])}")
        if away.key_players_out:
            factors.append(f"{away.name} missing: {', '.join(away.key_players_out[:2])}")

        # Attack vs defense mismatch
        if home_stats.attack_strength > away_stats.defense_strength + 15:
            factors.append(f"{home.name}'s attack vs {away.name}'s vulnerable defense")
        elif away_stats.attack_strength > home_stats.defense_strength + 15:
            factors.append(f"{away.name}'s attack vs {home.name}'s vulnerable defense")

        return factors[:5]  # Limit to top 5 factors
