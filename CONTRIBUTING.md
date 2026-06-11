# Contributing to World Cup Betting Insights

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Project Structure

This repository contains two separate projects:

- **`backend/`**: FastAPI REST API (Python)
- **`frontend/`**: React UI (TypeScript)

Changes can be made to either or both, depending on your contribution.

## Getting Started

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Frontend Setup

```bash
cd frontend
npm install
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feat/your-feature-name
# or
git checkout -b fix/issue-description
```

### 2. Make Changes

Follow the coding standards for each project:

#### Backend (Python)

- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Write docstrings for public functions and classes
- Keep functions focused and single-purpose

```python
def calculate_ev(probability: float, odds: float) -> float:
    """
    Calculate expected value percentage.
    
    Args:
        probability: Model probability (0-1)
        odds: Decimal odds from bookmaker
        
    Returns:
        EV percentage (e.g., 5.5 for 5.5%)
    """
    return (probability * odds - 1) * 100
```

#### Frontend (TypeScript/React)

- Use TypeScript for all new code
- Follow React best practices (functional components, hooks)
- Use Tailwind CSS for styling
- Keep components small and focused

```typescript
interface ValueBet {
  market: string
  odds: number
  ev_percentage: number
}

export function ValueBetCard({ bet }: { bet: ValueBet }) {
  return (
    <div className="bg-gray-800 rounded-lg p-4">
      <h3 className="font-medium">{bet.market}</h3>
      <p className="text-success">+{bet.ev_percentage.toFixed(1)}% EV</p>
    </div>
  )
}
```

### 3. Run Tests

#### Backend Tests

```bash
cd backend
PYTHONPATH=src pytest tests/ -v --cov=src
```

#### Frontend Tests

```bash
cd frontend
npm run test
```

### 4. Run Quality Checks

#### Backend

```bash
# Formatting
black src/ tests/

# Linting
flake8 src/ tests/ --max-line-length=120

# Type checking
mypy src/
```

#### Frontend

```bash
# Linting
npm run lint

# Type checking
npx tsc --noEmit
```

### 5. Commit Changes

Follow conventional commits format:

```
feat: add new match scanning endpoint
fix: correct EV calculation for away wins
docs: update API documentation
test: add unit tests for prediction engine
refactor: simplify scraper base class
```

### 6. Submit a Pull Request

1. Push your branch to GitHub
2. Open a pull request against `main`
3. Fill out the PR template
4. Wait for CI checks to pass
5. Address review feedback

## CI/CD Requirements

All PRs must pass:

### Backend CI
- ✅ Tests on Python 3.10-3.13
- ✅ Coverage floor (70% on Python 3.12)
- ✅ flake8 linting
- ✅ black formatting
- ✅ mypy type checking
- ✅ Docker image build

### Frontend CI
- ✅ npm install
- ✅ ESLint
- ✅ TypeScript compilation
- ✅ Tests (if applicable)
- ✅ Production build

### Security CI
- ✅ Dependency audit (pip-audit, npm audit)
- ✅ CodeQL analysis
- ✅ Secret scanning

## Areas for Contribution

### High Priority

1. **Scraper Improvements**
   - Add more Portuguese bookmakers
   - Improve anti-bot handling
   - Add error recovery

2. **Model Enhancement**
   - Better team data sources
   - Historical backtesting
   - More accurate probability calibration

3. **Frontend Features**
   - Real-time odds updates
   - Interactive charts
   - Mobile responsiveness improvements

4. **Testing**
   - Increase test coverage
   - Add integration tests
   - E2E testing with Playwright

### Nice to Have

- Additional languages support
- Dark/light theme toggle
- Export functionality (CSV, PDF)
- Historical odds tracking
- User authentication system

## Code Review Guidelines

### What We Look For

- Clear, readable code
- Appropriate test coverage
- No breaking changes without migration
- Documentation updates for API changes
- Security considerations addressed

### Common Review Comments

- "Please add type hints"
- "Consider extracting this into a helper function"
- "Add a test for this edge case"
- "Update the docstring to reflect the new behavior"

## Reporting Issues

### Bug Reports

Include:
- Steps to reproduce
- Expected vs actual behavior
- Environment details (Python/Node version, OS)
- Error messages and logs

### Feature Requests

Include:
- Problem you're trying to solve
- Proposed solution
- Alternative approaches considered
- Use cases

## Responsible Gambling Notice

When contributing, remember:

- This tool is for analysis only
- Never claim guaranteed wins
- Always include responsible gambling notices
- Respect legal restrictions by jurisdiction

## Questions?

Open an issue for:
- Clarification on requirements
- Architecture discussions
- Feature proposals

We welcome contributors of all experience levels!
