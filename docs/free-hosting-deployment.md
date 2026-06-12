# Free hosting deployment guide

This repository is a split application:

- `backend/`: FastAPI service packaged as a Docker image
- `frontend/`: Vite/React static application

The most practical free-hosting setup is:

1. Backend on Koyeb free/nano service using `backend/Dockerfile`
2. Frontend on Vercel Hobby using the Vite static build

Netlify is also supported for the frontend through `netlify.toml`.

## Recommended free hosting options

### Backend: Koyeb

Why: Koyeb can deploy a web service from this repository using the Dockerfile in `backend/`. The workflow in `.github/workflows/backend-deploy.yml` deploys the backend service to Koyeb whenever `main` changes under `backend/**`.

What the workflow deploys:

- App: `world-cup-betting`
- Service: `backend`
- Git workdir: `backend`
- Builder: Docker
- Port: `8000`
- Route: `/:8000`

### Frontend: Vercel

Why: Vercel is a good free static host for Vite/React apps. The workflow in `.github/workflows/frontend-deploy.yml` builds the frontend and deploys prebuilt output to Vercel.

What the workflow deploys:

- Root directory: `frontend`
- Build command: `npm run build`
- Output directory: `dist`
- SPA fallback: configured in `frontend/vercel.json`

### Frontend alternative: Netlify

`netlify.toml` is included for a manual Netlify setup:

- Base directory: `frontend`
- Build command: `npm ci && npm run build`
- Publish directory: `frontend/dist`
- SPA fallback: configured with a redirect to `/index.html`

## Required GitHub repository secrets

Add these in GitHub at:

`Settings -> Secrets and variables -> Actions -> New repository secret`

### Backend deployment secrets

`KOYEB_API_TOKEN`
: Koyeb API token. Create it in Koyeb account settings.

`FRONTEND_URL`
: The production frontend URL, for example `https://your-project.vercel.app`. The backend uses this as `CORS_ORIGINS`.

`BACKEND_API_KEYS`
: Comma-separated API key list accepted by the backend, for example `prod-key-please-change`. Use the same value, or one of the comma-separated values, as the frontend `VITE_API_KEY`.

### Frontend deployment secrets

`VERCEL_TOKEN`
: Vercel access token.

`VERCEL_ORG_ID`
: Vercel team/user ID for the project.

`VERCEL_PROJECT_ID`
: Vercel project ID.

`VITE_API_URL`
: Backend public URL, for example `https://world-cup-betting-backend.koyeb.app`.

`VITE_API_KEY`
: Browser-exposed API key sent as `X-API-Key`. It must match one of the values in `BACKEND_API_KEYS`.

Important: Vite variables are embedded into the frontend bundle. Do not use a private admin secret for `VITE_API_KEY`; treat it as a public client key. If you need strong security later, add real user authentication or a backend-for-frontend.

## Platform environment variables

The GitHub Actions workflows pass the deployment values automatically, but these are the effective runtime values to understand.

### Koyeb backend runtime environment

- `PORT=8000`
- `DEV_MODE=false`
- `ENABLE_CORS=true`
- `CORS_ORIGINS=$FRONTEND_URL`
- `VALID_API_KEYS=$BACKEND_API_KEYS`
- `LOG_LEVEL=INFO`
- `LOG_FILE=`

Optional backend variables if you add real data sources or monitoring later:

- `FOOTBALL_DATA_API_KEY`
- `FBREF_API_KEY`
- `API_FOOTBALL_API_KEY`
- `SENTRY_DSN`

### Vercel frontend build environment

- `VITE_API_URL=$VITE_API_URL`
- `VITE_API_KEY=$VITE_API_KEY`

## First deployment steps

1. Create a Koyeb account and API token.
2. Create a Vercel account and a Vercel project for the `frontend` directory.
3. Add all GitHub repository secrets listed above.
4. Merge this PR into `main`.
5. Open GitHub Actions and run, or wait for, these workflows:
   - `Backend Deploy`
   - `Frontend Deploy`
6. After backend deploy finishes, copy the Koyeb service URL into the `VITE_API_URL` GitHub secret.
7. After frontend deploy finishes, copy the Vercel URL into the `FRONTEND_URL` GitHub secret.
8. Re-run both deploy workflows so CORS and frontend API URL are aligned.

## Smoke tests after deployment

Backend:

```bash
curl https://your-backend-host/health
```

Frontend:

1. Open the Vercel URL.
2. Navigate through the app.
3. Confirm browser devtools show API calls going to the deployed backend URL, not `localhost:8000`.

## Notes and caveats

- Free tiers may sleep, cold start, or require periodic redeploys.
- The app currently exposes a browser API key by design. This is adequate for light demo deployments but not for a production betting application.
- Some bookmaker scraping may be blocked or behave differently from hosted cloud IPs. The app has mock/fallback behavior, but production-grade scraping needs monitoring and compliance review.
