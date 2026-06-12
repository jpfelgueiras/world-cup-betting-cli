# Free hosting deployment guide

This repository is a split application:

- `backend/`: FastAPI service packaged as a Docker image
- `frontend/`: Vite/React static application

The selected free-hosting setup is:

1. Backend on Render Free Web Service using `backend/Dockerfile`
2. Frontend on Vercel Hobby using the Vite static build

Netlify is also supported for the frontend through `netlify.toml`.

## Recommended free hosting options

### Backend: Render Free Web Service

Why: Render can build and run this backend from the existing Dockerfile, has a clear Free Web Service tier suitable for a demo API, and supports deploy hooks for GitHub Actions. The workflow in `.github/workflows/backend-deploy.yml` now runs backend validation first and then triggers Render only after those checks pass.

Important Render free-tier constraints:

- Free services can sleep after inactivity and have cold starts.
- Free instances are memory-constrained; verify the backend fits because the dependency set includes pandas, scikit-learn, and xgboost.
- Runtime filesystem changes are ephemeral. Do not rely on local SQLite/cache files as durable production storage.
- If Render auto-deploy is enabled, Render may deploy immediately on push before GitHub Actions tests complete. Disable auto-deploy if you want the Actions workflow to be the deployment gate.

Create the backend service in Render with:

- Service type: Web Service
- Source: this GitHub repository
- Branch: `main`
- Runtime/language: Docker
- Root directory: `backend`
- Dockerfile path: `Dockerfile`
- Instance type: Free
- Health check path: `/health`
- Auto-deploy: off when GitHub Actions should gate deployments

What the workflow does:

- Installs the backend dependencies with Python 3.11
- Runs `python -m pytest tests -q` in `backend/`
- Builds the backend Docker image with `backend/Dockerfile`
- Calls the secret Render deploy hook URL from `RENDER_DEPLOY_HOOK_URL` only on `main`

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

`RENDER_DEPLOY_HOOK_URL`
: Secret Render deploy hook URL for the backend Web Service. Copy it from the Render service `Settings` page. Regenerate it in Render if it is exposed.

### Frontend deployment secrets

`VERCEL_TOKEN`
: Vercel access token.

`VERCEL_ORG_ID`
: Vercel team/user ID for the project.

`VERCEL_PROJECT_ID`
: Vercel project ID.

`VITE_API_URL`
: Backend public URL, for example `https://world-cup-betting-backend.onrender.com`.

`VITE_API_KEY`
: Browser-exposed API key sent as `X-API-Key`. It must match one of the values in Render `VALID_API_KEYS`.

Important: Vite variables are embedded into the frontend bundle. Do not use a private admin secret for `VITE_API_KEY`; treat it as a public client key. If you need strong security later, add real user authentication or a backend-for-frontend.

## Platform environment variables

### Render backend runtime environment

Set these on the Render Web Service:

- `DEV_MODE=false`
- `ENABLE_CORS=true`
- `CORS_ORIGINS=<frontend URL>`
- `VALID_API_KEYS=<comma-separated backend API keys>`
- `LOG_LEVEL=INFO`

Render provides `PORT` automatically. The backend Dockerfile starts Uvicorn with `${PORT:-8000}` and the health check uses the same value.

Optional backend variables if you add real data sources or monitoring later:

- `FOOTBALL_DATA_API_KEY`
- `FBREF_API_KEY`
- `API_FOOTBALL_API_KEY`
- `SENTRY_DSN`

### Vercel frontend build environment

- `VITE_API_URL=$VITE_API_URL`
- `VITE_API_KEY=$VITE_API_KEY`

## First deployment steps

1. Create a Render account and a new backend Web Service using the settings above.
2. Add the Render runtime environment variables.
3. Copy the Render deploy hook URL into the GitHub secret `RENDER_DEPLOY_HOOK_URL`.
4. Create a Vercel account and a Vercel project for the `frontend` directory.
5. Add all GitHub repository secrets listed above.
6. Merge this PR into `main`.
7. Open GitHub Actions and run, or wait for, these workflows:
   - `Backend Deploy`
   - `Frontend Deploy`
8. After backend deploy finishes, confirm the Render service is healthy and copy its `onrender.com` URL into the `VITE_API_URL` GitHub secret.
9. After frontend deploy finishes, copy the Vercel URL into the Render `CORS_ORIGINS` environment variable.
10. Re-run `Backend Deploy` so backend CORS allows the final frontend URL.

## Smoke tests after deployment

Backend:

```bash
curl https://your-backend-host/health
```

Frontend:

1. Open the Vercel URL.
2. Navigate through the app.
3. Confirm browser devtools show API calls going to the deployed Render backend URL, not `localhost:8000`.

## Notes and caveats

- Render's free tier is appropriate for demos but can sleep/cold start and has limited CPU/memory.
- If the backend exceeds Render Free memory, use the provider-selection fallback: Google Cloud Run.
- The app currently exposes a browser API key by design. This is adequate for light demo deployments but not for a production betting application.
- Some bookmaker scraping may be blocked or behave differently from hosted cloud IPs. The app has mock/fallback behavior, but production-grade scraping needs monitoring and compliance review.
