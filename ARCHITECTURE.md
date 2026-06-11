# System Architecture

## Overview

World Cup Betting Insights is a full-stack application split into separate backend and frontend repositories, following clean architecture principles with loose coupling between layers.

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (React)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Pages   │  │Components│  │ Services │  │  Types   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                         │                                   │
│                    Axios/REST                               │
└─────────────────────────┼───────────────────────────────────┘
                          │ HTTP/JSON
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Routes  │  │  Models  │  │Middleware│  │ Security │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│                         │                                   │
│              ┌──────────┴──────────┐                       │
│              ▼                     ▼                       │
│  ┌──────────────────┐   ┌──────────────────┐              │
│  │ Prediction Engine│   │   Scrapers       │              │
│  │ - Team Stats     │   │ - Betano         │              │
│  │ - EV Calculator  │   │ - Betclic        │              │
│  └──────────────────┘   │ - Solverde       │              │
│                         └──────────────────┘              │
│                                │                           │
│                                ▼                           │
│                    ┌──────────────────┐                   │
│                    │ SQLite Cache     │                   │
│                    └──────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

## Backend Architecture

### Layers

1. **API Layer** (`src/api/`)
   - FastAPI application and routes
   - Pydantic models for request/response validation
   - Middleware (CORS, rate limiting, security headers)
   - Authentication (API key)

2. **Business Logic Layer**
   - **Prediction Engine** (`src/predictors/`): Match outcome modeling
   - **EV Calculator** (`src/utils/`): Expected value calculations
   - **Library** (`src/library.py`): High-level Python API

3. **Data Access Layer**
   - **Scrapers** (`src/scrapers/`): Bookmaker data extraction
   - **Cache** (`src/predictors/data_loader.py`): SQLite persistence

### Key Components

#### Prediction Engine

```python
class PredictionEngine:
    def predict_match(self, home: TeamData, away: TeamData) -> MatchPrediction:
        # 1. Calculate team stats
        # 2. Estimate expected goals
        # 3. Apply Poisson distribution
        # 4. Generate probabilities and confidence
        # 5. Return prediction with reasoning
```

#### EV Calculator

```python
def analyze_bet(
    market: str,
    odds: float,
    model_probability: float,
    confidence: float,
    min_ev: float = 5.0,
    min_confidence: float = 60.0,
) -> BetRecommendation:
    ev = (model_probability * odds) - 1
    is_value = ev > min_ev and confidence > min_confidence
    return BetRecommendation(...)
```

#### Scrapers

All scrapers implement the `BaseScraper` interface:

```python
class BaseScraper(ABC):
    @abstractmethod
    def get_match_odds(self, home: str, away: str) -> OddsData | None: ...
    
    @abstractmethod
    def get_upcoming_matches(self, days_ahead: int) -> list[OddsData]: ...
```

## Frontend Architecture

### Component Hierarchy

```
App
└── Layout
    ├── HomePage
    │   ├── Stats Cards
    │   ├── Scan Settings
    │   └── Match List
    ├── MatchesPage
    │   ├── Search Bar
    │   ├── Sort Controls
    │   └── MatchCard[]
    ├── BettingPage
    │   ├── Analysis Form
    │   ├── Probability Display
    │   └── ValueBetTable
    ├── LeaguesPage
    │   ├── League List
    │   └── Bookmaker Grid
    ├── SettingsPage
    │   └── Configuration Forms
    └── AboutPage
```

### State Management

- **TanStack Query**: Server state caching and synchronization
- **React State**: Local UI state (forms, filters)
- **No Global Store**: Each component manages its own state

### API Service Layer

```typescript
class ApiClient {
  async predictMatch(home: string, away: string): Promise<MatchAnalysisResponse>
  async scanMatches(days: number, site: string, minEv: number): Promise<ScanResponse>
  async getBookmakers(): Promise<BookmakerStatus[]>
  async getHealth(): Promise<HealthResponse>
}
```

## Data Flow

### Match Prediction Flow

1. User submits match analysis request in UI
2. Frontend sends POST to `/api/v1/predict`
3. Backend validates request with Pydantic
4. Prediction engine generates probabilities
5. Scrapers fetch odds from bookmakers
6. EV calculator identifies value bets
7. Response returned to frontend
8. TanStack Query caches result
9. UI displays analysis

### Match Scan Flow

1. User configures scan parameters (days, min EV)
2. Frontend requests `/api/v1/scan`
3. Backend queries all enabled scrapers
4. Each match analyzed for value bets
5. Results filtered and sorted
6. Frontend displays match cards

## Security Architecture

### Backend Security

- **Authentication**: API key via `X-API-Key` header
- **Rate Limiting**: Per-IP limits (default: 100 req/min)
- **CORS**: Configurable allowed origins
- **Security Headers**: X-Content-Type-Options, X-Frame-Options, etc.

### Frontend Security

- **Environment Variables**: API keys stored in `.env`
- **Input Validation**: TypeScript types + form validation
- **XSS Protection**: React's built-in escaping

## Deployment Architecture

### Backend Deployment

```yaml
services:
  api:
    image: ghcr.io/jpfelgueiras/world-cup-betting-cli/backend:latest
    ports:
      - "8000:8000"
    environment:
      - DEV_MODE=false
      - ENABLE_METRICS=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

### Frontend Deployment

Static files deployed to:
- Vercel / Netlify (recommended)
- AWS S3 + CloudFront
- Any CDN supporting static sites

## Monitoring & Observability

### Metrics

- Prometheus metrics endpoint at `/metrics`
- Request counts, latencies, error rates
- Bookmaker availability tracking

### Logging

- Structured logging support
- Configurable log levels
- Request/response logging (optional)

### Health Checks

- `/health` endpoint for container orchestration
- Component status reporting
- Database connectivity checks

## Development Workflow

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run with auto-reload
uvicorn src.api.app:app --reload

# Type checking
mypy src/
```

### Frontend

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Run tests
npm run test

# Build
npm run build
```

## Future Improvements

1. **Real-time Updates**: WebSocket integration for live odds
2. **Enhanced Model**: More sophisticated prediction algorithms
3. **Historical Analysis**: Track prediction accuracy over time
4. **User Accounts**: Personalized settings and bet tracking
5. **Mobile App**: React Native or Flutter implementation
6. **More Bookmakers**: Expand scraper coverage
