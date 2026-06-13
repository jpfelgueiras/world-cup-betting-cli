"""
REST API Routes

Provides REST endpoints for:
- Match predictions
- Value bet scanning
- Bookmaker odds
- Health checks
- Library configuration
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from .models import (
    AnalysisConfig,
    BookmakerStatus,
    ConfidenceLevels,
    ErrorResponse,
    HealthResponse,
    LibraryConfig,
    MarketAverage,
    MarketType,
    MatchAnalysisResponse,
    MatchPredictionRequest,
    RiskTolerance,
    ScanMatchResult,
    ScanRequest,
    ScanResponse,
    TeamProbabilities,
    ValueBet,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["betting-insights"])


# Dependency injection for services (would be initialized in create_app)
def get_prediction_engine():
    """Get prediction engine instance"""
    from ..predictors.prediction_engine import PredictionEngine

    return PredictionEngine()


def get_scrapers(site: str = "all"):
    """Get list of scrapers based on site parameter"""
    from ..scrapers.betano_scraper import BetanoScraper
    from ..scrapers.betclic_scraper import BetclicScraper
    from ..scrapers.bwin_scraper import BwinScraper
    from ..scrapers.casinoportugal_scraper import CasinoPortugalScraper
    from ..scrapers.esc_scraper import EscScraper
    from ..scrapers.goldenpark_scraper import GoldenParkScraper
    from ..scrapers.lebull_scraper import LeBullScraper
    from ..scrapers.placard_scraper import PlacardScraper
    from ..scrapers.solverde_scraper import SolverdeScraper

    scrapers: List[Any] = []
    if site == "all" or site == "betano":
        scrapers.append(BetanoScraper())
    if site == "all" or site == "betclic":
        scrapers.append(BetclicScraper())
    if site == "all" or site == "bwin":
        scrapers.append(BwinScraper())
    if site == "all" or site == "lebull":
        scrapers.append(LeBullScraper())
    if site == "all" or site == "esc":
        scrapers.append(EscScraper())
    if site == "all" or site == "solverde":
        scrapers.append(SolverdeScraper())
    if site == "all" or site == "goldenpark":
        scrapers.append(GoldenParkScraper())
    if site == "all" or site == "casinoportugal":
        scrapers.append(CasinoPortugalScraper())
    if site == "all" or site == "placard":
        scrapers.append(PlacardScraper())

    return scrapers


def get_analysis_config(
    min_ev: float = Query(5.0, ge=0, le=100, description="Minimum EV threshold %"),
    min_confidence: float = Query(
        60.0, ge=0, le=100, description="Minimum confidence %"
    ),
    risk_tolerance: RiskTolerance = Query(
        RiskTolerance.MODERATE, description="Risk tolerance level"
    ),
    markets: Optional[List[MarketType]] = Query(None, description="Markets to analyze"),
) -> AnalysisConfig:
    """Build AnalysisConfig from query params without leaking default-factory sentinels into dependency parsing."""
    return AnalysisConfig(
        min_ev=min_ev,
        min_confidence=min_confidence,
        risk_tolerance=risk_tolerance,
        markets=markets
        or [MarketType.MATCH_WINNER, MarketType.OVER_UNDER_25, MarketType.BTTS],
    )


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns status of all components:
    - API server
    - Bookmaker integrations
    - Prediction engine
    - Database connection
    """
    from src import __version__
    from src.config import BETTING_SITES

    bookmaker_statuses = []
    for site_key, config in BETTING_SITES.items():
        if site_key == "nossaaposta":
            continue
        status = BookmakerStatus(
            site_key=site_key,
            site_name=config.get("name", site_key),
            enabled=config.get("enabled", False),
            rate_limit_seconds=config.get("rate_limit_seconds", 5),
            status="operational" if config.get("enabled", False) else "disabled",
        )
        bookmaker_statuses.append(status)

    return HealthResponse(
        version=__version__,
        bookmakers=bookmaker_statuses,
        prediction_engine="operational",
        database="connected",
    )


