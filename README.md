# 🏆 World Cup Betting Insights CLI

A comprehensive command-line application and Python library for finding **value bets** in World Cup football matches by comparing AI-generated predictions against odds from Portuguese licensed betting sites.

## ⚠️ Responsible Gambling Disclaimer

**This tool provides insights only. No guaranteed wins.**

- You must be **18+** to gamble in Portugal
- Gambling involves risk - never bet more than you can afford to lose
- All integrated bookmakers are licensed by [SRIJ](https://www.srij.turismodeportugal.pt/)
- If you have a gambling problem, seek help at the SRIJ website

---

## Features

### 🔍 Core Capabilities

- **AI-Powered Predictions**: Statistical model generating win/draw/loss probabilities
- **Value Bet Detection**: Identify bets with positive Expected Value (EV)
- **Multi-Bookmaker Analysis**: Compare odds across Betano, Betclic, Solverde, and more
- **Multiple Interfaces**:
  - 🖥️ CLI for interactive use
  - 🌐 REST API for integrations
  - 📦 Python library for programmatic access

### 📊 Prediction Engine

The prediction model uses:
- **Team Strength**: ELO ratings, FIFA rankings
- **Recent Form**: Last 10 matches performance
- **Head-to-Head History**: Historical matchups
- **Advanced Metrics**: Expected goals (xG), possession stats
- **Tournament Context**: Must-win scenarios, rest days

### 🇵🇹 Portuguese Bookmakers

All integrated sites are **SRIJ-licensed**:

| Site | Status | Rate Limit |
|------|--------|------------|
| Betano.pt | ✅ Enabled | 5s |
| Betclic.pt | ✅ Enabled | 5s |
| Solverde.pt | ✅ Enabled | 5s |
| Esc Online | ⏸️ Disabled | 5s |
| Placard.pt | ⏸️ Disabled | 5s |

---

## Installation

### Prerequisites

- Python 3.10+
- pip (Python package manager)

### Quick Install

```bash
# Clone or navigate to the project
cd world-cup-betting-cli

# Install dependencies
pip install -r requirements.txt

# Install as editable package (optional)
pip install -e .
```

---

## CLI Usage

### Analyze a Specific Match

```bash
# Basic usage
python -m src.cli.main predict "Portugal vs Brazil"

# With specific bookmaker
python -m src.cli.main predict "Portugal vs Brazil" --site betano

# Custom EV threshold
python -m src.cli.main predict "Portugal vs Brazil" --min-ev 10

# JSON output
python -m src.cli.main predict "Portugal vs Brazil" --format json
```

### Scan Upcoming Matches

```bash
# Scan next 7 days
python -m src.cli.main scan

# Scan specific date
python -m src.cli.main scan --date 2026-06-15

# High EV threshold only
python -m src.cli.main scan --min-ev 15 --days 14
```

### Interactive Mode

```bash
python -m src.cli.main interactive
```

### Show Available Sites

```bash
python -m src.cli.main sites
```

---

## REST API

### Start the API Server

```bash
# Development mode with auto-reload
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --workers 4
```

### API Endpoints

#### Health Check
```bash
curl http://localhost:8000/api/v1/health
```

#### Get Available Bookmakers
```bash
curl http://localhost:8000/api/v1/bookmakers
```

#### Analyze a Match
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Portugal", "away_team": "Brazil"}'
```

#### Scan Upcoming Matches
```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"days_ahead": 7, "min_ev": 5.0}'
```

### API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## Python Library

Use the betting insights engine programmatically in your projects:

### Basic Usage

```python
from src.library import BettingInsights, create_insights

# Initialize with default settings
insights = BettingInsights(min_ev=5.0, min_confidence=60.0)

# Analyze a specific match
result = insights.analyze_match("Portugal", "Brazil")

print(f"Home win probability: {result.home_win_prob:.1%}")
print(f"Value bets found: {len(result.value_bets)}")

if result.has_value_bets:
    best = result.get_best_value_bet()
    print(f"Best bet: {best.market} @ {best.site_name}")
    print(f"EV: {best.ev_percentage:.1f}%")
```

### Scanning Multiple Matches

```python
from src.library import BettingInsights

insights = BettingInsights()

# Scan upcoming matches
scan_result = insights.scan_upcoming_matches(days_ahead=7)

print(f"Total matches: {scan_result.total_matches}")
print(f"Matches with value bets: {scan_result.matches_with_value_bets}")

# Get top value bets across all matches
top_bets = scan_result.get_top_value_bets(limit=5)
for bet in top_bets:
    print(f"{bet.market}: {bet.ev_percentage:.1f}% EV @ {bet.site_name}")
```

### Custom Configuration

```python
from src.library import create_insights

# Quick setup with custom thresholds
insights = create_insights(
    min_ev=8.0,
    min_confidence=70.0,
    enabled_sites=["betano", "betclic"]
)

# Or update config later
insights.update_config(
    min_ev=10.0,
    enabled_sites=["solverde"]
)
```

### Working with Results

```python
# Match analysis result
result = insights.analyze_match("Spain", "Germany")

# Access probabilities
print(f"Home: {result.home_win_prob:.1%}")
print(f"Draw: {result.draw_prob:.1%}")
print(f"Away: {result.away_win_prob:.1%}")

