"""
Team statistics and data models for prediction engine
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class TeamData:
    """Raw team data from various sources"""
    name: str
    country_code: str = ""
    fifa_ranking: int = 0
    elo_rating: int = 0

    # Recent form (last 10 matches)
    matches_played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_scored: int = 0
    goals_conceded: int = 0

    # Advanced metrics
    avg_xg_for: float = 0.0  # Expected goals for per match
    avg_xg_against: float = 0.0  # Expected goals against per match
    avg_possession: float = 0.0
    clean_sheets: int = 0

    # Head-to-head record (vs specific opponent)
    h2h_wins: int = 0
    h2h_draws: int = 0
    h2h_losses: int = 0

    # Player availability
    key_players_available: List[str] = field(default_factory=list)
    key_players_out: List[str] = field(default_factory=list)
    injuries: List[str] = field(default_factory=list)
    suspensions: List[str] = field(default_factory=list)

    # Tournament context
    group_position: Optional[int] = None
    must_win: bool = False
    rest_days: int = 0

    @property
    def form_points(self) -> int:
        """Calculate form points (3 for win, 1 for draw)"""
        return (self.wins * 3) + self.draws

    @property
    def form_percentage(self) -> float:
        """Calculate form as percentage of maximum points"""
        if self.matches_played == 0:
            return 50.0
        max_points = self.matches_played * 3
        return (self.form_points / max_points) * 100

    @property
    def goal_difference(self) -> int:
        return self.goals_scored - self.goals_conceded

    @property
    def avg_goals_scored(self) -> float:
        if self.matches_played == 0:
            return 0.0
        return self.goals_scored / self.matches_played

    @property
    def avg_goals_conceded(self) -> float:
        if self.matches_played == 0:
            return 0.0
        return self.goals_conceded / self.matches_played


@dataclass
class TeamStats:
    """Computed statistics for prediction modeling"""
    team_data: TeamData

    # Computed metrics
    attack_strength: float = 0.0
    defense_strength: float = 0.0
    overall_strength: float = 0.0
    form_factor: float = 0.0
    home_advantage: float = 0.0

    def __post_init__(self):
        """Compute derived statistics after initialization"""
        self._compute_attack_strength()
        self._compute_defense_strength()
        self._compute_overall_strength()
        self._compute_form_factor()

    def _compute_attack_strength(self):
        """Calculate attack strength based on multiple factors"""
        data = self.team_data

        # Goals scored component (40%)
        goal_component = min(100, data.avg_goals_scored * 30)

        # xG component (30%)
        xg_component = min(100, data.avg_xg_for * 40)

        # FIFA/ELO component (30%)
        ranking_component = max(0, 100 - (data.fifa_ranking * 0.5))
        elo_component = min(100, (data.elo_rating - 1000) / 2)

        self.attack_strength = (
            goal_component * 0.4
            + xg_component * 0.3
            + ((ranking_component + elo_component) / 2) * 0.3
        )

    def _compute_defense_strength(self):
        """Calculate defense strength (lower conceded = higher strength)"""
        data = self.team_data

        # Goals conceded component (40%) - inverted
        goal_component = max(0, 100 - (data.avg_goals_conceded * 40))

        # xG against component (30%) - inverted
        xg_component = max(0, 100 - (data.avg_xg_against * 50))

        # Clean sheets component (30%)
        if data.matches_played > 0:
            cs_component = (data.clean_sheets / data.matches_played) * 100
        else:
            cs_component = 50

        self.defense_strength = (
            goal_component * 0.4
            + xg_component * 0.3
            + cs_component * 0.3
        )

    def _compute_overall_strength(self):
        """Calculate overall team strength"""
        # Weighted average of attack and defense
        self.overall_strength = (
            self.attack_strength * 0.55
            + self.defense_strength * 0.45
        )

    def _compute_form_factor(self):
        """Calculate recent form factor"""
        data = self.team_data

        # Base form from points percentage
        base_form = data.form_percentage

        # Bonus for recent momentum (last 5 vs last 10)
        # Simplified: use goal difference trend
        gd_per_game = data.goal_difference / max(1, data.matches_played)
        momentum_bonus = min(15, max(-15, gd_per_game * 5))

        self.form_factor = min(100, max(0, base_form + momentum_bonus))

    def get_h2h_advantage(self, opponent_stats: 'TeamStats') -> float:
        """
        Calculate head-to-head advantage.
        Positive = this team has advantage, negative = opponent has advantage
        """
        total_h2h = (
            self.team_data.h2h_wins +
            self.team_data.h2h_draws +
            self.team_data.h2h_losses
        )

        if total_h2h == 0:
            return 0.0  # No H2H data

        win_rate = self.team_data.h2h_wins / total_h2h
        loss_rate = self.team_data.h2h_losses / total_h2h

        # Scale to -50 to +50 range
        return (win_rate - loss_rate) * 50


class MatchContext:
    """Context information for a specific match"""

    def __init__(
        self,
        home_team: TeamData,
        away_team: TeamData,
        match_date: datetime,
        venue: str = "Neutral",
        tournament_stage: str = "Group Stage",
        is_must_win_home: bool = False,
        is_must_win_away: bool = False
    ):
        self.home_team = home_team
        self.away_team = away_team
        self.match_date = match_date
        self.venue = venue
        self.tournament_stage = tournament_stage
        self.is_must_win_home = is_must_win_home
        self.is_must_win_away = is_must_win_away

        # Compute rest days
        today = datetime.now()
        self.rest_days_home = (match_date - today).days
        self.rest_days_away = (match_date - today).days
