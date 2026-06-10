"""
Unit tests for Prediction Engine

Tests all functions in src/predictors/prediction_engine.py and team_stats.py
"""

import pytest
from datetime import datetime, timedelta

from src.predictors.prediction_engine import PredictionEngine, MatchPrediction
from src.predictors.team_stats import TeamData, TeamStats, MatchContext


class TestTeamData:
    """Tests for TeamData dataclass"""

    def test_create_team_data(self):
        """Test creating TeamData instance"""
        team = TeamData(
            name="Portugal",
            country_code="PT",
            fifa_ranking=8,
            elo_rating=1750,
            matches_played=10,
            wins=7,
            draws=2,
            losses=1,
        )

        assert team.name == "Portugal"
        assert team.fifa_ranking == 8
        assert team.elo_rating == 1750

    def test_form_points_calculation(self):
        """Test form points calculation (3 for win, 1 for draw)"""
        team = TeamData(
            name="Test",
            matches_played=10,
            wins=5,
            draws=3,
            losses=2,
        )

        # 5 wins × 3 + 3 draws × 1 = 18 points
        assert team.form_points == 18

    def test_form_percentage(self):
        """Test form percentage calculation"""
        team = TeamData(
            name="Test",
            matches_played=10,
            wins=5,
            draws=3,
            losses=2,
        )

        # Max points = 10 × 3 = 30
        # Form % = 18 / 30 × 100 = 60%
        assert team.form_percentage == pytest.approx(60.0, rel=0.01)

    def test_form_percentage_no_matches(self):
        """Test form percentage with no matches returns 50%"""
        team = TeamData(name="Test", matches_played=0)
        assert team.form_percentage == 50.0

    def test_goal_difference(self):
        """Test goal difference calculation"""
        team = TeamData(
            name="Test",
            goals_scored=25,
            goals_conceded=12,
        )

        assert team.goal_difference == 13

    def test_avg_goals_scored(self):
        """Test average goals scored per match"""
        team = TeamData(
            name="Test",
            matches_played=10,
            goals_scored=23,
        )

        assert team.avg_goals_scored == pytest.approx(2.3, rel=0.01)

    def test_avg_goals_scored_no_matches(self):
        """Test average goals with no matches"""
        team = TeamData(name="Test", matches_played=0, goals_scored=0)
        assert team.avg_goals_scored == 0.0

    def test_key_players_lists(self):
        """Test key player availability lists"""
        team = TeamData(
            name="Test",
            key_players_available=["Ronaldo", "Silva"],
            key_players_out=["Pepe"],
            injuries=["Costa"],
            suspensions=["Fernandes"],
        )

        assert len(team.key_players_available) == 2
        assert "Ronaldo" in team.key_players_available
        assert len(team.key_players_out) == 1
        assert "Pepe" in team.key_players_out


