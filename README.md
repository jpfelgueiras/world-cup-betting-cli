# 🏆 World Cup Betting Insights

A full-stack application for analyzing football betting markets by comparing model-generated match probabilities with odds from Portuguese bookmakers.

## Architecture

This project is split into two separate repositories:

```
world-cup-betting-cli/
├── backend/          # FastAPI REST API (Python)
└── frontend/         # React + Vite + TypeScript UI
```

### Backend (`backend/`)

- **Framework**: FastAPI (Python 3.11+)
- **Features**:
  - REST API for match predictions and value bet scanning
  - Bookmaker scrapers (Betano, Betclic, Solverde)
  - Prediction engine with EV calculation
  - SQLite caching layer
  - Prometheus metrics integration
  - Docker containerization

### Frontend (`frontend/`)

- **Stack**: React 18 + Vite + TypeScript
- **Features**:
  - Modern responsive UI with Tailwind CSS
  - Real-time match scanning
  - Value bet discovery interface
  - Bookmaker status monitoring
  - Settings and configuration management

---

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Run API server
uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

# Or use Docker
docker-compose up api-dev
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Access the UI at `http://localhost:5173` and the API at `http://localhost:8000`.

---

## Documentation

- [Backend README](backend/README.md) - Backend API documentation
- [Frontend README](frontend/README.md) - Frontend UI documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

---

## ⚠️ Responsible Gambling

This software is for analysis only:

- No guaranteed wins
- Use only where legal
- In Portugal, gambling is restricted to adults (18+)
- Only use licensed operators
- Never bet more than you can afford to lose

If gambling is becoming a problem, seek help through the Portuguese regulator:  
<https://www.srij.turismodeportugal.pt/>

---

## License

MIT License - see LICENSE file for details
