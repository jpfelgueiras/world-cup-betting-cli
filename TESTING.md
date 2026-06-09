# Testing Guide

## Overview

This project has comprehensive unit tests covering all major components:

- ✅ EV Calculator utilities (100% function coverage)
- ✅ Prediction Engine & Team Stats
- ✅ Base Scraper & Bookmaker Scrapers
- ✅ REST API endpoints & models
- ✅ Python Library interface

## Test Files

| File | Component | Tests | Description |
|------|-----------|-------|-------------|
| `tests/test_ev_calculator.py` | `src/utils/ev_calculator.py` | 40+ | EV calculations, value bet detection |
| `tests/test_prediction_engine.py` | `src/predictors/` | 50+ | Match predictions, team stats |
| `tests/test_scrapers.py` | `src/scrapers/` | 45+ | Odds scraping, error handling |
| `tests/test_api.py` | `src/api/` | 50+ | REST endpoints, Pydantic models |
| `tests/test_library.py` | `src/library.py` | 35+ | Python library interface |

**Total: 220+ unit tests**

## Running Tests

### Quick Run

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

### Run Specific Test File

```bash
# EV Calculator tests
pytest tests/test_ev_calculator.py -v

# Prediction Engine tests  
pytest tests/test_prediction_engine.py -v

# Scraper tests
pytest tests/test_scrapers.py -v

# API tests
pytest tests/test_api.py -v

# Library tests
pytest tests/test_library.py -v
```

### Run Specific Test Class

```bash
# Only EV calculation tests
pytest tests/test_ev_calculator.py::TestCalculateEV -v

# Only prediction tests
pytest tests/test_prediction_engine.py::TestPredictionEngine -v
```

### Run Specific Test Function

```bash
# Single test
pytest tests/test_ev_calculator.py::TestCalculateEV::test_positive_ev -v
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

Test individual functions and classes in isolation:

- Mathematical calculations (EV, probabilities)
- Data model validation
- Error handling

### Integration Tests (`@pytest.mark.integration`)

Test component interactions:

- API endpoint responses
- Scraper HTTP requests (mocked)
- Library method chains

### Slow Tests (`@pytest.mark.slow`)

Tests that take longer (>100ms):

- Multiple prediction runs
- Large dataset processing

Run fast tests only:
```bash
pytest -m "not slow" -v
```

## Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| EV Calculator | 100% | ✅ 100% |
| Prediction Engine | 90% | ✅ 90%+ |
| Scrapers | 85% | ✅ 85%+ |
| API Routes | 90% | ✅ 90%+ |
| Library | 90% | ✅ 90%+ |
| **Overall** | **90%** | ✅ **90%+** |

## Key Test Scenarios

### EV Calculator

✅ Positive/negative/zero EV calculations
✅ Implied probability from odds
✅ Market average calculations
✅ Value bet qualification logic
✅ Confidence from variance calculations

### Prediction Engine

✅ Team data properties (form points, goal difference)
✅ Team stats computation (attack/defense strength)
✅ H2H advantage calculations
✅ Match prediction output
✅ Probability normalization (sums to 1.0)
✅ Context adjustments (must-win scenarios)
✅ Poisson distribution conversion
✅ Over 2.5 and BTTS probability calculations

### Scrapers

✅ OddsData creation and validation
✅ Base scraper rate limiting
✅ HTTP error handling (timeout, 403, 404, 429)
✅ Team name normalization
✅ Mock odds generation with realistic values
✅ Bookmaker status reporting

### API

✅ Pydantic model validation
✅ Health check endpoint
✅ Bookmaker listing endpoint
✅ Config get/update endpoints
✅ Predict endpoint with various inputs
✅ Scan endpoint with filters
✅ Error response formatting
✅ CORS headers

### Library

✅ BettingInsights initialization
✅ Match analysis results
✅ Scan results aggregation
✅ Configuration updates
✅ Value bet filtering
✅ Result export to dictionary

## Mocking Strategy

### External Dependencies

- HTTP requests: `@patch('requests.Session.request')`
- Database: In-memory SQLite or mocked DataLoader
- Time-dependent code: `freeze_time` from pytest-freezegun

### Example Mock Test

```python
@patch('requests.Session.request')
def test_make_request_success(self, mock_request, mock_scraper):
    """Test successful HTTP request"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "<html>Success</html>"
    mock_request.return_value = mock_response
    
    response = mock_scraper._make_request("https://test.com/page")
    
    assert response.status_code == 200
    mock_request.assert_called_once()
```

## Fixtures

Common test fixtures:

```python
@pytest.fixture
def engine():
    """Create prediction engine instance"""
    return PredictionEngine()

@pytest.fixture
def sample_teams():
    """Create sample team data for testing"""
    home = TeamData(name="Portugal", fifa_ranking=8, ...)
    away = TeamData(name="Brazil", fifa_ranking=3, ...)
    return home, away

@pytest.fixture
def scraper():
    """Create scraper instance"""
    return BetanoScraper()

@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(create_app())
```

## Continuous Integration

Add to your CI pipeline:

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12", "3.13"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest tests/ --cov=src --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Debugging Tests

### Verbose Output

```bash
pytest -v -s tests/test_file.py::TestClass::test_method
```

### Show Local Variables on Failure

```bash
pytest --showlocals tests/
```

### Stop on First Failure

```bash
pytest -x tests/
```

### Print Output

```bash
# Use print() in tests and show with -s
pytest -s tests/
```

## Common Issues

### Import Errors

Make sure you're running from the project root:

```bash
cd /path/to/world-cup-betting-cli
pytest tests/
```

Or add src to PYTHONPATH:

```bash
PYTHONPATH=src pytest tests/
```

### Fixture Not Found

Ensure fixtures are in conftest.py or imported:

```python
# tests/conftest.py
import pytest

@pytest.fixture
def sample_data():
    return {...}
```

### Async Tests

Use pytest-asyncio for async tests:

```python
@pytest.mark.asyncio
async def test_async_endpoint():
    result = await some_async_function()
    assert result is not None
```

## Writing New Tests

### Test Template

```python
"""
Unit tests for [Component Name]
"""

import pytest
from src.[module] import [ClassOrFunction]


class Test[ComponentName]:
    """Tests for [Component]"""
    
    def test_[scenario]_returns_[expected](self):
        """Test that [description]"""
        # Arrange
        input_value = ...
        
        # Act
        result = [ClassOrFunction](input_value)
        
        # Assert
        assert result == expected_value
    
    def test_[edge_case]_raises_[exception](self):
        """Test error handling"""
        with pytest.raises(ExpectedError):
            [ClassOrFunction](invalid_input)
```

### Best Practices

1. **Test names should describe behavior**: `test_positive_ev_returns_percentage`
2. **One assertion per concept** (can have multiple related assertions)
3. **Arrange-Act-Assert pattern** for clarity
4. **Test edge cases**: empty inputs, None, boundary values
5. **Mock external dependencies**: don't make real HTTP calls in tests
6. **Keep tests fast**: <100ms per test ideally

## Coverage Report

Generate HTML coverage report:

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

## Performance Benchmarks

For performance-critical code:

```bash
pip install pytest-benchmark

# Run with benchmark
pytest tests/ --benchmark-only
```

Example benchmark test:

```python
def test_prediction_speed(benchmark):
    """Benchmark prediction generation"""
    engine = PredictionEngine()
    
    result = benchmark(
        engine.predict_match,
        home_team_data,
        away_team_data
    )
    
    assert result is not None
```

---

**Last Updated**: 2026-06-09
**Test Count**: 220+
**Coverage Target**: 90%+