# Access market averages
print(f"Market avg home win: {result.market_avg_home}")

# Export to dictionary
data = result.to_dict()

# Scan result
scan = insights.scan_upcoming_matches()
all_bets = scan.all_value_bets
top_10 = scan.get_top_value_bets(limit=10)
```

---

## Architecture

```
src/
├── cli/                  # Command-line interface
│   └── main.py          # Click-based CLI
├── api/                  # REST API (FastAPI)
│   ├── app.py          # Application factory
│   ├── routes.py       # API endpoints
│   └── models.py       # Pydantic models
├── predictors/           # Prediction engine
│   ├── prediction_engine.py  # Main model
│   ├── team_stats.py   # Team data models
│   └── data_loader.py  # Data fetching/caching
├── scrapers/            # Bookmaker scrapers
│   ├── base_scraper.py # Abstract base class
│   ├── betano_scraper.py
│   ├── betclic_scraper.py
│   └── solverde_scraper.py
├── utils/               # Utilities
│   └── ev_calculator.py # EV calculations
└── library.py          # Python library interface
```

---

## Configuration

### Environment Variables

```bash
# Optional: API keys for data sources
FOOTBALL_DATA_API_KEY=your_api_key_here

# Optional: Custom cache directory
BETTING_CACHE_DIR=/path/to/cache
```

### Config File (Optional)

Create `config.yaml` for persistent settings:

```yaml
defaults:
  min_ev: 5.0
  min_confidence: 60.0
  
bookmakers:
  betano:
    enabled: true
  betclic:
    enabled: true
  solverde:
    enabled: true

cache:
  enabled: true
  ttl_hours: 1
```

---

## Testing

### Run All Tests

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio httpx

# Run tests with coverage
pytest --cov=src --cov-report=html
```

### Run Specific Test Files

```bash
# EV calculator tests
pytest tests/test_ev_calculator.py -v

# Prediction engine tests
pytest tests/test_prediction_engine.py -v

# Scraper tests
pytest tests/test_scrapers.py -v

# API tests
pytest tests/test_api.py -v

# Library tests
pytest tests/test_library.py -v
```

### Test Coverage Report

```bash
pytest --cov=src --cov-report=term-missing
```

---

## Expected Value (EV) Calculation

The core metric for identifying value bets:

```
EV = (Your Probability × Decimal Odds) - 1
```

**Example:**
- Your model predicts Brazil has 46% chance to win
- Betano offers odds of 2.25
- EV = (0.46 × 2.25) - 1 = 0.035 = **+3.5%**

A positive EV indicates a potentially profitable bet in the long run.

### Value Bet Criteria

By default, a bet qualifies as a "value bet" when:
- **EV > 5%** (configurable via `--min-ev`)
- **Confidence > 60%** (configurable via `--min-confidence`)

---

## Data Sources

### Free Sources (Implemented/Skeleton)
- **FBref.com**: Team statistics, player data
- **Football-Data.org**: Historical results (API)

### Portuguese Sports Media (For Injury News)
- Record.pt
- A Bola
- O Jogo

### Bookmaker Integration
- Direct scraping (with rate limiting)
- Official APIs (when available)

---

## Legal & Ethical Requirements

✅ **Compliant with Portuguese Regulations**

- Only SRIJ-licensed operators integrated
- No automated betting - insights only
- Rate limiting respects bookmaker policies
- User agent rotation for responsible scraping
- Clear responsible gambling messaging
- No guaranteed win claims

⚠️ **Important Notes**

- This tool is for **personal research only**
- Do not use for commercial purposes without proper licensing
- Respect each bookmaker's Terms of Service
- Scraping may be blocked by some sites

---

## Troubleshooting

### Common Issues

**"No odds available"**
- Bookmaker may be temporarily unavailable
- Check rate limiting settings
- Verify internet connection

**"Module not found"**
- Ensure you've installed dependencies: `pip install -r requirements.txt`
- Run from project root directory

**API server won't start**
- Check if port 8000 is already in use
- Try: `uvicorn src.api.app:app --port 8001`

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
python -m src.cli.main predict "Portugal vs Brazil" --verbose
```

---

## Development

### Setting Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

### Adding New Bookmakers

1. Create new scraper in `src/scrapers/`:
```python
from .base_scraper import BaseScraper, OddsData

class NewSiteScraper(BaseScraper):
    def get_match_odds(self, home_team, away_team, match_date=None):
        # Implement scraping logic
        pass
    
    def get_upcoming_matches(self, days_ahead=7):
        # Implement match listing
        pass
```

2. Add configuration to `src/config.py`:
```python
BETTING_SITES = {
    "newsite": {
        "name": "NewSite.pt",
        "url": "https://www.newsite.pt",
        "enabled": True,
        "rate_limit_seconds": 5,
    },
}
```

3. Update scraper factory in `src/cli/main.py` and `src/api/routes.py`

---

## License

This project is provided for educational and personal research purposes only.

**Disclaimer**: Gambling involves risk. This tool does not guarantee profits. Use responsibly and only if you are 18+.

---

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

---

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing documentation
- Review test files for usage examples

---

**Built with ❤️ for responsible sports betting analysis**
