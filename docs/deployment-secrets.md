# Deployment secrets

This file lists the GitHub Actions secrets needed by the current free-hosting deployment workflows in this repository. For the full account setup, Render service creation, first deployment order, and troubleshooting guide, see `docs/free-hosting-deployment.md`.

Koyeb deployment is obsolete for this repository. Do not add old Koyeb tokens, app names, or service IDs for the current workflow; `.github/workflows/backend-deploy.yml` uses Render's deploy hook instead.

Add repository secrets in GitHub at:

`Settings -> Secrets and variables -> Actions -> New repository secret`

## Required secrets

### Backend / Render Free Web Service

The backend deploy workflow no longer deploys to Koyeb. It validates the backend, builds the Docker image locally in CI, then triggers the Render service through Render's recommended deploy-hook flow for GitHub Actions. The deploy hook URL is a secret because anyone with it can trigger a deploy.

`RENDER_DEPLOY_HOOK_URL`
: Render deploy hook URL for the backend Web Service. In the Render dashboard, open the backend service, go to `Settings`, copy the deploy hook URL, and store it exactly as this GitHub secret. Regenerate the hook in Render if it is exposed.

### Frontend / Vercel

`VERCEL_TOKEN`
: Vercel access token.

`VERCEL_ORG_ID`
: Vercel team/user/org ID for the project.

`VERCEL_PROJECT_ID`
: Vercel project ID.

`VITE_API_URL`
: The deployed Render backend URL, for example `https://world-cup-betting-backend.onrender.com`.

`VITE_API_KEY`
: Browser-exposed API key sent as `X-API-Key`. It must match one of the values in Render `VALID_API_KEYS`.

## Render backend service environment

Set these in the Render dashboard for the backend Web Service, not in the GitHub workflow:

`DEV_MODE=false`
: Runs the API in production mode.

`ENABLE_CORS=true`
: Enables CORS for the deployed frontend.

`CORS_ORIGINS=<frontend URL>`
: Use the deployed frontend URL, for example `https://your-project.vercel.app`.

`VALID_API_KEYS=<comma-separated backend API keys>`
: Comma-separated API key list accepted by the backend, for example `prod-demo-key-change-me`. The frontend `VITE_API_KEY` must match one of these values.

`LOG_LEVEL=INFO`
: Production log verbosity.

Render provides `PORT` automatically. The backend Dockerfile reads `${PORT:-8000}`, so do not hard-code a different value in the workflow.

## Optional future backend secrets

Only add these if you enable real data sources or monitoring:

`FOOTBALL_DATA_API_KEY`
: API key for football-data.org or the configured football data provider.

`FBREF_API_KEY`
: API key for an FBref-compatible data provider, if one is configured.

`API_FOOTBALL_API_KEY`
: API key for API-Football, if one is configured.

`SENTRY_DSN`
: Sentry DSN for backend error monitoring.

## Deployment order after merge

1. Create a Render Web Service for the backend from this GitHub repository:
   - Runtime/language: Docker
   - Root directory: `backend`
   - Dockerfile path: `Dockerfile`
   - Branch: `main`
   - Instance type: Free
   - Health check path: `/health`
   - Auto-deploy: disable it if you want GitHub Actions to gate deploys after tests; otherwise Render may deploy before CI finishes.
2. Add the Render backend environment variables listed above.
3. Copy the Render deploy hook URL into the GitHub repository secret `RENDER_DEPLOY_HOOK_URL`.
4. Create the Vercel frontend project and add the required Vercel/Vite GitHub secrets.
5. Run `Backend Deploy` from the `main` branch, then copy the Render backend URL.
6. Set or update `VITE_API_URL` with the Render backend URL.
7. Run `Frontend Deploy` and copy the Vercel frontend URL.
8. Set or update the Render `CORS_ORIGINS` environment variable with the Vercel frontend URL.
9. Re-run `Backend Deploy` so backend CORS allows the final frontend URL.

## Security note

Vite embeds all `VITE_*` variables into the browser bundle. Treat `VITE_API_KEY` as a public/demo client key, not a private admin secret. For production-grade access control, add real user authentication or a backend-for-frontend.
