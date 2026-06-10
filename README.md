# 🏆 World Cup Betting Insights CLI

A Python project for analyzing football betting markets by comparing model-generated match probabilities with odds from Portuguese bookmakers.

The repository currently ships three ways to use the same core logic:

- **CLI** for ad-hoc local analysis
- **FastAPI app** for HTTP integrations
- **Python library** for embedding the engine in other code

> **Important:** the current implementation is best understood as a well-structured prototype/demo. Several integrations use deterministic mock data and skeleton scraper implementations rather than production-grade live feeds.

## ⚠️ Responsible gambling

This software is for analysis only.

- No guaranteed wins
- Use only where legal
- In Portugal, gambling is restricted to adults (18+)
- Only use licensed operators
- Never bet more than you can afford to lose

If gambling is becoming a problem, seek help through the Portuguese regulator: <https://www.srij.turismodeportugal.pt/>

---

## Table of contents

- [What this project does](#what-this-project-does)
- [Current status and realism](#current-status-and-realism)
- [Architecture overview](#architecture-overview)
- [Repository layout](#repository-layout)
- [Installation](#installation)
- [Quick start](#quick-start)
- [CLI guide](#cli-guide)
- [REST API guide](#rest-api-guide)
- [Python library guide](#python-library-guide)
- [How predictions are produced](#how-predictions-are-produced)
- [How value bets are identified](#how-value-bets-are-identified)
- [Bookmaker integrations](#bookmaker-integrations)
- [Data and caching](#data-and-caching)
- [Development workflow](#development-workflow)
- [Testing and quality checks](#testing-and-quality-checks)
- [Known limitations](#known-limitations)
- [Roadmap ideas](#roadmap-ideas)

---

## What this project does

At a high level, the project:

1. Builds a match prediction for two teams
2. Collects bookmaker odds for relevant markets
3. Compares model probability vs market price
4. Computes **expected value (EV)**
5. Returns bets that pass configurable EV and confidence thresholds

Markets currently represented in the codebase include:

- **1X2** (home win / draw / away win)
- **Over/Under 2.5 goals**
- **Both teams to score (BTTS)**
- Structural placeholders for additional markets such as Asian handicap and double chance

---

## Current status and realism

This is the most important thing to know before using or extending the project.

### What is real

- The project structure is real and coherent
- The CLI, API, and library interfaces are implemented
- The prediction engine, EV calculator, and test suite are present
- SQLite caching infrastructure exists
- GitHub Actions CI is configured

### What is mocked or incomplete

- Team data is largely generated from helper functions rather than live sources
- Scrapers return **deterministic mock odds** for direct match analysis
- Some “upcoming matches” flows fall back to mock fixtures
- Data source classes such as `FBrefLoader` are mostly scaffolding
- The interactive CLI mode is intentionally minimal

### Practical interpretation

Use this repository as:

- a **prototype**,
- a **teaching/reference implementation**, or
- a **foundation for a fuller betting analysis tool**.

Do **not** treat it as a production-ready automated betting platform.

---

## Architecture overview

The code is organized so each layer has a clear job.

```text
CLI / API / Library
        │
        ▼
Prediction engine + recommendation logic
        │
        ├── Team stats / match context
        ├── EV calculator
        └── Bookmaker scrapers
                │
                └── Optional cache / persistence layer
```

### Main components

#### 1. CLI (`src/cli/main.py`)
Provides commands for:
- single-match analysis
- multi-match scanning
- site listing
- a minimal interactive shell

#### 2. API (`src/api/`)
FastAPI application exposing HTTP endpoints for:
- health checks
- match prediction
- match scanning
- configuration-shaped request parameters

#### 3. Library (`src/library.py`)
A higher-level Python API centered on the `BettingInsights` class, which coordinates:
- prediction generation
- scraper selection
- market-average calculations
- value-bet filtering

#### 4. Prediction engine (`src/predictors/`)
The project’s modeling layer:
- computes expected goals
- converts them to result probabilities via Poisson logic
- derives confidence scores
- generates reasoning snippets

#### 5. Scrapers (`src/scrapers/`)
Site adapters that normalize bookmaker odds into a shared `OddsData` structure.

#### 6. EV utilities (`src/utils/ev_calculator.py`)
Implements the expected-value math and recommendation filtering.

---

## Repository layout

```text
world-cup-betting-cli/
├── .github/workflows/        # CI workflows
├── data/cache/               # SQLite cache location
├── src/
│   ├── api/                  # FastAPI app, routes, models
│   ├── cli/                  # Click CLI
│   ├── predictors/           # Prediction engine, team stats, cache/data loading
│   ├── scrapers/             # Bookmaker adapters
│   ├── utils/                # EV calculations and helpers
│   ├── config.py             # Project configuration/constants
│   ├── library.py            # Public Python library interface
│   └── __init__.py           # Package metadata
├── tests/                    # Unit tests
├── README.md                 # Main documentation
├── TESTING.md                # Testing guide
├── PROJECT_SUMMARY.md        # Project walkthrough and status summary
├── requirements.txt          # Runtime + test dependencies
└── setup.py                  # Packaging and console entry point
```

---

## Installation

### Prerequisites

- Python **3.10+**
- `pip`
- Optional: a virtual environment

### Recommended setup

```bash
git clone https://github.com/jpfelgueiras/world-cup-betting-cli.git
cd world-cup-betting-cli
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

Installing with `-e` exposes the `worldcup` console command during development.

---

## Quick start

### CLI

```bash
worldcup predict "Portugal vs Brazil"
worldcup scan --days 7 --min-ev 10
worldcup sites
```

### API

```bash
uvicorn src.api.app:app --reload
curl http://127.0.0.1:8000/api/v1/health
```

### Python

```python
from src.library import BettingInsights

insights = BettingInsights(min_ev=5.0, min_confidence=60.0)
result = insights.analyze_match("Portugal", "Brazil")

print(result.most_likely_outcome)
print(result.has_value_bets)
```

---

## CLI guide

The package installs a `worldcup` command via `setup.py`.

### `worldcup predict`

Analyze a single fixture.

```bash
worldcup predict "Portugal vs Brazil"
worldcup predict "Portugal vs Brazil" --site betano
worldcup predict "Portugal vs Brazil" --min-ev 8 --min-confidence 65
worldcup predict "Portugal vs Brazil" --format json
worldcup predict "Portugal vs Brazil" --format csv
```

#### Inputs

- Match string must look like `Team A vs Team B` or `Team A versus Team B`
- `--site` accepts `betano`, `betclic`, `solverde`, or `all`
- `--format` accepts `table`, `json`, or `csv`

#### What happens internally

- Team names are split from the input string
- Mock team data is created
- `PredictionEngine.predict_match()` is called
- Selected scraper instances provide odds
- Market averages are computed
- Recommendations are filtered by EV/confidence thresholds
- Output is rendered in the requested format

### `worldcup scan`

Scan upcoming fixtures.

```bash
worldcup scan
worldcup scan --days 14 --min-ev 12
worldcup scan --site betclic
worldcup scan --date 2026-06-15
```

#### Notes

- The `--date` option validates the date format but the current scan flow still works primarily from scraper-provided upcoming matches.
- Because scraper implementations are mostly mock-based, scan results are currently demo-oriented.

### `worldcup sites`

Shows configured bookmakers, URLs, status flags, and rate limits.

### `worldcup interactive`

Provides a small interactive prompt for trying core actions.

This mode is intentionally lightweight and not yet a full TUI/workbench.

---

## REST API guide

The API app is created in `src/api/app.py` and routes live in `src/api/routes.py`.

### Run locally

```bash
uvicorn src.api.app:app --reload --host 127.0.0.1 --port 8000
```

### Docs UIs

- Swagger UI: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>

### Root endpoint

```bash
curl http://127.0.0.1:8000/
```

Returns API metadata and doc links.

### Health check

```bash
curl http://127.0.0.1:8000/api/v1/health
```

Reports:
- package version
- bookmaker status stubs
- prediction engine state
- database/cache status summary

### Predict endpoint

```bash
curl -X POST http://127.0.0.1:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "home_team": "Portugal",
    "away_team": "Brazil",
    "site": "all"
  }'
```

### Scan endpoint

```bash
curl -X POST http://127.0.0.1:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{
    "days_ahead": 7,
    "site": "all"
  }'
```

### Query-based analysis configuration

Several thresholds are supplied via query parameters through the `AnalysisConfig` dependency:

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/predict?min_ev=8&min_confidence=65&risk_tolerance=moderate" \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Spain", "away_team": "Germany"}'
```

### API models

`src/api/models.py` defines typed request/response contracts for:
- match prediction requests
- scans
- analysis config
- value bets
- match analysis responses
- health responses
- standardized errors

---

## Python library guide

The public library entry point is `src/library.py`.

### Main class: `BettingInsights`

```python
from src.library import BettingInsights

insights = BettingInsights(
    min_ev=5.0,
    min_confidence=60.0,
    enabled_sites=["betano", "betclic"],
    cache_enabled=True,
)
```

### Primary methods

#### Analyze one match

```python
result = insights.analyze_match("France", "Argentina")

print(result.home_win_prob)
print(result.draw_prob)
print(result.away_win_prob)
print(result.value_bets)
```

#### Scan multiple matches

```python
scan = insights.scan_upcoming_matches(days_ahead=7)
print(scan.total_matches)
print(scan.matches_with_value_bets)
print(scan.get_top_value_bets(limit=5))
```

#### Inspect bookmaker configuration

```python
bookmakers = insights.get_bookmakers_info()
for bookmaker in bookmakers:
    print(bookmaker)
```

#### Update configuration

```python
insights.update_config(min_ev=10.0, enabled_sites=["solverde"])
```

### Result objects

#### `MatchAnalysisResult`
Contains:
- teams and optional match date
- win/draw/loss probabilities
- secondary market probabilities
- per-outcome confidence
- market averages
- list of `BetRecommendation`s
- derived helpers like `most_likely_outcome`, `has_value_bets`, and `get_best_value_bet()`

#### `ScanResult`
Contains:
- aggregate counts
- per-match analyses
- helper accessors like `all_value_bets` and `get_top_value_bets()`

---

## How predictions are produced

The prediction engine is in `src/predictors/prediction_engine.py`.

### Inputs considered

The engine combines several simplified signals:

- FIFA ranking
- ELO rating
- recent results
- goals scored and conceded
- expected goals (xG) for and against
- possession
- clean sheets
- head-to-head stats
- rest days / must-win context
- missing key players

### Modeling flow

1. `TeamData` captures raw team information
2. `TeamStats` derives attack, defense, overall strength, and form
3. Expected goals are estimated for both teams
4. A Poisson model turns expected goals into scoreline probabilities
5. Scoreline matrix is collapsed into:
   - home win
   - draw
   - away win
6. Secondary markets are estimated:
   - over 2.5 goals
   - BTTS
7. Confidence levels and reasoning bullets are generated

### Why Poisson?

Poisson models are a common baseline for football score prediction because goals are low-count events. This implementation uses a compact, readable version rather than a heavily calibrated production model.

---

## How value bets are identified

The EV logic lives in `src/utils/ev_calculator.py`.

### Core formula

```text
EV = (probability × decimal_odds) - 1
```

The project returns EV as a percentage:

```text
EV% = ((probability × decimal_odds) - 1) × 100
```

### Value-bet criteria

By default, a recommendation is considered a value bet only when:

- `EV% > 5.0`
- `confidence > 60.0`

These thresholds can be overridden in the CLI, API, or library interface.

### Recommendation flow

For each available market:

1. Take model probability
2. Take bookmaker odds
3. Compute EV
4. Attach confidence and reasoning
5. Filter via `is_value_bet()`
6. Sort descending by EV

---

## Bookmaker integrations

Configured bookmaker metadata lives in `src/config.py`.

### Enabled in code

- `betano`
- `betclic`
- `esc`
- `solverde`
- `placard`
- `nossaaposta` (disabled by default)

### Actually implemented scraper classes

- `BetanoScraper`
- `BetclicScraper`
- `SolverdeScraper`

### Important nuance

Not every configured bookmaker has a concrete scraper implementation wired into the CLI/API/library paths.

The current active code paths primarily use:
- Betano
- Betclic
- Solverde

### Scraper behavior today

The scraper classes include:
- a shared base class with request session handling
- retry and rate-limit helpers
- team-name normalization
- deterministic mock odds generation

This keeps the interfaces testable without depending on live bookmaker sites.

---

## Data and caching

`src/predictors/data_loader.py` provides a lightweight persistence layer.

### Cache location

By default, the SQLite database is stored at:

```text
data/cache/odds_history.db
```

### Tables

#### `odds_cache`
Stores normalized bookmaker odds snapshots.

#### `predictions_log`
Stores predictions for later accuracy analysis.

### Available capabilities

- initialize cache database automatically
- save odds snapshots
- fetch recently cached odds for a match
- log predictions
- compute simple historical accuracy statistics

### Current reality

The infrastructure exists, but the full end-to-end live ingestion story is still incomplete. It’s a useful base for future extensions.

---

## Development workflow

### Install dev dependencies

Everything currently lives in `requirements.txt`, including runtime and test tools.

```bash
pip install -r requirements.txt
pip install -e .
```

### Typical local loop

```bash
git checkout -b docs-or-feature-branch
pytest tests/ -v
worldcup predict "Portugal vs Brazil"
uvicorn src.api.app:app --reload
```

### Entry points worth knowing

- CLI: `src/cli/main.py`
- API app: `src/api/app.py`
- API routes: `src/api/routes.py`
- Library facade: `src/library.py`
- Prediction engine: `src/predictors/prediction_engine.py`
- EV math: `src/utils/ev_calculator.py`

### Packaging

`setup.py` defines:
- package name: `world-cup-betting-insights`
- console script: `worldcup`
- Python support: 3.10–3.13

---

## Testing and quality checks

The test suite lives under `tests/` and covers:

- EV calculations
- prediction engine behavior
- scraper behavior
- API routes/models
- library interface

### Run the main suite

```bash
PYTHONPATH=src pytest tests/ -v
```

### Run coverage

```bash
PYTHONPATH=src pytest tests/ --cov=src --cov-report=term-missing
```

### Existing CI

GitHub Actions runs:
- tests across Python 3.10–3.13
- coverage export
- flake8
- black check
- isort check
- mypy

See `.github/workflows/tests.yml`.

For more detail, read [TESTING.md](TESTING.md).

---

## Known limitations

A few are worth calling out explicitly.

1. **Live data is incomplete**  
   Several flows rely on mock data rather than real upstream feeds.

2. **Production scraper hardening is not done**  
   Real-world anti-bot handling, HTML drift, legal review, and site-specific parsing are still needed.

3. **Model calibration is lightweight**  
   The prediction engine is interpretable and testable, but not obviously backtested enough for serious staking decisions.

4. **Some docs in older files overstate completeness**  
   The codebase is solid, but parts of it remain prototype-grade.

5. **Configured bookmakers outnumber implemented scrapers**  
   `config.py` contains more bookmaker entries than are actively integrated in the main execution paths.

6. **Interactive mode is minimal**  
   It is more of a demo shell than a full analyst workflow.

---

## Roadmap ideas

If you want to take the project from prototype toward production, the next useful steps would be:

1. Replace mock team data with real fetchers
2. Finish live bookmaker parsing for each supported site
3. Add stronger calibration/backtesting for the model
4. Separate runtime dependencies from dev/test dependencies
5. Add richer logging and structured observability
6. Persist historical odds and outcomes more systematically
7. Add containerization and deployment docs
8. Expand the API with pagination/history endpoints

---

## Related docs

- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) — compact project overview
- [TESTING.md](TESTING.md) — testing workflow, coverage, and CI notes

If you’re new to the repo, start here in `README.md`, then read the project summary, then inspect the core modules.
