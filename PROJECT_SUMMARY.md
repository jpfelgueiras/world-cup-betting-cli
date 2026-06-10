# Project Summary

This document gives a fast but accurate overview of what is in the repository today.

## Snapshot

**World Cup Betting Insights CLI** is a Python codebase that combines:

- a Click-based CLI,
- a FastAPI HTTP API,
- a reusable Python library,
- a prediction engine for football outcomes, and
- bookmaker adapters normalized into a shared odds model.

The project focuses on spotting potential **value bets** by comparing model probabilities with bookmaker odds.

## What is implemented

### User-facing interfaces

- **CLI** in `src/cli/main.py`
- **REST API** in `src/api/`
- **Library facade** in `src/library.py`

### Core analysis pieces

- `PredictionEngine` in `src/predictors/prediction_engine.py`
- `TeamData`, `TeamStats`, and `MatchContext` in `src/predictors/team_stats.py`
- EV and recommendation helpers in `src/utils/ev_calculator.py`

### Persistence and support

- SQLite-backed cache/logging helper in `src/predictors/data_loader.py`
- Shared bookmaker configuration in `src/config.py`
- Shared scraper abstraction in `src/scrapers/base_scraper.py`

### Scrapers currently present

- `BetanoScraper`
- `BetclicScraper`
- `SolverdeScraper`

## What the code is best described as

This repository is a **structured prototype** rather than a fully productionized betting platform.

That distinction matters because the codebase includes both:

- genuinely useful architecture and test coverage, and
- mock/demo behavior in parts of the data-collection path.

### Specifically

- direct match odds methods return deterministic mock odds
- “upcoming matches” flows may also use mock fixture data
- team statistics are often mock-generated in CLI/API flows
- loader classes for external football data are still partial scaffolding

## End-to-end flow

A typical analysis works like this:

1. Teams are supplied through the CLI, API, or library
2. Team data objects are built
3. The prediction engine estimates expected goals and outcome probabilities
4. Scrapers provide bookmaker odds in normalized `OddsData` objects
5. EV is calculated for each market/opportunity
6. Bets are filtered by EV and confidence thresholds
7. The top recommendations are returned to the caller

## Main markets represented

- Match winner (1X2)
- Over/Under 2.5 goals
- Both teams to score (BTTS)
- Some structural support for additional markets

## Package and runtime details

- Python 3.10+
- Console script: `worldcup`
- Package metadata defined in `setup.py`
- Dependencies listed in `requirements.txt`

## CI and quality checks

GitHub Actions currently runs:

- tests across Python 3.10–3.13
- coverage reporting
- flake8
- black
- isort
- mypy

## Where to read next

- Start with [README.md](README.md) for a full project guide
- Use [TESTING.md](TESTING.md) for development and verification details
- Inspect `src/library.py` if you want the clearest high-level integration surface

## Most important caveat

The project is promising and well organized, but documentation and usage should stay honest about the current state:

- **good foundation** ✅
- **good tests** ✅
- **clear interfaces** ✅
- **fully live production data pipeline** ❌
- **production-ready betting automation** ❌
