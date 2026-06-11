# 🏆 World Cup Betting Insights - Frontend

React + Vite + TypeScript UI for betting insights.

## Features

- **Match Dashboard**: View scanned matches with value bets
- **Betting Analysis**: Analyze specific matches for value opportunities
- **Leagues & Bookmakers**: Monitor available leagues and bookmaker status
- **Settings**: Configure EV thresholds and confidence levels
- **Responsive Design**: Mobile-friendly UI with Tailwind CSS

## Tech Stack

- **Framework**: React 18
- **Build Tool**: Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: TanStack Query (React Query)
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Icons**: Lucide React

## Installation

```bash
npm install
```

## Development

```bash
# Start dev server
npm run dev

# Run linter
npm run lint

# Type check
npx tsc --noEmit

# Run tests
npm run test

# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/    # Reusable UI components
│   │   ├── Layout.tsx
│   │   ├── MatchCard.tsx
│   │   └── ValueBetTable.tsx
│   ├── pages/         # Page components
│   │   ├── HomePage.tsx
│   │   ├── MatchesPage.tsx
│   │   ├── BettingPage.tsx
│   │   ├── LeaguesPage.tsx
│   │   ├── SettingsPage.tsx
│   │   └── AboutPage.tsx
│   ├── services/      # API service layer
│   │   └── api.ts
│   ├── types/         # TypeScript interfaces
│   │   └── index.ts
│   ├── utils/         # Helper functions
│   │   └── index.ts
│   ├── App.tsx        # Main app component
│   ├── main.tsx       # Entry point
│   └── index.css      # Global styles
├── public/            # Static assets
├── index.html         # HTML template
├── package.json       # Dependencies
├── tsconfig.json      # TypeScript config
├── vite.config.ts     # Vite config
└── tailwind.config.js # Tailwind config
```

## Configuration

Create a `.env` file:

```env
VITE_API_URL=http://localhost:8000
VITE_API_KEY=your-api-key-here
```

## Pages

### Home (`/`)
Dashboard with quick stats and match scanning interface.

### Matches (`/matches`)
Browse all scanned matches with filtering and sorting.

### Betting (`/betting`)
Analyze specific matches for value bets.

### Leagues (`/leagues`)
View available leagues and bookmaker information.

### Settings (`/settings`)
Configure analysis thresholds and API settings.

### About (`/about`)
Project information and responsible gambling notice.

## Components

- **Layout**: Main application layout with navigation
- **MatchCard**: Display match information and top value bet
- **ValueBetTable**: Table of value bet recommendations

## API Integration

The frontend communicates with the backend API via the `api` service:

```typescript
import { api } from '@services/api'

// Get health status
const health = await api.getHealth()

// Predict a match
const prediction = await api.predictMatch('Portugal', 'Brazil')

// Scan matches
const scan = await api.scanMatches(7, 'all', 5.0)
```

## Testing

```bash
# Run tests
npm run test

# Run tests with coverage
npm run test:coverage

# Run tests with UI
npm run test:ui
```

## Building for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

## Deployment

Configure your deployment target in `.github/workflows/frontend-deploy.yml`.

Supported platforms:
- Vercel
- Netlify
- AWS S3 + CloudFront
- Any static hosting service

## License

MIT License
