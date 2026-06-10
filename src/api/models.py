"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MarketType(str, Enum):
    """Supported betting market types"""
    MATCH_WINNER = "1X2"
    OVER_UNDER_25 = "OU25"
    BTTS = "BTTS"
    ASIAN_HANDICAP = "AH"
    DOUBLE_CHANCE = "DC"


class SiteType(str, Enum):
    """Supported Portuguese betting sites"""
    BETANO = "betano"
    BETCLIC = "betclic"
    ESC = "esc"
    SOLVERDE = "solverde"
    PLACARD = "placard"
    NOSSAAPOSTA = "nossaaposta"
    ALL = "all"


class RiskTolerance(str, Enum):
    """Risk tolerance levels"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


class OutputFormat(str, Enum):
    """Output format options"""
    TABLE = "table"
    JSON = "json"
    CSV = "csv"


# Request Models

class MatchPredictionRequest(BaseModel):
    """Request model for match prediction"""
    home_team: str = Field(..., min_length=1, description="Home team name")
    away_team: str = Field(..., min_length=1, description="Away team name")
    match_date: Optional[datetime] = Field(None, description="Optional match date")
    site: SiteType = Field(SiteType.ALL, description="Betting site to analyze")

    class Config:
        json_schema_extra = {
            "example": {
                "home_team": "Portugal",
                "away_team": "Brazil",
                "match_date": "2026-06-15T20:00:00Z",
                "site": "all"
            }
        }


class ScanRequest(BaseModel):
    """Request model for scanning upcoming matches"""
    start_date: Optional[datetime] = Field(None, description="Start date for scan")
    end_date: Optional[datetime] = Field(None, description="End date for scan")
    days_ahead: int = Field(7, ge=1, le=30, description="Days to scan ahead")
    min_ev: float = Field(5.0, ge=0, le=100, description="Minimum EV threshold %")
    min_confidence: float = Field(60.0, ge=0, le=100, description="Minimum confidence %")
    site: SiteType = Field(SiteType.ALL, description="Betting site filter")

    class Config:
        json_schema_extra = {
            "example": {
                "days_ahead": 7,
                "min_ev": 5.0,
                "min_confidence": 60.0,
                "site": "all"
            }
        }


class AnalysisConfig(BaseModel):
    """Configuration for bet analysis"""
    min_ev: float = Field(5.0, ge=0, le=100, description="Minimum EV threshold %")
    min_confidence: float = Field(60.0, ge=0, le=100, description="Minimum confidence %")
    risk_tolerance: RiskTolerance = Field(RiskTolerance.MODERATE, description="Risk tolerance level")
    markets: List[MarketType] = Field(
        default_factory=lambda: [MarketType.MATCH_WINNER, MarketType.OVER_UNDER_25, MarketType.BTTS],
        description="Markets to analyze"
    )

    @field_validator('min_ev')
    @classmethod
    def validate_min_ev(cls, v):
        if v < 0 or v > 100:
            raise ValueError('min_ev must be between 0 and 100')
        return v


# Response Models

class TeamProbabilities(BaseModel):
    """Team win/draw/loss probabilities"""
    home_win: float = Field(..., ge=0, le=1, description="Home win probability")
    draw: float = Field(..., ge=0, le=1, description="Draw probability")
    away_win: float = Field(..., ge=0, le=1, description="Away win probability")
    over_2_5: float = Field(..., ge=0, le=1, description="Over 2.5 goals probability")
    btts: float = Field(..., ge=0, le=1, description="Both teams to score probability")

    @field_validator('home_win', 'draw', 'away_win')
    @classmethod
    def validate_probabilities(cls, values):
        # Note: This validator runs on individual fields, not the whole set
        return values


class ConfidenceLevels(BaseModel):
    """Confidence levels for predictions"""
    home_win: float = Field(..., ge=0, le=100, description="Home win confidence %")
    draw: float = Field(..., ge=0, le=100, description="Draw confidence %")
    away_win: float = Field(..., ge=0, le=100, description="Away win confidence %")


class MarketAverage(BaseModel):
    """Market average odds across bookmakers"""
    home_win: Optional[float] = Field(None, gt=1, description="Average home win odds")
    draw: Optional[float] = Field(None, gt=1, description="Average draw odds")
    away_win: Optional[float] = Field(None, gt=1, description="Average away win odds")
    over_2_5: Optional[float] = Field(None, gt=1, description="Average over 2.5 odds")
    btts_yes: Optional[float] = Field(None, gt=1, description="Average BTTS yes odds")
    num_bookmakers: int = Field(..., ge=0, description="Number of bookmakers analyzed")


class ValueBet(BaseModel):
    """A value bet recommendation"""
    market: str = Field(..., description="Betting market type")
    site: str = Field(..., description="Betting site identifier")
    site_name: str = Field(..., description="Human-readable site name")
    odds: float = Field(..., gt=1, description="Decimal odds")
    probability: float = Field(..., ge=0, le=1, description="Model probability")
    ev_percentage: float = Field(..., description="Expected value percentage")
    confidence: float = Field(..., ge=0, le=100, description="Confidence percentage")
    is_value_bet: bool = Field(..., description="Whether this qualifies as a value bet")
    reasoning: List[str] = Field(default_factory=list, description="Reasoning factors")


class MatchAnalysisResponse(BaseModel):
    """Complete match analysis response"""
    match_id: str = Field(..., description="Unique match identifier")
    home_team: str = Field(..., description="Home team name")
    away_team: str = Field(..., description="Away team name")
    match_date: Optional[datetime] = Field(None, description="Match date/time")
    tournament_stage: Optional[str] = Field(None, description="Tournament stage")

    probabilities: TeamProbabilities = Field(..., description="Model probabilities")
    confidence: ConfidenceLevels = Field(..., description="Confidence levels")
    market_averages: MarketAverage = Field(..., description="Market average odds")

    value_bets: List[ValueBet] = Field(..., description="Recommended value bets")
    key_factors: List[str] = Field(..., description="Key analysis factors")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "match_id": "portugal_vs_brazil_20260615",
                "home_team": "Portugal",
                "away_team": "Brazil",
                "match_date": "2026-06-15T20:00:00Z",
                "tournament_stage": "Group Stage",
                "probabilities": {
                    "home_win": 0.28,
                    "draw": 0.26,
                    "away_win": 0.46,
                    "over_2_5": 0.62,
                    "btts": 0.58
                },
                "confidence": {
                    "home_win": 65.0,
                    "draw": 55.0,
                    "away_win": 72.0
                },
                "market_averages": {
                    "home_win": 3.20,
                    "draw": 3.40,
                    "away_win": 2.10,
                    "over_2_5": 1.90,
                    "btts_yes": 1.75,
                    "num_bookmakers": 3
                },
                "value_bets": [
                    {
                        "market": "1X2 - Away Win",
                        "site": "betano",
                        "site_name": "Betano.pt",
                        "odds": 2.25,
                        "probability": 0.46,
                        "ev_percentage": 8.5,
                        "confidence": 72.0,
                        "is_value_bet": True,
                        "reasoning": ["Brazil unbeaten in last 12 matches"]
                    }
                ],
                "key_factors": [
                    "Brazil in excellent form (80% last 10)",
                    "Brazil dominates historical H2H"
                ]
            }
        }


class ScanMatchResult(BaseModel):
    """Single match result from scan"""
    match_id: str
    home_team: str
    away_team: str
    match_date: Optional[datetime]
    value_bet_count: int
    top_value_bet: Optional[ValueBet] = None


class ScanResponse(BaseModel):
    """Response for match scan operation"""
    scan_date: datetime = Field(default_factory=datetime.now)
    total_matches: int = Field(..., description="Total matches scanned")
    matches_with_value_bets: int = Field(..., description="Matches with at least one value bet")
    total_value_bets: int = Field(..., description="Total value bets found")
    matches: List[ScanMatchResult] = Field(..., description="Match results")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters used in scan")


class OddsData(BaseModel):
    """Odds data from a single bookmaker"""
    match_id: str
    home_team: str
    away_team: str
    match_date: Optional[datetime]
    site: str
    site_name: str
    home_win: Optional[float] = None
    draw: Optional[float] = None
    away_win: Optional[float] = None
    over_2_5: Optional[float] = None
    under_2_5: Optional[float] = None
    btts_yes: Optional[float] = None
    btts_no: Optional[float] = None
    last_updated: Optional[datetime] = None
    url: Optional[str] = None


class BookmakerStatus(BaseModel):
    """Status of a bookmaker integration"""
    site_key: str
    site_name: str
    enabled: bool
    rate_limit_seconds: int
    last_request: Optional[datetime] = None
    total_requests: int = 0
    status: str = "operational"  # operational, degraded, unavailable


class HealthResponse(BaseModel):
    """API health check response"""
    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)
    bookmakers: List[BookmakerStatus] = []
    prediction_engine: str = "operational"
    database: str = "connected"


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    code: str
    details: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Invalid team name provided",
                "code": "INVALID_INPUT",
                "details": {"field": "home_team", "reason": "empty string"}
            }
        }


class LibraryConfig(BaseModel):
    """Configuration for library usage"""
    min_ev: float = 5.0
    min_confidence: float = 60.0
    enabled_sites: List[str] = Field(default_factory=lambda: ["betano", "betclic", "solverde"])
    cache_enabled: bool = True
    cache_ttl_hours: int = 1
    rate_limit_enabled: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "min_ev": 5.0,
                "min_confidence": 60.0,
                "enabled_sites": ["betano", "betclic"],
                "cache_enabled": True,
                "cache_ttl_hours": 1
            }
        }
