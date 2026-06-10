# Testing Guide

This guide explains how to validate the project locally and what the current automated checks cover.

## Test suite overview

The repository contains unit and interface-level tests for the main building blocks:

- `tests/test_ev_calculator.py` — expected value helpers
- `tests/test_prediction_engine.py` — prediction engine and derived team stats
- `tests/test_scrapers.py` — scraper base behavior and bookmaker adapters
- `tests/test_scraper_integration_real_fixtures.py` — fixture-driven integration coverage for the real scraper classes
- `tests/test_api.py` — FastAPI endpoints and response models
- `tests/test_library.py` — `BettingInsights` facade and result objects

## Recommended local commands

### 1. Run the full test suite

```bash
PYTHONPATH=src pytest tests/ -v
```

The explicit `PYTHONPATH=src` mirrors the CI workflow and helps imports resolve consistently.

### 2. Run with coverage

```bash
PYTHONPATH=src pytest tests/ \
  --verbose \
  --tb=short \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=xml \
  --cov-report=html
```

This produces:

- terminal coverage output
- `coverage.xml`
- `htmlcov/` for browser inspection

### 3. Run a focused file

```bash
pytest tests/test_api.py -v
pytest tests/test_prediction_engine.py -v
pytest tests/test_scrapers.py -v
```

### 4. Run a single test

```bash
pytest tests/test_ev_calculator.py::TestCalculateEV::test_positive_ev -v
```

## Quality checks beyond pytest

The GitHub workflow also runs several static checks.

### flake8

```bash
flake8 src/ tests/ --max-line-length=120 --extend-ignore=E203
```

### black

```bash
black --check src/ tests/
```

### isort

```bash
isort --check-only src/ tests/
```

### mypy

```bash
mypy src/ --ignore-missing-imports --no-strict-optional
```

## What CI currently does

The workflow in `.github/workflows/tests.yml` has two jobs.

### Test job

Runs on Python:

- 3.10
- 3.11
- 3.12
- 3.13

It installs dependencies, runs pytest with coverage, and uploads coverage artifacts.

### Lint job

Runs:

- flake8
- black check
- isort check
- mypy

## Practical verification tips

Because the project mixes real logic with mock/demo data paths, useful manual checks include both automated and smoke-test validation.

### CLI smoke tests

```bash
worldcup predict "Portugal vs Brazil"
worldcup predict "Spain vs Germany" --format json
worldcup scan --days 7
worldcup sites
```

### API smoke tests

```bash
uvicorn src.api.app:app --reload
curl http://127.0.0.1:8000/api/v1/health
curl -X POST http://127.0.0.1:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Portugal", "away_team": "Brazil"}'
```

### Library smoke test

```bash
python - <<'PY'
from src.library import BettingInsights

insights = BettingInsights()
result = insights.analyze_match("Portugal", "Brazil")
print(result.to_dict())
PY
```

## Interpreting failures

A few failure patterns are more likely than others:

### Import path issues

If modules fail to import, retry with:

```bash
PYTHONPATH=src pytest tests/ -v
```

### Dependency drift

If API or typing checks fail unexpectedly, make sure the environment matches `requirements.txt`.

### Scraper-related failures

Scraper CI is designed to stay stable: parser-level integration tests run against captured HTML/JSON fixtures rather than live bookmaker pages. If they fail, that usually means a parser contract changed, fixture coverage is incomplete, or a normalization regression slipped in — not that an external site happened to be down.

## Suggested contributor workflow

A sensible lightweight workflow for changes is:

```bash
pip install -r requirements.txt
pip install -e .
PYTHONPATH=src pytest tests/test_ev_calculator.py tests/test_library.py tests/test_scraper_integration_real_fixtures.py -v
PYTHONPATH=src pytest tests/ -v
black src/ tests/
isort src/ tests/
flake8 src/ tests/ --max-line-length=120 --extend-ignore=E203
mypy src/ --ignore-missing-imports --no-strict-optional
```

For documentation-only changes, you can usually stop after:

- reviewing the changed docs,
- optionally running a quick smoke test, and
- confirming there are no accidental code changes.

## Current confidence level

The repo has a stronger testing story than many prototypes, especially around:

- EV math
- model behavior
- API contracts
- library surface

That said, passing tests do **not** mean the system is production-ready for real-money betting. They mainly confirm that the implemented logic behaves consistently and that the public interfaces remain stable.