class TestTeamStats:
    """Tests for TeamStats class"""

    def test_create_team_stats(self):
        """Test creating TeamStats from TeamData"""
        team_data = TeamData(
            name="Portugal",
            fifa_ranking=8,
            elo_rating=1750,
            matches_played=10,
            wins=7,
            draws=2,
            losses=1,
            goals_scored=23,
            goals_conceded=8,
            avg_xg_for=2.1,
            avg_xg_against=0.9,
            clean_sheets=5,
        )

        stats = TeamStats(team_data)

        assert stats.team_data.name == "Portugal"
        assert stats.attack_strength > 0
        assert stats.defense_strength > 0
        assert stats.overall_strength > 0

    def test_attack_strength_computation(self):
        """Test attack strength is computed correctly"""
        team_data = TeamData(
            name="Attack Team",
            fifa_ranking=1,  # Top ranked
            elo_rating=2000,  # High ELO
            matches_played=10,
            goals_scored=35,  # High scoring
            avg_xg_for=2.8,  # High xG
        )

        stats = TeamStats(team_data)

        # Should have high attack strength
        assert stats.attack_strength > 60

    def test_defense_strength_computation(self):
        """Test defense strength is computed correctly"""
        team_data = TeamData(
            name="Defense Team",
            matches_played=10,
            goals_conceded=3,  # Very few conceded
            avg_xg_against=0.4,  # Low xG against
            clean_sheets=8,  # Many clean sheets
        )

        stats = TeamStats(team_data)

        # Should have high defense strength
        assert stats.defense_strength > 70

    def test_overall_strength_weighted_average(self):
        """Test overall strength is weighted average of attack and defense"""
        team_data = TeamData(
            name="Balanced Team",
            fifa_ranking=10,
            elo_rating=1700,
            matches_played=10,
            wins=5,
            draws=3,
            losses=2,
            goals_scored=18,
            goals_conceded=10,
            avg_xg_for=1.8,
            avg_xg_against=1.0,
            clean_sheets=4,
        )

        stats = TeamStats(team_data)

        # Overall should be between attack and defense
        min_strength = min(stats.attack_strength, stats.defense_strength)
        max_strength = max(stats.attack_strength, stats.defense_strength)

        assert min_strength <= stats.overall_strength <= max_strength

    def test_form_factor_calculation(self):
        """Test form factor includes momentum bonus"""
        # Good form team
        good_team = TeamData(
            name="Good Form",
            matches_played=10,
            wins=8,
            draws=1,
            losses=1,
            goals_scored=28,
            goals_conceded=8,
        )

        # Poor form team
        poor_team = TeamData(
            name="Poor Form",
            matches_played=10,
            wins=2,
            draws=2,
            losses=6,
            goals_scored=10,
            goals_conceded=22,
        )

        good_stats = TeamStats(good_team)
        poor_stats = TeamStats(poor_team)

        assert good_stats.form_factor > poor_stats.form_factor

    def test_h2h_advantage_positive(self):
        """Test H2H advantage when team dominates"""
        team_data = TeamData(
            name="Dominant",
            h2h_wins=5,
            h2h_draws=1,
            h2h_losses=1,
        )

        opponent_data = TeamData(
            name="Opponent",
            h2h_wins=1,
            h2h_draws=1,
            h2h_losses=5,
        )

        stats = TeamStats(team_data)
        opponent_stats = TeamStats(opponent_data)

        advantage = stats.get_h2h_advantage(opponent_stats)

        # Should have positive advantage
        assert advantage > 0

    def test_h2h_advantage_negative(self):
        """Test H2H disadvantage when team loses often"""
        team_data = TeamData(
            name="Underdog",
            h2h_wins=1,
            h2h_draws=1,
            h2h_losses=5,
        )

        opponent_data = TeamData(
            name="Favorite",
            h2h_wins=5,
            h2h_draws=1,
            h2h_losses=1,
        )

        stats = TeamStats(team_data)
        opponent_stats = TeamStats(opponent_data)

        disadvantage = stats.get_h2h_advantage(opponent_stats)

        # Should have negative advantage (disadvantage)
        assert disadvantage < 0

    def test_h2h_no_data(self):
        """Test H2H advantage with no historical data"""
        team_data = TeamData(name="Team A")
        opponent_data = TeamData(name="Team B")

        stats = TeamStats(team_data)
        opponent_stats = TeamStats(opponent_data)

        advantage = stats.get_h2h_advantage(opponent_stats)

        # Should return 0 when no H2H data
        assert advantage == 0.0


class TestMatchContext:
    """Tests for MatchContext class"""

    def test_create_match_context(self):
        """Test creating MatchContext"""
        home = TeamData(name="Portugal")
        away = TeamData(name="Brazil")
        match_date = datetime.now() + timedelta(days=5)

        context = MatchContext(
            home_team=home,
            away_team=away,
            match_date=match_date,
            venue="Neutral",
            tournament_stage="Group Stage",
        )

        assert context.home_team.name == "Portugal"
        assert context.away_team.name == "Brazil"
        assert context.tournament_stage == "Group Stage"

    def test_must_win_flags(self):
        """Test must-win scenario flags"""
        home = TeamData(name="Home")
        away = TeamData(name="Away")
        match_date = datetime.now() + timedelta(days=3)

        context = MatchContext(
            home_team=home,
            away_team=away,
            match_date=match_date,
            is_must_win_home=True,
            is_must_win_away=False,
        )

        assert context.is_must_win_home is True
        assert context.is_must_win_away is False