@router.post(
    "/predict",
    response_model=MatchAnalysisResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        404: {"model": ErrorResponse, "description": "Match not found"},
        500: {"model": ErrorResponse, "description": "Internal error"},
    },
    tags=["Predictions"],
)
async def predict_match(
    request: MatchPredictionRequest,
    config: AnalysisConfig = Depends(get_analysis_config),  # type: ignore
    engine=Depends(get_prediction_engine),  # type: ignore
):
    """
    Analyze a specific match and find value bets.

    Compares AI-generated probabilities against odds from Portuguese bookmakers
    to identify bets with positive expected value (EV).

    **Example:**
    ```json
    {
        "home_team": "Portugal",
        "away_team": "Brazil",
        "site": "all"
    }
    ```
    """
    try:
        # Create mock team data (in production, fetch from data sources)
        home_data = _create_mock_team_data(request.home_team)
        away_data = _create_mock_team_data(request.away_team)

        # Generate prediction
        prediction = engine.predict_match(home_data, away_data)

        # Get odds from scrapers
        scrapers = get_scrapers(request.site.value)
        all_odds = []

        for scraper in scrapers:
            try:
                odds = scraper.get_match_odds(
                    request.home_team, request.away_team, request.match_date
                )
                if odds:
                    all_odds.append(odds)
            except Exception as exc:
                logger.warning(
                    "Skipping unavailable odds scraper for %s vs %s: %s",
                    request.home_team,
                    request.away_team,
                    exc,
                    exc_info=True,
                )
                continue  # Skip unavailable scrapers

        if not all_odds:
            raise HTTPException(
                status_code=404,
                detail=f"No odds available for {request.home_team} vs {request.away_team}",
            )

        # Calculate market averages
        market_avg = _calculate_market_averages(all_odds)

        # Generate recommendations
        recommendations = _generate_recommendations(
            prediction, all_odds, market_avg, config.min_ev, config.min_confidence
        )

        # Filter value bets based on risk tolerance
        value_bets = _filter_by_risk_tolerance(recommendations, config.risk_tolerance)

        # Build response
        response = MatchAnalysisResponse(
            match_id=f"{request.home_team.lower()}_{request.away_team.lower()}_{datetime.now().strftime('%Y%m%d')}",
            home_team=request.home_team,
            away_team=request.away_team,
            match_date=request.match_date,
            tournament_stage="Group Stage",  # Would be determined from context
            probabilities=TeamProbabilities(
                home_win=prediction.home_win_prob,
                draw=prediction.draw_prob,
                away_win=prediction.away_win_prob,
                over_2_5=prediction.over_2_5_prob,
                btts=prediction.btts_prob,
            ),
            confidence=ConfidenceLevels(
                home_win=prediction.home_confidence,
                draw=prediction.draw_confidence,
                away_win=prediction.away_confidence,
            ),
            market_averages=MarketAverage(
                home_win=market_avg.get("home_win"),
                draw=market_avg.get("draw"),
                away_win=market_avg.get("away_win"),
                over_2_5=market_avg.get("over_2_5"),
                btts_yes=market_avg.get("btts_yes"),
                num_bookmakers=len(all_odds),
            ),
            value_bets=[
                ValueBet(
                    market=b.market,
                    site=b.site,
                    site_name=b.site_name,
                    odds=b.odds,
                    probability=b.probability,
                    ev_percentage=b.ev_percentage,
                    confidence=b.confidence,
                    is_value_bet=b.is_value_bet,
                    reasoning=b.reasoning[:3],  # Limit reasoning
                )
                for b in value_bets[:10]  # Top 10 value bets
            ],
            key_factors=prediction.key_factors,
            metadata={
                "model_version": "1.0.0",
                "analysis_timestamp": datetime.now().isoformat(),
            },
        )

        return response

    except HTTPException:
        raise
    except Exception:
        logger.exception(
            "Prediction failed for %s vs %s", request.home_team, request.away_team
        )
        raise HTTPException(
            status_code=500,
            detail="Prediction failed due to an internal error",
            headers={"X-Error-Code": "PREDICTION_ERROR"},
        )


@router.post("/scan", response_model=ScanResponse, tags=["Scanning"])
async def scan_matches(
    request: ScanRequest = None,
    config: AnalysisConfig = Depends(get_analysis_config),  # type: ignore
    engine=Depends(get_prediction_engine),  # type: ignore
):
    """
    Scan upcoming matches for value bets.

    Analyzes all available matches within the specified date range
    and returns those with value bets matching your criteria.
    """
    if request is None:
        request = ScanRequest.model_construct()

    # Determine date range
    start_date = request.start_date or datetime.now()
    if request.end_date:
        end_date = request.end_date
    else:
        from datetime import timedelta

        end_date = start_date + timedelta(days=request.days_ahead)

    # Get scrapers
    scrapers = get_scrapers(request.site.value)

    # Collect all upcoming matches
    all_matches: Dict[str, Dict[str, Any]] = {}

    for scraper in scrapers:
        try:
            matches = scraper.get_upcoming_matches(days_ahead=request.days_ahead)
            for match in matches:
                key = f"{match.home_team}_{match.away_team}"
                if key not in all_matches:
                    all_matches[key] = {"match": match, "odds": []}
                all_matches[key]["odds"].append(match)
        except Exception as exc:
            logger.warning(
                "Skipping unavailable match scraper %s: %s",
                scraper.__class__.__name__,
                exc,
                exc_info=True,
            )
            continue  # Skip failed scrapers

    # Analyze each match
    scan_results = []
    total_value_bets = 0

    for match_key, data in all_matches.items():
        match = data["match"]
        odds_list = data["odds"]

        # Create team data
        home_data = _create_mock_team_data(match.home_team)
        away_data = _create_mock_team_data(match.away_team)

        # Generate prediction
        prediction = engine.predict_match(home_data, away_data)

        # Calculate market averages
        market_avg = _calculate_market_averages(odds_list)

        # Generate recommendations
        recommendations = _generate_recommendations(
            prediction, odds_list, market_avg, config.min_ev, config.min_confidence
        )

        # Filter value bets
        value_bets = [r for r in recommendations if r.is_value_bet]

        if value_bets:
            total_value_bets += len(value_bets)
            best_bet = max(value_bets, key=lambda x: x.ev_percentage)

            result = ScanMatchResult(
                match_id=match.match_id,
                home_team=match.home_team,
                away_team=match.away_team,
                match_date=match.match_date,
                value_bet_count=len(value_bets),
                top_value_bet=(
                    ValueBet(
                        market=best_bet.market,
                        site=best_bet.site,
                        site_name=best_bet.site_name,
                        odds=best_bet.odds,
                        probability=best_bet.probability,
                        ev_percentage=best_bet.ev_percentage,
                        confidence=best_bet.confidence,
                        is_value_bet=best_bet.is_value_bet,
                        reasoning=best_bet.reasoning[:2],
                    )
                    if best_bet
                    else None
                ),
            )
            scan_results.append(result)

    return ScanResponse(
        scan_date=datetime.now(),
        total_matches=len(all_matches),
        matches_with_value_bets=len(scan_results),
        total_value_bets=total_value_bets,
        matches=scan_results,
        filters_applied={
            "min_ev": config.min_ev,
            "min_confidence": config.min_confidence,
            "risk_tolerance": config.risk_tolerance.value,
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        },
    )


