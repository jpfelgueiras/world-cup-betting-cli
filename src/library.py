"""
World Cup Betting Insights - Python Library Interface

Import this module to use the betting insights engine programmatically
in your own projects.

Example usage:
    from src.library import BettingInsights

    # Initialize
    insights = BettingInsights(min_ev=5.0, min_confidence=60.0)

    # Analyze a match
    result = insights.analyze_match("Portugal", "Brazil")
    print(f"Value bets found: {len(result.value_bets)}")

    # Scan upcoming matches
    scan_results = insights.scan_upcoming_matches(days_ahead=7)
    print(f"Total value bets: {scan_results.total_value_bets}")
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from .config import BETTING_SITES, DEFAULT_MIN_CONFIDENCE, DEFAULT_MIN_EV
from .predictors.prediction_engine import PredictionEngine
from .predictors.team_stats import TeamData
from .scrapers.base_scraper import OddsData
from .scrapers.betano_scraper import BetanoScraper
from .scrapers.betclic_scraper import BetclicScraper
from .scrapers.solverde_scraper import SolverdeScraper
from .utils.ev_calculator import (
    BetRecommendation,
    analyze_bet,
    calculate_market_average,
    find_best_value_bets,
)


@dataclass
class MatchAnalysisResult:
    """Result of a match analysis"""

    home_team: str
    away_team: str
    match_date: Optional[datetime] = None

    # Probabilities
    home_win_prob: float = 0.0
    draw_prob: float = 0.0
    away_win_prob: float = 0.0
    over_2_5_prob: float = 0.0
    btts_prob: float = 0.0

    # Confidence levels
    home_confidence: float = 0.0
    draw_confidence: float = 0.0
    away_confidence: float = 0.0

    # Market averages
    market_avg_home: Optional[float] = None
    market_avg_draw: Optional[float] = None
    market_avg_away: Optional[float] = None

    # Value bets
    value_bets: List[BetRecommendation] = field(default_factory=list)

    # Analysis metadata
    key_factors: List[str] = field(default_factory=list)
    num_bookmakers: int = 0
    analysis_timestamp: datetime = field(default_factory=datetime.now)

    @property
    def most_likely_outcome(self) -> str:
        """Get the most likely outcome"""
        probs = [
            ("home", self.home_win_prob),
            ("draw", self.draw_prob),
            ("away", self.away_win_prob),
        ]
        return max(probs, key=lambda x: x[1])[0]

    @property
    def has_value_bets(self) -> bool:
        """Check if there are any value bets"""
        return len(self.value_bets) > 0

    def get_best_value_bet(self) -> Optional[BetRecommendation]:
        """Get the best value bet by EV"""
        if not self.value_bets:
            return None
        return max(self.value_bets, key=lambda x: x.ev_percentage)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "match_date": self.match_date.isoformat() if self.match_date else None,
            "probabilities": {
                "home_win": self.home_win_prob,
                "draw": self.draw_prob,
                "away_win": self.away_win_prob,
                "over_2_5": self.over_2_5_prob,
                "btts": self.btts_prob,
            },
            "confidence": {
                "home": self.home_confidence,
                "draw": self.draw_confidence,
                "away": self.away_confidence,
            },
            "market_averages": {
                "home": self.market_avg_home,
                "draw": self.market_avg_draw,
                "away": self.market_avg_away,
            },
            "value_bets": [
                {
                    "market": b.market,
                    "site": b.site,
                    "site_name": b.site_name,
                    "odds": b.odds,
                    "ev_percentage": b.ev_percentage,
                    "confidence": b.confidence,
                    "is_value_bet": b.is_value_bet,
                }
                for b in self.value_bets
            ],
            "key_factors": self.key_factors,
            "num_bookmakers": self.num_bookmakers,
        }


@dataclass
class ScanResult:
    """Result of scanning multiple matches"""

    scan_date: datetime = field(default_factory=datetime.now)
    total_matches: int = 0
    matches_with_value_bets: int = 0
    total_value_bets: int = 0
    matches: List[MatchAnalysisResult] = field(default_factory=list)

    @property
    def all_value_bets(self) -> List[BetRecommendation]:
        """Get all value bets from all matches"""
        all_bets = []
        for match in self.matches:
            all_bets.extend(match.value_bets)
        return all_bets

    def get_top_value_bets(self, limit: int = 10) -> List[BetRecommendation]:
        """Get top N value bets across all matches"""
        all_bets = self.all_value_bets
        sorted_bets = sorted(all_bets, key=lambda x: x.ev_percentage, reverse=True)
        return sorted_bets[:limit]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "scan_date": self.scan_date.isoformat(),
            "total_matches": self.total_matches,
            "matches_with_value_bets": self.matches_with_value_bets,
            "total_value_bets": self.total_value_bets,
            "matches": [m.to_dict() for m in self.matches],
        }


class BettingInsights:
    """
    Main library interface for programmatic access.

    Provides methods to:
    - Analyze individual matches
    - Scan upcoming matches for value bets
    - Get bookmaker information
    - Configure analysis parameters

    Example:
        insights = BettingInsights(min_ev=5.0, min_confidence=60.0)
        result = insights.analyze_match("Portugal", "Brazil")

        if result.has_value_bets:
            best_bet = result.get_best_value_bet()
            print(f"Best bet: {best_bet.market} @ {best_bet.site_name}")
            print(f"EV: {best_bet.ev_percentage:.1f}%")
    """

    def __init__(
        self,
        min_ev: float = DEFAULT_MIN_EV,
        min_confidence: float = DEFAULT_MIN_CONFIDENCE,
        enabled_sites: Optional[List[str]] = None,
        cache_enabled: bool = True,
    ):
        """
        Initialize the betting insights engine.

        Args:
            min_ev: Minimum expected value threshold (percentage)
            min_confidence: Minimum confidence threshold (percentage)
            enabled_sites: List of bookmaker site keys to use (default: all enabled)
            cache_enabled: Enable caching of odds data
        """
        self.min_ev = min_ev
        self.min_confidence = min_confidence
        self.cache_enabled = cache_enabled

        # Initialize prediction engine
        self.engine = PredictionEngine()

        # Initialize scrapers based on enabled sites
        if enabled_sites is None:
            enabled_sites = [
                key
                for key, config in BETTING_SITES.items()
                if config.get("enabled", False)
            ]

        self.scrapers: List[Any] = []
        if "betano" in enabled_sites:
            self.scrapers.append(BetanoScraper())
        if "betclic" in enabled_sites:
            self.scrapers.append(BetclicScraper())
        if "solverde" in enabled_sites:
            self.scrapers.append(SolverdeScraper())

        # Initialize cache
        if cache_enabled:
            try:
                from .predictors.data_loader import DataLoader

                self.data_loader = DataLoader()
            except Exception:
                self.data_loader = None
                self.cache_enabled = False
        else:
            self.data_loader = None

    def analyze_match(
        self,
        home_team: str,
        away_team: str,
        match_date: Optional[datetime] = None,
        min_ev: Optional[float] = None,
        min_confidence: Optional[float] = None,
    ) -> MatchAnalysisResult:
        """
        Analyze a specific match for value bets.

        Args:
            home_team: Home team name
            away_team: Away team name
            match_date: Optional match date
            min_ev: Override minimum EV threshold
            min_confidence: Override minimum confidence threshold

        Returns:
            MatchAnalysisResult with probabilities and value bets

        Raises:
            ValueError: If no odds available from any bookmaker
        """
        # Use overrides or defaults
        ev_threshold = min_ev if min_ev is not None else self.min_ev
        conf_threshold = (
            min_confidence if min_confidence is not None else self.min_confidence
        )

        # Create team data (in production, fetch from real sources)
        home_data = self._create_team_data(home_team)
        away_data = self._create_team_data(away_team)

        # Generate prediction
        prediction = self.engine.predict_match(home_data, away_data)

        # Get odds from scrapers
        all_odds = self._get_match_odds(home_team, away_team, match_date)

        if not all_odds:
            raise ValueError(f"No odds available for {home_team} vs {away_team}")

        # Calculate market averages
        market_avg = self._calculate_market_averages(all_odds)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            prediction, all_odds, market_avg, ev_threshold, conf_threshold
        )

        # Filter value bets
        value_bets = find_best_value_bets(recommendations, ev_threshold, conf_threshold)

        # Build result
        result = MatchAnalysisResult(
            home_team=home_team,
            away_team=away_team,
            match_date=match_date,
            home_win_prob=prediction.home_win_prob,
            draw_prob=prediction.draw_prob,
            away_win_prob=prediction.away_win_prob,
            over_2_5_prob=prediction.over_2_5_prob,
            btts_prob=prediction.btts_prob,
            home_confidence=prediction.home_confidence,
            draw_confidence=prediction.draw_confidence,
            away_confidence=prediction.away_confidence,
            market_avg_home=market_avg.get("home_win"),
            market_avg_draw=market_avg.get("draw"),
            market_avg_away=market_avg.get("away_win"),
            value_bets=value_bets,
            key_factors=prediction.key_factors,
            num_bookmakers=len(all_odds),
        )

        # Log prediction for tracking
        if self.data_loader:
            self.data_loader.log_prediction(home_team, away_team, prediction)

        return result

    def scan_upcoming_matches(
        self,
        days_ahead: int = 7,
        min_ev: Optional[float] = None,
        min_confidence: Optional[float] = None,
    ) -> ScanResult:
        """
        Scan upcoming matches for value bets.

        Args:
            days_ahead: Number of days to scan ahead
            min_ev: Override minimum EV threshold
            min_confidence: Override minimum confidence threshold

        Returns:
            ScanResult with all matches containing value bets
        """
        ev_threshold = min_ev if min_ev is not None else self.min_ev
        conf_threshold = (
            min_confidence if min_confidence is not None else self.min_confidence
        )

        # Collect all upcoming matches
        all_matches: Dict[str, Dict[str, Any]] = {}

        for scraper in self.scrapers:
            try:
                matches = scraper.get_upcoming_matches(days_ahead=days_ahead)
                for match in matches:
                    key = f"{match.home_team}_{match.away_team}"
                    if key not in all_matches:
                        all_matches[key] = {"match": match, "odds": []}
                    all_matches[key]["odds"].append(match)
            except Exception:
                continue  # Skip failed scrapers

        # Analyze each match
        matches_with_bets = []
        total_value_bets = 0

        for data in all_matches.values():
            match = data["match"]

            # Analyze match
            try:
                result = self.analyze_match(
                    match.home_team,
                    match.away_team,
                    match.match_date,
                    ev_threshold,
                    conf_threshold,
                )

                if result.has_value_bets:
                    total_value_bets += len(result.value_bets)
                    matches_with_bets.append(result)
            except Exception:
                continue  # Skip failed analyses

        return ScanResult(
            total_matches=len(all_matches),
            matches_with_value_bets=len(matches_with_bets),
            total_value_bets=total_value_bets,
            matches=matches_with_bets,
        )

    def get_bookmakers(self) -> List[Dict[str, Any]]:
        """
        Get list of configured bookmakers.

        Returns:
            List of bookmaker information dictionaries
        """
        result = []
        for site_key, config in BETTING_SITES.items():
            result.append(
                {
                    "key": site_key,
                    "name": config.get("name", site_key),
                    "url": config.get("url", ""),
                    "enabled": config.get("enabled", False),
                    "rate_limit_seconds": config.get("rate_limit_seconds", 5),
                }
            )
        return result

    def update_config(
        self,
        min_ev: Optional[float] = None,
        min_confidence: Optional[float] = None,
        enabled_sites: Optional[List[str]] = None,
    ):
        """
        Update configuration parameters.

        Args:
            min_ev: New minimum EV threshold
            min_confidence: New minimum confidence threshold
            enabled_sites: New list of enabled bookmaker sites
        """
        if min_ev is not None:
            self.min_ev = min_ev
        if min_confidence is not None:
            self.min_confidence = min_confidence

        if enabled_sites is not None:
            self.scrapers = []
            if "betano" in enabled_sites:
                self.scrapers.append(BetanoScraper())
            if "betclic" in enabled_sites:
                self.scrapers.append(BetclicScraper())
            if "solverde" in enabled_sites:
                self.scrapers.append(SolverdeScraper())

    def _create_team_data(self, team_name: str) -> TeamData:
        """Create team data (mock implementation)"""
        import random

        return TeamData(
            name=team_name,
            fifa_ranking=random.randint(1, 50),
            elo_rating=random.randint(1400, 2000),
            matches_played=10,
            wins=random.randint(4, 9),
            draws=random.randint(1, 4),
            losses=random.randint(0, 3),
            goals_scored=random.randint(15, 30),
            goals_conceded=random.randint(5, 15),
            avg_xg_for=random.uniform(1.5, 2.5),
            avg_xg_against=random.uniform(0.8, 1.5),
            avg_possession=random.uniform(45, 65),
            clean_sheets=random.randint(3, 7),
            rest_days=random.randint(2, 7),
        )

    def _get_match_odds(
        self, home_team: str, away_team: str, match_date: Optional[datetime]
    ) -> List[OddsData]:
        """Get odds from all configured scrapers"""
        all_odds = []

        for scraper in self.scrapers:
            try:
                # Fetch from scraper
                odds = scraper.get_match_odds(home_team, away_team, match_date)
                if odds:
                    all_odds.append(odds)

            except Exception as e:
                # Log error but continue with other scrapers
                import logging

                logging.warning(f"{scraper.site_key} failed: {type(e).__name__}: {e}")
                continue

        return all_odds

    def _calculate_market_averages(self, odds_list: list) -> dict:
        """Calculate market average odds"""
        home_odds = [o.home_win for o in odds_list if o.home_win]
        draw_odds = [o.draw for o in odds_list if o.draw]
        away_odds = [o.away_win for o in odds_list if o.away_win]
        over_odds = [o.over_2_5 for o in odds_list if o.over_2_5]
        btts_odds = [o.btts_yes for o in odds_list if o.btts_yes]

        return {
            "home_win": calculate_market_average(home_odds) if home_odds else None,
            "draw": calculate_market_average(draw_odds) if draw_odds else None,
            "away_win": calculate_market_average(away_odds) if away_odds else None,
            "over_2_5": calculate_market_average(over_odds) if over_odds else None,
            "btts_yes": calculate_market_average(btts_odds) if btts_odds else None,
            "num_bookmakers": len(odds_list),
        }

    def _generate_recommendations(
        self, prediction, odds_list, market_avg, min_ev, min_conf
    ):
        """Generate bet recommendations"""
        recommendations = []

        for odds in odds_list:
            # 1X2 markets
            if odds.home_win:
                rec = analyze_bet(
                    market="1X2 - Home Win",
                    site=odds.site,
                    site_name=odds.site_name,
                    odds=odds.home_win,
                    model_probability=prediction.home_win_prob,
                    confidence=prediction.home_confidence,
                    reasoning=prediction.key_factors,
                    min_ev=min_ev,
                    min_confidence=min_conf,
                )
                recommendations.append(rec)

            if odds.draw:
                rec = analyze_bet(
                    market="1X2 - Draw",
                    site=odds.site,
                    site_name=odds.site_name,
                    odds=odds.draw,
                    model_probability=prediction.draw_prob,
                    confidence=prediction.draw_confidence,
                    reasoning=prediction.key_factors,
                    min_ev=min_ev,
                    min_confidence=min_conf,
                )
                recommendations.append(rec)

            if odds.away_win:
                rec = analyze_bet(
                    market="1X2 - Away Win",
                    site=odds.site,
                    site_name=odds.site_name,
                    odds=odds.away_win,
                    model_probability=prediction.away_win_prob,
                    confidence=prediction.away_confidence,
                    reasoning=prediction.key_factors,
                    min_ev=min_ev,
                    min_confidence=min_conf,
                )
                recommendations.append(rec)

            # Over/Under 2.5
            if odds.over_2_5:
                rec = analyze_bet(
                    market="Over 2.5 Goals",
                    site=odds.site,
                    site_name=odds.site_name,
                    odds=odds.over_2_5,
                    model_probability=prediction.over_2_5_prob,
                    confidence=65.0,
                    reasoning=prediction.key_factors,
                    min_ev=min_ev,
                    min_confidence=min_conf,
                )
                recommendations.append(rec)

            # BTTS
            if odds.btts_yes:
                rec = analyze_bet(
                    market="Both Teams To Score",
                    site=odds.site,
                    site_name=odds.site_name,
                    odds=odds.btts_yes,
                    model_probability=prediction.btts_prob,
                    confidence=65.0,
                    reasoning=prediction.key_factors,
                    min_ev=min_ev,
                    min_confidence=min_conf,
                )
                recommendations.append(rec)

        return recommendations


# Convenience function for quick access
def create_insights(
    min_ev: float = 5.0, min_confidence: float = 60.0, **kwargs
) -> BettingInsights:
    """
    Create a BettingInsights instance with custom configuration.

    This is a convenience function for quick setup.

    Args:
        min_ev: Minimum EV threshold (default: 5.0)
        min_confidence: Minimum confidence threshold (default: 60.0)
        **kwargs: Additional arguments passed to BettingInsights

    Returns:
        Configured BettingInsights instance

    Example:
        insights = create_insights(min_ev=8.0, min_confidence=70.0)
    """
    return BettingInsights(min_ev=min_ev, min_confidence=min_confidence, **kwargs)
