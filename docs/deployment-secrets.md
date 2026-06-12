# Deployment secrets

This file lists the GitHub Actions secrets needed by the free-hosting deployment workflows in this repository.

Add repository secrets in GitHub at:

`Settings -> Secrets and variables -> Actions -> New repository secret`

## Required secrets

### Backend / Koyeb

`KOYEB_API_TOKEN`
: Koyeb API token. Create it in Koyeb account settings.

`FRONTEND_URL`
: The deployed frontend URL, for example `https://your-project.vercel.app`. The backend deployment workflow passes this value to the backend as `CORS_ORIGINS`.

`BACKEND_API_KEYS`
: Comma-separated API key list accepted by the backend, for example `prod-demo-key-change-me`. The frontend `VITE_API_KEY` must match one of these values.

### Frontend / Vercel

`VERCEL_TOKEN`
: Vercel access token.

`VERCEL_ORG_ID`
: Vercel team/user/org ID for the project.

`VERCEL_PROJECT_ID`
: Vercel project ID.

`VITE_API_URL`
: The deployed backend URL, for example `https://your-backend.koyeb.app`.

`VITE_API_KEY`
: Browser-exposed API key sent as `X-API-Key`. It must match one of the values in `BACKEND_API_KEYS`.

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

1. Create Koyeb and Vercel projects/accounts.
2. Add all required GitHub Actions secrets above.
3. Run `Backend Deploy` and copy the Koyeb backend URL.
4. Set or update `VITE_API_URL` with that backend URL.
5. Run `Frontend Deploy` and copy the Vercel frontend URL.
6. Set or update `FRONTEND_URL` with that frontend URL.
7. Re-run `Backend Deploy` so backend CORS allows the final frontend URL.

## Security note

Vite embeds all `VITE_*` variables into the browser bundle. Treat `VITE_API_KEY` as a public/demo client key, not a private admin secret. For production-grade access control, add real user authentication or a backend-for-frontend.