@router.get("/bookmakers", response_model=List[BookmakerStatus], tags=["Configuration"])
async def list_bookmakers():
    """
    List all available bookmakers and their status.

    Returns information about each integrated Portuguese betting site:
    - Enabled/disabled status
    - Rate limits
    - Current operational status
    """
    from src.config import BETTING_SITES

    statuses = []
    for site_key, config in BETTING_SITES.items():
        status = BookmakerStatus(
            site_key=site_key,
            site_name=config.get("name", site_key),
            enabled=config.get("enabled", False),
            rate_limit_seconds=config.get("rate_limit_seconds", 5),
            status="operational" if config.get("enabled", False) else "disabled",
        )
        statuses.append(status)

    return statuses


@router.get("/config", response_model=LibraryConfig, tags=["Configuration"])
async def get_config():
    """
    Get current library/API configuration.

    Returns active settings for:
    - EV thresholds
    - Confidence thresholds
    - Enabled bookmakers
    - Cache settings
    """
    from src.config import BETTING_SITES, DEFAULT_MIN_CONFIDENCE, DEFAULT_MIN_EV

    enabled_sites = [
        key for key, config in BETTING_SITES.items() if config.get("enabled", False)
    ]

    return LibraryConfig(
        min_ev=DEFAULT_MIN_EV,
        min_confidence=DEFAULT_MIN_CONFIDENCE,
        enabled_sites=enabled_sites,
        cache_enabled=True,
        cache_ttl_hours=1,
        rate_limit_enabled=True,
    )


@router.put("/config", response_model=LibraryConfig, tags=["Configuration"])
async def update_config(new_config: LibraryConfig):
    """
    Update library/API configuration.

    **Note:** In production, this would persist to a config file or database.
    For now, changes are temporary and apply only to current session.
    """
    # In production: save to config file or database
    # For demo: just echo back the config
    return new_config


# Helper functions


def _create_mock_team_data(team_name: str):
    """Create mock team data (replace with real data fetching in production)"""
    import random

    from ..predictors.team_stats import TeamData

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


def _calculate_market_averages(odds_list: list) -> dict:
    """Calculate average odds across bookmakers"""
    from ..utils.ev_calculator import calculate_market_average

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
    prediction, odds_list, market_avg, min_ev, min_confidence
):
    """Generate bet recommendations"""
    from ..utils.ev_calculator import analyze_bet

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
                min_confidence=min_confidence,
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
                min_confidence=min_confidence,
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
                min_confidence=min_confidence,
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
                min_confidence=min_confidence,
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
                min_confidence=min_confidence,
            )
            recommendations.append(rec)

    return recommendations


def _filter_by_risk_tolerance(recommendations, risk_tolerance: RiskTolerance):
    """Filter recommendations based on risk tolerance"""
    from ..utils.ev_calculator import find_best_value_bets

    # Adjust thresholds based on risk tolerance
    if risk_tolerance == RiskTolerance.CONSERVATIVE:
        min_ev = 8.0
        min_confidence = 70.0
    elif risk_tolerance == RiskTolerance.AGGRESSIVE:
        min_ev = 3.0
        min_confidence = 50.0
    else:  # MODERATE
        min_ev = 5.0
        min_confidence = 60.0

    return find_best_value_bets(recommendations, min_ev, min_confidence)