class TestPredictionEngine:
    """Tests for PredictionEngine class"""

    @pytest.fixture
    def engine(self):
        """Create prediction engine instance"""
        return PredictionEngine()

    @pytest.fixture
    def sample_teams(self):
        """Create sample team data for testing"""
        home = TeamData(
            name="Portugal",
            fifa_ranking=8,
            elo_rating=1750,
            matches_played=10,
            wins=7,
            draws=2,
            losses=1,
            goals_scored=23,
            goals_conceded=8,
            avg_xg_for=2.1,
            avg_xg_against=0.9,
            clean_sheets=5,
            rest_days=4,
        )

        away = TeamData(
            name="Brazil",
            fifa_ranking=3,
            elo_rating=1850,
            matches_played=10,
            wins=8,
            draws=2,
            losses=0,
            goals_scored=28,
            goals_conceded=5,
            avg_xg_for=2.5,
            avg_xg_against=0.6,
            clean_sheets=7,
            rest_days=5,
        )

        return home, away

    def test_predict_match_basic(self, engine, sample_teams):
        """Test basic match prediction"""
        home, away = sample_teams

        prediction = engine.predict_match(home, away)

        assert isinstance(prediction, MatchPrediction)
        assert prediction.home_team == "Portugal"
        assert prediction.away_team == "Brazil"

    def test_prediction_probabilities_sum_to_one(self, engine, sample_teams):
        """Test that win/draw/loss probabilities sum to ~1.0"""
        home, away = sample_teams

        prediction = engine.predict_match(home, away)

        total = prediction.home_win_prob + prediction.draw_prob + prediction.away_win_prob
        assert total == pytest.approx(1.0, abs=0.01)

    def test_prediction_probabilities_valid_range(self, engine, sample_teams):
        """Test that all probabilities are in valid range [0, 1]"""
        home, away = sample_teams

        prediction = engine.predict_match(home, away)

        assert 0 <= prediction.home_win_prob <= 1
        assert 0 <= prediction.draw_prob <= 1
        assert 0 <= prediction.away_win_prob <= 1
        assert 0 <= prediction.over_2_5_prob <= 1
        assert 0 <= prediction.btts_prob <= 1

    def test_stronger_team_favored(self, engine):
        """Test that stronger team gets higher win probability"""
        strong = TeamData(
            name="Strong Team",
            fifa_ranking=1,
            elo_rating=2000,
            matches_played=10,
            wins=9,
            draws=1,
            losses=0,
            goals_scored=30,
            goals_conceded=3,
            avg_xg_for=3.0,
            avg_xg_against=0.3,
        )

        weak = TeamData(
            name="Weak Team",
            fifa_ranking=50,
            elo_rating=1400,
            matches_played=10,
            wins=2,
            draws=2,
            losses=6,
            goals_scored=8,
            goals_conceded=20,
            avg_xg_for=0.8,
            avg_xg_against=2.0,
        )

        prediction = engine.predict_match(strong, weak)

        # Strong team should be favored
        assert prediction.home_win_prob > prediction.away_win_prob

    def test_confidence_levels_valid(self, engine, sample_teams):
        """Test that confidence levels are in valid range"""
        home, away = sample_teams

        prediction = engine.predict_match(home, away)

        assert 0 <= prediction.home_confidence <= 100
        assert 0 <= prediction.draw_confidence <= 100
        assert 0 <= prediction.away_confidence <= 100

    def test_key_factors_generated(self, engine, sample_teams):
        """Test that reasoning/key factors are generated"""
        home, away = sample_teams

        prediction = engine.predict_match(home, away)

        assert isinstance(prediction.key_factors, list)
        # May have 0-5 factors depending on data
        assert len(prediction.key_factors) <= 5

    def test_most_likely_outcome(self, engine, sample_teams):
        """Test most_likely_outcome property"""
        home, away = sample_teams

        prediction = engine.predict_match(home, away)

        outcome = prediction.most_likely_outcome
        assert outcome in ["home", "draw", "away"]

        # Verify it matches the highest probability
        probs = {
            "home": prediction.home_win_prob,
            "draw": prediction.draw_prob,
            "away": prediction.away_win_prob,
        }

        expected = max(probs.items(), key=lambda x: x[1])[0]
        assert outcome == expected

    def test_get_probability_method(self, engine, sample_teams):
        """Test get_probability method for different outcomes"""
        home, away = sample_teams

        prediction = engine.predict_match(home, away)

        # Test different outcome identifiers
        assert prediction.get_probability("home") == prediction.home_win_prob
        assert prediction.get_probability("1") == prediction.home_win_prob
        assert prediction.get_probability("draw") == prediction.draw_prob
        assert prediction.get_probability("X") == prediction.draw_prob
        assert prediction.get_probability("away") == prediction.away_win_prob
        assert prediction.get_probability("2") == prediction.away_win_prob
        assert prediction.get_probability("over_2_5") == prediction.over_2_5_prob
        assert prediction.get_probability("btts") == prediction.btts_prob
        assert prediction.get_probability("gg") == prediction.btts_prob

    def test_context_must_win_adjustment(self, engine, sample_teams):
        """Test that must-win context affects probabilities"""
        home, away = sample_teams

        match_date = datetime.now() + timedelta(days=3)

        # Context where home must win
        context_must_win = MatchContext(
            home_team=home,
            away_team=away,
            match_date=match_date,
            is_must_win_home=True,
            is_must_win_away=False,
        )

        # Context where away must win
        context_away_must = MatchContext(
            home_team=home,
            away_team=away,
            match_date=match_date,
            is_must_win_home=False,
            is_must_win_away=True,
        )

        pred_must_win = engine.predict_match(home, away, context_must_win)
        pred_away_must = engine.predict_match(home, away, context_away_must)

        # Home should have higher win prob when they must win
        assert pred_must_win.home_win_prob > pred_away_must.home_win_prob

    def test_poisson_to_probabilities(self, engine):
        """Test Poisson distribution conversion"""
        # Test with equal expected goals
        home_win, draw, away_win = engine._poisson_to_probabilities(1.5, 1.5)

        # Should sum to ~1.0
        total = home_win + draw + away_win
        assert total == pytest.approx(1.0, abs=0.01)

        # With equal xG, home and away should be similar (slight draw bias)
        assert abs(home_win - away_win) < 0.1

    def test_over_2_5_probability_high_xg(self, engine):
        """Test over 2.5 probability with high expected goals"""
        prob = engine._calculate_over_2_5_probability(2.5, 2.0)

        # With 4.5 total xG, over 2.5 should be likely
        assert prob > 0.7

    def test_over_2_5_probability_low_xg(self, engine):
        """Test over 2.5 probability with low expected goals"""
        prob = engine._calculate_over_2_5_probability(0.8, 0.6)

        # With 1.4 total xG, over 2.5 should be unlikely
        assert prob < 0.3

    def test_btts_probability_both_strong_attacks(self, engine):
        """Test BTTS probability with strong attacking teams"""
        prob = engine._calculate_btts_probability(2.0, 1.8)

        # Both teams likely to score
        assert prob > 0.6

    def test_btts_probability_weak_attacks(self, engine):
        """Test BTTS probability with weak attacking teams"""
        prob = engine._calculate_btts_probability(0.5, 0.4)

        # Unlikely both teams score
        assert prob < 0.3


