# Free hosting deployment guide

This repository is a split application:

- `backend/`: FastAPI service packaged as a Docker image in `backend/Dockerfile`
- `frontend/`: Vite/React static application

The selected free-hosting setup is:

1. Backend on Render Free Web Service
2. Frontend on Vercel Hobby, with Netlify as a manual frontend alternative

Koyeb is obsolete for this repository. The backend GitHub Actions workflow no longer uses Koyeb secrets or Koyeb deployment commands; it validates the backend, builds the Docker image in CI, and then triggers Render through `RENDER_DEPLOY_HOOK_URL`.

## Accounts and prerequisites

Create or confirm access to these accounts before configuring secrets:

- GitHub account with `Admin` access to this repository, so you can add Actions secrets.
- Render account. The free workspace is sufficient for the demo backend.
- Vercel account for the frontend. A Hobby project is sufficient for the Vite app.
- Optional: Netlify account if you choose the manual Netlify frontend path instead of Vercel.

Local tools are not required for the hosted deployment, but they are useful for troubleshooting:

```bash
git clone <repository-url>
cd world-cup-betting-cli
cd backend && python -m pytest tests -q
cd ../frontend && npm ci && npm run lint && npm run build
```

## Backend: Render Free Web Service

Render is the selected free backend provider because it can build and run this backend from the existing Dockerfile, provides a Free Web Service tier suitable for a demo API, supports `/health` checks, and exposes deploy hooks that fit the GitHub Actions workflow.

For a dedicated Render/GitHub Actions operator checklist, see `docs/render-github-secrets.md`.

### 1. Create the Render backend service

1. Sign in to Render.
2. Create a new `Web Service`.
3. Connect the GitHub account or organization that owns this repository.
4. Select this repository.
5. Use these service settings:

   | Setting | Value |
   | --- | --- |
   | Runtime/language | `Docker` |
   | Branch | `main` |
   | Root directory | `backend` |
   | Dockerfile path | `Dockerfile` |
   | Instance type | `Free` |
   | Health check path | `/health` |
   | Auto-deploy | `Off` if GitHub Actions should gate deploys; otherwise Render may deploy before CI tests finish |

6. Save the service.

Render provides `PORT` automatically. Do not add a hard-coded `PORT` value unless Render support asks you to. The Dockerfile starts Uvicorn with `${PORT:-8000}`.

### 2. Set Render runtime environment variables

Open the Render service dashboard and add these environment variables to the backend Web Service:

| Variable | Value | Notes |
| --- | --- | --- |
| `DEV_MODE` | `false` | Runs the API in production mode. |
| `ENABLE_CORS` | `true` | Required for the hosted frontend to call the API. |
| `CORS_ORIGINS` | `https://your-frontend.vercel.app` | Use the final frontend URL. During first backend deployment, use a temporary expected Vercel URL or update it after frontend deployment. |
| `VALID_API_KEYS` | `public-demo-client-key-change-me` | Comma-separated keys accepted by the backend. `VITE_API_KEY` must match one of these. |
| `LOG_LEVEL` | `INFO` | Production log verbosity. |

Optional variables if real data sources or monitoring are enabled later:

| Variable | Purpose |
| --- | --- |
| `FOOTBALL_DATA_API_KEY` | Football data provider API key. |
| `FBREF_API_KEY` | FBref-compatible data provider key, if configured. |
| `API_FOOTBALL_API_KEY` | API-Football provider key, if configured. |
| `SENTRY_DSN` | Backend error monitoring. |

### 3. Create the Render deploy hook

1. In the Render backend service, open `Settings`.
2. Find `Deploy Hook`.
3. Copy the deploy hook URL.
4. Store it in GitHub as the repository secret `RENDER_DEPLOY_HOOK_URL`.
5. If the URL is ever pasted into a public place, regenerate it in Render and replace the GitHub secret.

Anyone with the deploy hook URL can trigger a backend deploy, so treat it as a secret.

### 4. How backend deployment works from GitHub Actions

`.github/workflows/backend-deploy.yml` runs on pushes to `main` that touch backend files or the backend workflow, and it can also be started manually with `workflow_dispatch`.

The workflow:

1. Checks out the repository.
2. Sets up Python 3.11.
3. Installs backend dependencies from `backend/requirements.txt` and the editable package.
4. Runs `python -m pytest tests -q` in `backend/`.
5. Builds the Docker image with `backend/Dockerfile`.
6. On `main`, posts to `RENDER_DEPLOY_HOOK_URL` to ask Render to build and deploy the service.

The workflow requires this GitHub repository secret:

- `RENDER_DEPLOY_HOOK_URL`

It does not require any Koyeb secrets.

### 5. Manual Render deployment or verification

To deploy manually without waiting for a push:

1. Open GitHub Actions.
2. Select `Backend Deploy`.
3. Choose `Run workflow` on branch `main`.
4. Wait for the job to finish.
5. Open the Render service dashboard and confirm a new deploy starts and completes.
6. Open the service URL and test the health endpoint:

```bash
curl --fail https://your-backend.onrender.com/health
```

A healthy response confirms the container is accepting HTTP traffic. If the first request is slow, wait and retry; free services can cold start after inactivity.

## Frontend: Vercel Hobby

Vercel is the selected frontend host because it works well for Vite/React static builds and the existing `.github/workflows/frontend-deploy.yml` deploys prebuilt output through the Vercel CLI.

### 1. Create the Vercel project

1. Sign in to Vercel.
2. Import this GitHub repository.
3. Configure the project with:

   | Setting | Value |
   | --- | --- |
   | Framework preset | `Vite` |
   | Root directory | `frontend` |
   | Build command | `npm run build` |
   | Output directory | `dist` |

4. Confirm `frontend/vercel.json` is present so direct SPA routes fall back to `index.html`.
5. Create a Vercel access token from Vercel account settings.
6. Find the Vercel project ID and team/user/org ID. The easiest way is to run `vercel link` locally and inspect `.vercel/project.json`, or copy them from Vercel project settings.

### 2. Set Vercel/GitHub frontend secrets

Add these GitHub repository secrets for `.github/workflows/frontend-deploy.yml`:

| Secret | Description |
| --- | --- |
| `VERCEL_TOKEN` | Vercel access token. |
| `VERCEL_ORG_ID` | Vercel team/user/org ID for the project owner. |
| `VERCEL_PROJECT_ID` | Vercel project ID. |
| `VITE_API_URL` | Public Render backend URL, for example `https://world-cup-betting-backend.onrender.com`. |
| `VITE_API_KEY` | Browser-exposed API key sent as `X-API-Key`; must match one value in Render `VALID_API_KEYS`. |

Important: Vite embeds all `VITE_*` values into the browser bundle. Treat `VITE_API_KEY` as a public/demo client key, not a private admin secret. For production-grade access control, add real user authentication or a backend-for-frontend.

### 3. How frontend deployment works from GitHub Actions

`.github/workflows/frontend-deploy.yml` runs on pushes to `main` that touch frontend files or the frontend workflow, and it can also be started manually with `workflow_dispatch`.

The workflow:

1. Checks out the repository.
2. Sets up Node.js 22.
3. Runs `npm ci`.
4. Runs `npm run lint`.
5. Installs the Vercel CLI.
6. Pulls Vercel project environment for production.
7. Builds the production Vercel output.
8. Deploys the prebuilt output to production.

## First full deployment order

Use this order for the first deployment so backend CORS and frontend API settings end up aligned:

