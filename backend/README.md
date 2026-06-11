# 🏆 World Cup Betting Insights - Backend API

FastAPI-based REST API for AI-powered betting insights.

## Features

- **Match Predictions**: AI-powered win/draw/loss probabilities
- **Value Bet Detection**: Identify bets with positive expected value (EV)
- **Multi-Bookmaker Analysis**: Compare odds across Portuguese licensed sites
- **REST API**: Full RESTful API with OpenAPI documentation
- **Docker Support**: Production-ready containerization

## Installation

### Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Docker

```bash
# Development
docker-compose up api-dev

# Production
docker-compose up api
```

## Usage

### Run API Server

```bash
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

### Example Requests

#### Health Check

```bash
curl http://localhost:8000/health
```

#### Predict Match

```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"home_team": "Portugal", "away_team": "Brazil", "site": "all"}'
```

#### Scan Matches

```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -H "Content-Type: application/json" \
  -d '{"days_ahead": 7, "site": "all", "min_ev": 5.0}'
```

## Configuration

Set environment variables via `.env` file:

```env
# API Configuration
DEV_MODE=true
LOG_LEVEL=INFO
ENABLE_CORS=true
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Rate Limiting
RATE_LIMIT_PER_IP=100
RATE_LIMIT_WINDOW_SECONDS=60

# Thresholds
MIN_EV_THRESHOLD=5.0
MIN_CONFIDENCE_THRESHOLD=60.0

# API Keys (production)
VALID_API_KEYS=your-api-key-here
```

## Testing

```bash
PYTHONPATH=src pytest tests/ -v

# With coverage
PYTHONPATH=src pytest tests/ --cov=src --cov-report=html
```

## Project Structure

```
backend/
├── src/
│   ├── api/           # FastAPI routes, models, middleware
│   ├── scrapers/      # Bookmaker data scrapers
│   ├── predictors/    # Prediction engine and team stats
│   ├── utils/         # EV calculator and helpers
│   ├── cli/           # CLI interface (legacy)
│   ├── config.py      # Configuration
│   └── library.py     # Python library interface
├── tests/             # Test suite
├── Dockerfile         # Production Docker image
├── docker-compose.yml # Docker Compose configuration
└── requirements.txt   # Python dependencies
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/api/v1/predict` | POST | Analyze a match |
| `/api/v1/scan` | POST | Scan upcoming matches |
| `/api/v1/bookmakers` | GET | List bookmakers |
| `/api/v1/config` | GET/PUT | Get/update config |

## Security

- API Key authentication (X-API-Key header)
- Rate limiting per IP
- CORS configuration
- Security headers

## Monitoring

- Prometheus metrics at `/metrics`
- Health checks for container orchestration
- Structured logging support

## License

MIT License
