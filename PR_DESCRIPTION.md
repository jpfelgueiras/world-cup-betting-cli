# Pull Request: Split Backend and Frontend Repositories

## Overview

This PR splits the monolithic World Cup Betting CLI project into separate backend and frontend repositories, following modern full-stack development best practices.

## Changes

### 📁 Repository Structure

**Before:**
```
world-cup-betting-cli/
├── src/
├── tests/
├── requirements.txt
└── Dockerfile
```

**After:**
```
world-cup-betting-cli/
├── backend/              # FastAPI REST API
│   ├── src/
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── docker-compose.yml
├── frontend/             # React + Vite + TypeScript UI
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
├── .github/workflows/    # CI/CD for both projects
├── README.md             # Root documentation
├── ARCHITECTURE.md       # System architecture
└── CONTRIBUTING.md       # Contribution guidelines
```

### 🔧 Backend Changes

**Location:** `backend/`

- Moved all Python source code from `src/` to `backend/src/`
- Preserved all API endpoints, models, and routes
- Kept scrapers, prediction engine, and EV calculator
- Updated Docker configuration for backend-only deployment
- Created backend-specific `.gitignore` and `.env.example`
- Added backend README with API documentation

**Key Files:**
- `backend/src/api/app.py` - FastAPI application
- `backend/src/api/routes.py` - REST endpoints
- `backend/src/predictors/` - Prediction engine
- `backend/src/scrapers/` - Bookmaker scrapers
- `backend/tests/` - Test suite

### 🎨 Frontend Changes

**Location:** `frontend/`

Created new React + Vite + TypeScript application with:

**Pages:**
- `HomePage` - Dashboard with match scanning
- `MatchesPage` - Browse and filter matches
- `BettingPage` - Analyze specific matches
- `LeaguesPage` - View leagues and bookmakers
- `SettingsPage` - Configure thresholds
- `AboutPage` - Project information

**Components:**
- `Layout` - Navigation and footer
- `MatchCard` - Match display component
- `ValueBetTable` - Value bets table

**Services:**
- `api.ts` - API client with Axios and React Query

**Styling:**
- Tailwind CSS for responsive design
- Dark theme optimized for betting analytics

### 🚀 CI/CD Workflows

**New Workflows:**

1. **Backend CI** (`.github/workflows/backend-ci.yml`)
   - Tests on Python 3.10-3.13
   - Coverage enforcement (70% floor)
   - Quality checks (flake8, black, mypy)
   - Docker image build and test

2. **Frontend CI** (.github/workflows/frontend-ci.yml`)
   - npm install and dependency caching
   - ESLint and TypeScript checks
   - Vitest tests (when configured)
   - Production build verification

3. **Security CI** (`.github/workflows/security.yml`)
   - Backend: pip-audit, CodeQL
   - Frontend: npm audit, Snyk
   - Secret scanning with Gitleaks

4. **Backend Deploy** (`.github/workflows/backend-deploy.yml`)
   - Build and push to GHCR
   - Production deployment hooks

5. **Frontend Deploy** (`.github/workflows/frontend-deploy.yml`)
   - Production build
   - Static site deployment hooks

**Dependency Updates:**
- Dependabot configured for both pip and npm
- Weekly updates on Mondays

### 📚 Documentation

**New Documentation:**

1. **README.md** (root) - Project overview with quick start
2. **backend/README.md** - Backend API documentation
3. **frontend/README.md** - Frontend UI documentation
4. **ARCHITECTURE.md** - System architecture diagrams
5. **CONTRIBUTING.md** - Contribution guidelines

**Updated Documentation:**
- Removed CLI-focused sections
- Added split repository instructions
- Updated installation and deployment guides

### ⚙️ Configuration Files

**Backend:**
- `backend/.env.example` - Environment variables template
- `backend/.gitignore` - Python-specific ignores
- `backend/Dockerfile` - Multi-stage production build
- `backend/docker-compose.yml` - Development and production configs
- `backend/requirements.txt` - Python dependencies

**Frontend:**
- `frontend/.env.example` - Environment variables template
- `frontend/.gitignore` - Node.js-specific ignores
- `frontend/package.json` - npm dependencies
- `frontend/tsconfig.json` - TypeScript configuration
- `frontend/vite.config.ts` - Vite build configuration
- `frontend/tailwind.config.js` - Tailwind CSS theming
- `frontend/postcss.config.js` - PostCSS configuration

## Testing

### Backend Tests

All existing tests moved to `backend/tests/`:

```bash
cd backend
PYTHONPATH=src pytest tests/ -v --cov=src
```

**Coverage:** 70% minimum enforced on Python 3.12

### Frontend Tests

Basic test infrastructure configured with Vitest:

```bash
cd frontend
npm run test
```

## Migration Guide

### For Developers

**Old Workflow:**
```bash
pip install -r requirements.txt
uvicorn src.api.app:app --reload
```

**New Workflow:**
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn src.api.app:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### For Docker Users

**Old:**
```bash
docker-compose up api
```

**New:**
```bash
# Backend only
cd backend
docker-compose up api

# Or from root with both services
docker-compose up
```

### For CI/CD

No changes required for existing deployments using the old structure. New workflows run in parallel for both projects.

## Benefits

1. **Independent Development**: Backend and frontend can evolve separately
2. **Clearer Boundaries**: Well-defined API contract between layers
3. **Better CI/CD**: Targeted pipelines for each project
4. **Easier Scaling**: Deploy backend and frontend independently
5. **Modern Stack**: React + TypeScript frontend with proper tooling
6. **Improved DX**: Faster installs, clearer project structure

## Breaking Changes

- CLI commands now require navigating to `backend/` directory
- Frontend is a new addition; no migration path needed
- Environment variables split between `backend/.env` and `frontend/.env`

## Backward Compatibility

- All existing API endpoints preserved
- Request/response models unchanged
- Authentication mechanism unchanged
- Docker images maintain same interface

## Rollout Plan

1. ✅ Merge this PR to `feat/split-backend-frontend` branch
2. ✅ Test both backend and frontend locally
3. ✅ Verify CI/CD workflows pass
4. ⏳ Deploy to staging environment
5. ⏳ Update documentation links
6. ⏳ Merge to main branch

## Related Issues

- Closes #XX - Split into separate repositories
- Closes #XX - Add React frontend
- Closes #XX - Improve CI/CD pipeline

## Checklist

- [x] Backend code moved to `backend/`
- [x] Frontend created in `frontend/`
- [x] All tests passing
- [x] CI/CD workflows configured
- [x] Documentation updated
- [x] Docker configurations updated
- [x] Environment templates created
- [x] .gitignore files updated
- [x] Architecture documented
- [x] Contributing guidelines written

## Reviewers

Please review:
- Backend structure and API preservation
- Frontend implementation and design
- CI/CD workflow correctness
- Documentation completeness

---

**Questions?** See [ARCHITECTURE.md](ARCHITECTURE.md) or [CONTRIBUTING.md](CONTRIBUTING.md)