1. Create the Render backend Web Service with the settings above.
2. Add Render backend runtime environment variables. If you do not know the final frontend URL yet, set `CORS_ORIGINS` to the expected Vercel URL and update it later.
3. Copy the Render deploy hook URL into the GitHub secret `RENDER_DEPLOY_HOOK_URL`.
4. Create the Vercel frontend project for `frontend/`.
5. Add the Vercel and Vite GitHub repository secrets: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`, `VITE_API_URL`, and `VITE_API_KEY`.
6. Merge the deployment changes into `main`.
7. Run `Backend Deploy` from GitHub Actions, or push a backend/workflow change to `main`.
8. Confirm the Render backend URL and `/health` endpoint.
9. If needed, update the GitHub secret `VITE_API_URL` with the final Render URL.
10. Run `Frontend Deploy` from GitHub Actions, or push a frontend/workflow change to `main`.
11. Copy the final Vercel production URL.
12. Update the Render `CORS_ORIGINS` environment variable with the final Vercel URL.
13. Re-run `Backend Deploy` or trigger a Render manual deploy so the backend uses the final CORS setting.
14. Open the frontend and confirm API calls go to the Render backend.

## Smoke tests after deployment

Backend:

```bash
curl --fail https://your-backend.onrender.com/health
curl --fail https://your-backend.onrender.com/api/v1/health
```

Both health endpoints are public and should succeed once the service is awake. Use an authenticated API endpoint with `-H "X-API-Key: public-demo-client-key-change-me"` when testing the API key itself.

Frontend:

1. Open the Vercel production URL.
2. Navigate through the app.
3. In browser developer tools, confirm API requests use `VITE_API_URL` and do not point to `localhost:8000`.
4. If requests fail with authentication errors, confirm `VITE_API_KEY` exactly matches one comma-separated entry in Render `VALID_API_KEYS`.
5. If requests fail with CORS errors, update Render `CORS_ORIGINS` to the exact Vercel origin, without a trailing path.

## Frontend alternative: Netlify

`netlify.toml` is included for a manual Netlify setup if you choose not to use Vercel:

- Base directory: `frontend`
- Build command: `npm ci && npm run build`
- Publish directory: `frontend/dist`
- SPA fallback: configured with a redirect to `/index.html`

If Netlify is used, replace Vercel-specific frontend steps with equivalent Netlify project settings and set Render `CORS_ORIGINS` to the Netlify site URL.

## Troubleshooting free-tier deployments

### Render service sleeps or first request is slow

Render free services can sleep after inactivity. The first request after sleep may take longer while the container starts. Retry the request after the service wakes. For user-facing production traffic, upgrade the instance or use another always-on provider.

### Render deploy fails during build

Check the Render deploy logs first. Common causes are dependency installation failures, Dockerfile path mistakes, or selecting the repository root instead of `backend` as the root directory. Confirm the service settings match this guide.

### Render instance runs out of memory

The backend dependencies include pandas, scikit-learn, and xgboost, so the free instance may be tight on memory. If the service is killed or repeatedly restarts, reduce memory usage, remove unused heavy dependencies, or use the documented fallback provider from the provider-selection task: Google Cloud Run.

### Render health check fails

Confirm the Render health check path is `/health`, `DEV_MODE=false`, and Render is providing `PORT`. Do not configure the service to bind only to `localhost`; the Dockerfile should start Uvicorn on `0.0.0.0`.

### GitHub Actions backend workflow passes but Render does not deploy

Confirm `RENDER_DEPLOY_HOOK_URL` is set as a repository secret, not an environment variable. Regenerate and replace the hook if it was copied incorrectly. Also confirm the workflow ran on `refs/heads/main`; the deploy hook step is intentionally gated to `main`.

### Frontend deploy succeeds but the app calls localhost

Confirm `VITE_API_URL` is set as a GitHub repository secret before the Vercel build runs. Re-run `Frontend Deploy` after changing it because Vite embeds the value at build time.

### API calls fail with CORS errors

Set Render `CORS_ORIGINS` to the exact frontend origin, for example `https://your-project.vercel.app`. Do not include a trailing slash or path. Redeploy/restart the backend after changing it.

### API calls fail with 401 or API-key errors

Confirm the frontend `VITE_API_KEY` value exactly matches one entry in Render `VALID_API_KEYS`. If `VALID_API_KEYS` contains multiple keys, separate them with commas and no accidental spaces unless the backend trims them.

### Quotas, regions, and ephemeral storage

Free tiers have quota and region limitations. Keep the demo low traffic, expect occasional cold starts, and do not store durable user data in the container filesystem because runtime filesystem changes can be discarded. Use managed storage if the app later needs persistence.

## Obsolete provider note

Older docs or branches may mention Koyeb. Treat those instructions as obsolete for this repository. The current backend deployment path is Render plus `RENDER_DEPLOY_HOOK_URL`; old Koyeb secrets such as tokens, app names, or service IDs are not required by the current workflow.
