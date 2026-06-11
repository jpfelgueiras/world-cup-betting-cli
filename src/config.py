"""
Configuration for World Cup Betting Insights CLI

Portuguese licensed betting sites (SRIJ regulated):
https://www.srij.turismodeportugal.pt/

Configuration values can be set via environment variables.
See .env.example for required/optional variables.
"""

import os
from typing import Any, Dict, List, Optional


def get_env_int(name: str, default: int) -> int:
    """Get integer from environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def get_env_float(name: str, default: float) -> float:
    """Get float from environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        return default


def get_env_bool(name: str, default: bool) -> bool:
    """Get boolean from environment variable."""
    value = os.getenv(name, "").lower()
    if value in ("true", "1", "yes"):
        return True
    if value in ("false", "0", "no"):
        return False
    return default


def get_env_list(name: str, default: List[str]) -> List[str]:
    """Get comma-separated list from environment variable."""
    value = os.getenv(name)
    if value is None:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def validate_required_env_vars() -> List[str]:
    """
    Validate that required environment variables are set.

    Returns:
        List of missing required environment variable names
    """
    missing = []

    # Check API keys that should be set in production
    if not os.getenv("FBREF_API_KEY") and not os.getenv("FOOTBALL_DATA_API_KEY"):
        # At least one data source should be configured
        pass  # Not strictly required for mock mode

    return missing


# Betting sites configuration
BETTING_SITES: Dict[str, Dict[str, Any]] = {
    "betano": {
        "name": "Betano.pt",
        "url": os.getenv("BETANO_URL", "https://www.betano.pt"),
        "sports_url": os.getenv(
            "BETANO_SPORTS_URL", "https://www.betano.pt/sport/"
        ),
        "enabled": get_env_bool("BETANO_ENABLED", True),
        "rate_limit_seconds": get_env_int("BETANO_RATE_LIMIT", 5),
    },
    "betclic": {
        "name": "Betclic.pt",
        "url": os.getenv("BETCLIC_URL", "https://www.betclic.pt"),
        "sports_url": os.getenv(
            "BETCLIC_SPORTS_URL", "https://www.betclic.pt/futebol-s1/"
        ),
        "enabled": get_env_bool("BETCLIC_ENABLED", True),
        "rate_limit_seconds": get_env_int("BETCLIC_RATE_LIMIT", 5),
    },
    "esc": {
        "name": "Esc Online",
        "url": os.getenv("ESC_URL", "https://www.esconline.pt"),
        "sports_url": os.getenv(
            "ESC_SPORTS_URL", "https://www.esconline.pt/sportsbook/futebol/"
        ),
        "enabled": get_env_bool("ESC_ENABLED", True),
        "rate_limit_seconds": get_env_int("ESC_RATE_LIMIT", 5),
    },
    "solverde": {
        "name": "Solverde.pt",
        "url": os.getenv("SOLVERDE_URL", "https://www.solverde.pt"),
        "sports_url": os.getenv(
            "SOLVERDE_SPORTS_URL",
            "https://www.solverde.pt/apostas-desportivas/futebol/",
        ),
        "enabled": get_env_bool("SOLVERDE_ENABLED", True),
        "rate_limit_seconds": get_env_int("SOLVERDE_RATE_LIMIT", 5),
    },
    "placard": {
        "name": "Placard.pt",
        "url": os.getenv("PLACARD_URL", "https://www.placard.pt"),
        "sports_url": os.getenv(
            "PLACARD_SPORTS_URL",
            "https://www.placard.pt/jogos-apostas-desportivas/futebol/",
        ),
        "enabled": get_env_bool("PLACARD_ENABLED", True),
        "rate_limit_seconds": get_env_int("PLACARD_RATE_LIMIT", 5),
    },
    "nossaaposta": {
        "name": "NossaAposta.pt",
        "url": os.getenv("NOSSAAPOSTA_URL", "https://www.nossaaposta.pt"),
        "sports_url": os.getenv(
            "NOSSAAPOSTA_SPORTS_URL",
            "https://www.nossaaposta.pt/apostas-desportivas/futebol/",
        ),
        "enabled": get_env_bool("NOSSAAPOSTA_ENABLED", False),
        "rate_limit_seconds": get_env_int("NOSSAAPOSTA_RATE_LIMIT", 5),
    },
}

# Default thresholds
DEFAULT_MIN_EV: float = get_env_float("MIN_EV_THRESHOLD", 5.0)
DEFAULT_MIN_CONFIDENCE: float = get_env_float(
    "MIN_CONFIDENCE_THRESHOLD", 60.0
)
DEFAULT_ODDS_DISCREPANCY: float = get_env_float(
    "ODDS_DISCREPANCY_THRESHOLD", 10.0
)

# Data sources
DATA_SOURCES: Dict[str, str] = {
    "fbref": os.getenv("FBREF_URL", "https://fbref.com/"),
    "football_data": os.getenv(
        "FOOTBALL_DATA_URL", "https://www.football-data.org/"
    ),
    "api_football": os.getenv(
        "API_FOOTBALL_URL", "https://api-football.com/"
    ),
}

# API keys (should be set via environment variables in production)
FBREF_API_KEY: Optional[str] = os.getenv("FBREF_API_KEY")
FOOTBALL_DATA_API_KEY: Optional[str] = os.getenv("FOOTBALL_DATA_API_KEY")
API_FOOTBALL_API_KEY: Optional[str] = os.getenv("API_FOOTBALL_API_KEY")

# Portuguese sports media for injury news
NEWS_SOURCES: List[str] = get_env_list(
    "NEWS_SOURCES",
    [
        "https://www.record.pt/",
        "https://www.abola.pt/",
        "https://www.ojogo.pt/",
    ],
)

# User agents for scraping (rotate these)
USER_AGENTS: List[str] = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
]

# Responsible gambling disclaimer
DISCLAIMER: str = """
⚠️  RESPONSIBLE GAMBLING DISCLAIMER
Gambling involves risk. Please bet responsibly.
This tool provides insights only - no guaranteed wins.
You must be 18+ to gamble in Portugal.
If you have a gambling problem, visit: https://www.srij.turismodeportugal.pt/
"""

# Market types
MARKET_TYPES: Dict[str, str] = {
    "1X2": "Match Winner (Home/Draw/Away)",
    "OU25": "Over/Under 2.5 Goals",
    "BTTS": "Both Teams To Score",
    "AH": "Asian Handicap",
    "DC": "Double Chance",
    "GG": "Anytime Goalscorer",
}

# Logging configuration
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE: Optional[str] = os.getenv("LOG_FILE")
LOG_STRUCTURED: bool = get_env_bool("LOG_STRUCTURED", False)

# Rate limiting configuration
RATE_LIMIT_PER_IP: int = get_env_int("RATE_LIMIT_PER_IP", 100)
RATE_LIMIT_WINDOW_SECONDS: int = get_env_int("RATE_LIMIT_WINDOW_SECONDS", 60)

# Security configuration
API_KEY_HEADER: str = os.getenv("API_KEY_HEADER", "X-API-Key")
CORS_ORIGINS: List[str] = get_env_list(
    "CORS_ORIGINS", ["http://localhost:3000", "http://localhost:8000"]
)
ENABLE_CORS: bool = get_env_bool("ENABLE_CORS", True)

# Monitoring configuration
SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN")
PROMETHEUS_PORT: int = get_env_int("PROMETHEUS_PORT", 9090)
ENABLE_METRICS: bool = get_env_bool("ENABLE_METRICS", False)