class TestPredictionEngineWeights:
    """Tests for prediction engine weight configuration"""

    def test_default_weights_sum_to_one(self):
        """Test that default weights sum to 1.0"""
        engine = PredictionEngine()

        total = sum(engine.weights.values())
        assert total == pytest.approx(1.0, rel=0.01)

    def test_all_weights_present(self):
        """Test that all required weights are present"""
        engine = PredictionEngine()

        required_weights = ['elo', 'form', 'h2h', 'attack_defense', 'context']

        for weight_name in required_weights:
            assert weight_name in engine.weights
            assert engine.weights[weight_name] > 0


class TestMatchPredictionDataclass:
    """Tests for MatchPrediction dataclass"""

    def test_create_match_prediction(self):
        """Test creating MatchPrediction directly"""
        pred = MatchPrediction(
            home_team="Team A",
            away_team="Team B",
            home_win_prob=0.45,
            draw_prob=0.28,
            away_win_prob=0.27,
            home_confidence=68.0,
            draw_confidence=55.0,
            away_confidence=62.0,
            over_2_5_prob=0.58,
            btts_prob=0.52,
            key_factors=["Factor 1", "Factor 2"],
        )

        assert pred.home_team == "Team A"
        assert pred.away_team == "Team B"
        assert len(pred.key_factors) == 2
