"""
Configuration for World Cup Betting Insights CLI

Portuguese licensed betting sites (SRIJ regulated):
https://www.srij.turismodeportugal.pt/
"""

# Betting sites configuration
BETTING_SITES = {
    "betano": {
        "name": "Betano.pt",
        "url": "https://www.betano.pt",
        "sports_url": "https://www.betano.pt/sport/",
        "enabled": True,
        "rate_limit_seconds": 5,
    },
    "betclic": {
        "name": "Betclic.pt",
        "url": "https://www.betclic.pt",
        "sports_url": "https://www.betclic.pt/futebol-s1/",
        "enabled": True,
        "rate_limit_seconds": 5,
    },
    "esc": {
        "name": "Esc Online",
        "url": "https://www.esconline.pt",
        "sports_url": "https://www.esconline.pt/sportsbook/futebol/",
        "enabled": True,
        "rate_limit_seconds": 5,
    },
    "solverde": {
        "name": "Solverde.pt",
        "url": "https://www.solverde.pt",
        "sports_url": "https://www.solverde.pt/apostas-desportivas/futebol/",
        "enabled": True,
        "rate_limit_seconds": 5,
    },
    "placard": {
        "name": "Placard.pt",
        "url": "https://www.placard.pt",
        "sports_url": "https://www.placard.pt/jogos-apostas-desportivas/futebol/",
        "enabled": True,
        "rate_limit_seconds": 5,
    },
    "nossaaposta": {
        "name": "NossaAposta.pt",
        "url": "https://www.nossaaposta.pt",
        "sports_url": "https://www.nossaaposta.pt/apostas-desportivas/futebol/",
        "enabled": False,  # Optional
        "rate_limit_seconds": 5,
    },
}

# Default thresholds
DEFAULT_MIN_EV = 5.0  # Minimum expected value percentage
DEFAULT_MIN_CONFIDENCE = 60.0  # Minimum confidence percentage
DEFAULT_ODDS_DISCREPANCY = 10.0  # Minimum odds discrepancy vs market average

# Data sources
DATA_SOURCES = {
    "fbref": "https://fbref.com/",
    "football_data": "https://www.football-data.org/",
    "api_football": "https://api-football.com/",
}

# Portuguese sports media for injury news
NEWS_SOURCES = [
    "https://www.record.pt/",
    "https://www.abola.pt/",
    "https://www.ojogo.pt/",
]

# User agents for scraping (rotate these)
USER_AGENTS = [
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
DISCLAIMER = """
⚠️  RESPONSIBLE GAMBLING DISCLAIMER
Gambling involves risk. Please bet responsibly.
This tool provides insights only - no guaranteed wins.
You must be 18+ to gamble in Portugal.
If you have a gambling problem, visit: https://www.srij.turismodeportugal.pt/
"""

# Market types
MARKET_TYPES = {
    "1X2": "Match Winner (Home/Draw/Away)",
    "OU25": "Over/Under 2.5 Goals",
    "BTTS": "Both Teams To Score",
    "AH": "Asian Handicap",
    "DC": "Double Chance",
    "GG": "Anytime Goalscorer",
}
