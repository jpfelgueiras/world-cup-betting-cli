# Render secrets for GitHub backend deployments

This guide lives at `docs/render-github-secrets.md` in this repository. It explains how to connect the GitHub Actions backend deployment workflow to a Render Web Service without committing credentials or runtime secrets to git.

The workflow that consumes the GitHub secret is `.github/workflows/backend-deploy.yml`. It tests the `backend/` FastAPI application, builds the Docker image from `backend/Dockerfile`, and triggers a Render deploy when relevant changes reach `main` or when the workflow is run manually.

## Prerequisites

Before you start, make sure you have:

- Admin access to this GitHub repository, or permission to manage repository Actions secrets.
- Access to the Render account or team that owns the backend service.
- A Render `Web Service` for the `backend/` directory, or permission to create one.
- A deployed or planned frontend URL so backend CORS can allow it.
- A frontend API key value that will also be configured in Render `VALID_API_KEYS`.
- Any optional provider keys you intend the backend to use, such as football data or monitoring keys.

Use fake placeholders in notes and tickets. Do not paste real deploy hook URLs, API keys, tokens, `.env` files, or screenshots that show secret values into issues, pull requests, commits, or chat logs.

## Required GitHub Actions secrets

Add GitHub Actions secrets under `Settings -> Secrets and variables -> Actions -> New repository secret`.

| GitHub secret | Where it comes from | Example placeholder |
| --- | --- | --- |
| `RENDER_DEPLOY_HOOK_URL` | Render backend service deploy hook URL from `Settings -> Deploy Hook`. | `https://api.render.com/deploy/srv-fake123?key=fake-render-hook-key` |

Only the deploy hook URL belongs in GitHub for the current backend workflow. Backend runtime values such as `CORS_ORIGINS`, `VALID_API_KEYS`, provider API keys, and `DEV_MODE` must be set on the Render service, not in GitHub Actions, because the running container reads them from Render at runtime.

Related frontend Vercel deployment secrets are documented in `docs/vercel-github-secrets.md`. The combined free-hosting deployment guide is `docs/free-hosting-deployment.md`.

## Required Render backend environment variables

Set these in the Render dashboard for the backend Web Service under `Environment`. Keep examples obviously fake.

| Render variable | Example placeholder | Notes |
| --- | --- | --- |
| `DEV_MODE` | `false` | Production deployments should require API keys. |
| `ENABLE_CORS` | `true` | Required for the hosted frontend to call the API from a browser. |
| `CORS_ORIGINS` | `https://your-frontend.vercel.app` | Use the exact deployed frontend origin. Do not include a trailing slash or path. |
| `VALID_API_KEYS` | `public-demo-client-key-change-me` | Comma-separated API keys accepted by the backend. The frontend `VITE_API_KEY` must match one entry. |
| `LOG_LEVEL` | `INFO` | Production log verbosity. |

Optional variables if real data providers or monitoring are enabled later:

| Render variable | Purpose |
| --- | --- |
| `FOOTBALL_DATA_API_KEY` | Football data provider API key. |
| `FBREF_API_KEY` | FBref-compatible data provider key, if configured. |
| `API_FOOTBALL_API_KEY` | API-Football provider key, if configured. |
| `SENTRY_DSN` | Backend error monitoring DSN. |
| `ENABLE_METRICS` | Enable Prometheus metrics if the deployment is configured to expose them. |

Render provides `PORT` automatically. Do not add a hard-coded `PORT` value unless Render support asks you to. The backend Dockerfile starts Uvicorn with `${PORT:-8000}` and its healthcheck uses the same platform-provided port.

## Step 1: Create or confirm the Render Web Service

1. Sign in to Render.
2. Create a new `Web Service`, or open the existing backend service.
3. Connect the GitHub account or organization that owns this repository.
4. Select this repository.
5. Configure the service with these settings:

   | Setting | Value |
   | --- | --- |
   | Runtime/language | `Docker` |
   | Branch | `main` |
   | Root directory | `backend` |
   | Dockerfile path | `Dockerfile` |
   | Instance type | `Free` |
   | Health check path | `/health` |
   | Auto-deploy | `Off` if GitHub Actions should gate deploys after tests; otherwise Render may deploy before CI finishes |

6. Save the service.
7. Wait for the first Render build to finish, or skip the first deploy if you plan to trigger it from GitHub Actions after the secret is configured.

This repository expects Python 3.11 in the backend image. Render should build through `backend/Dockerfile`; you do not need separate Render build or start commands when using Docker. The Dockerfile installs `backend/requirements.txt`, installs the package, and starts:

```bash
python -m uvicorn src.api.app:app --host 0.0.0.0 --port ${PORT:-8000}
```

Render Free Web Services can sleep after inactivity. The first request after sleep may be slow while the container cold starts. That is expected on the free tier and does not necessarily mean the deploy failed.

## Step 2: Set Render runtime environment variables

1. Open the backend service in Render.
2. Go to `Environment`.
3. Add the required variables listed above:
   - `DEV_MODE=false`
   - `ENABLE_CORS=true`
   - `CORS_ORIGINS=https://your-frontend.vercel.app`
   - `VALID_API_KEYS=public-demo-client-key-change-me`
   - `LOG_LEVEL=INFO`
4. Add optional provider keys only if the backend feature that needs them is enabled.
5. Save changes.

If the final frontend URL is not known yet, use the expected Vercel production origin as a temporary value, deploy the frontend, then return to Render and update `CORS_ORIGINS` to the final origin.

## Step 3: Create and copy the Render deploy hook

1. In the Render backend service, open `Settings`.
2. Find the `Deploy Hook` section.
3. Create a deploy hook if one does not already exist.
4. Copy the deploy hook URL once.
5. Treat the URL as a secret. Anyone with it can trigger a backend deploy.

If the deploy hook URL is exposed, regenerate it in Render and replace the GitHub secret immediately.

## Step 4: Save the deploy hook as a GitHub secret

1. Open the GitHub repository.
2. Go to `Settings -> Secrets and variables -> Actions`.
3. Select `New repository secret`.
4. Name the secret exactly `RENDER_DEPLOY_HOOK_URL`.
5. Paste the Render deploy hook URL as the value.
6. Save the secret.

GitHub only shows secret values while you enter them. To rotate the hook later, regenerate it in Render and update the GitHub secret with the new URL.

## Step 5: Confirm how the backend workflow deploys

The workflow name is `Backend Deploy`, defined in `.github/workflows/backend-deploy.yml`.

It runs on pushes to `main` that touch backend files or the backend workflow:

- `backend/**`
- `.github/workflows/backend-deploy.yml`

It can also be started manually with `workflow_dispatch` from the GitHub Actions UI.

The workflow steps are:

1. Check out the repository.
2. Set up Python 3.11.
3. Install dependencies from `backend/requirements.txt` and install the backend package.
4. Run `python -m pytest tests -q` in `backend/`.
5. Build the Docker image with `backend/Dockerfile`.
6. On `refs/heads/main`, send a `POST` request to `RENDER_DEPLOY_HOOK_URL`.

The deploy hook step intentionally runs only on `main`. Manual runs or branch runs that are not on `main` can validate the backend but will not trigger Render.

## Step 6: Verify the deployment

1. In GitHub, open `Actions -> Backend Deploy`.
2. Run the workflow manually on branch `main`, or merge a backend or workflow change to `main`.
3. Confirm these GitHub Actions steps pass:
   - `Install backend dependencies`
   - `Run backend tests`
   - `Build backend Docker image`
   - `Trigger Render deploy`
4. Open the Render backend service dashboard.
5. Confirm a new Render deploy starts after the GitHub Actions deploy hook step.
6. Watch the Render deploy logs until the deploy is `Live`.
7. Test the public health endpoint:

   ```bash
   curl --fail https://your-backend.onrender.com/health
   ```

8. Optionally test the API versioned health endpoint:

   ```bash
   curl --fail https://your-backend.onrender.com/api/v1/health
   ```

9. Test an authenticated API endpoint by sending the `X-API-Key` header with one of the values configured in Render `VALID_API_KEYS`. Keep the real key out of documentation and shell history. For example, replace this URL with the deployed backend and add the API-key header from your local-only secret store:

   ```bash
   curl --fail https://your-backend.onrender.com/api/v1/value-bets
   ```

10. Open the deployed frontend and confirm browser requests go to the Render backend URL, not `localhost:8000`.
11. If the frontend receives `401` or `403` responses, confirm its `VITE_API_KEY` matches one comma-separated value in Render `VALID_API_KEYS`.
12. If the frontend receives CORS errors, confirm Render `CORS_ORIGINS` exactly matches the deployed frontend origin.

## Security notes

- Never commit real deploy hook URLs, API keys, tokens, `.env` files, or local Render/Vercel project state.
- Store `RENDER_DEPLOY_HOOK_URL` as a GitHub repository secret, not as a plain workflow variable.
- Store backend runtime secrets in Render environment variables, not in the GitHub workflow.
- Keep documentation examples obviously fake.
- Regenerate the Render deploy hook after suspected exposure or staff changes.
- Treat `VALID_API_KEYS` values as bearer credentials. Rotate them if exposed.
- Remember that the frontend `VITE_API_KEY` is embedded in the browser bundle. Use a public/demo client key there, not a private admin key.
- Prefer separate Render services or environments for staging and production if you need different credentials.

## Troubleshooting

- `Trigger Render deploy` fails with an empty secret: confirm `RENDER_DEPLOY_HOOK_URL` is set under GitHub repository Actions secrets and is available to the `Backend Deploy` workflow.
- `Trigger Render deploy` returns an HTTP error: regenerate the deploy hook in Render, update the GitHub secret, and re-run the workflow.
- The GitHub workflow passes but Render does not deploy: confirm the workflow ran on `refs/heads/main`; the deploy hook step is intentionally gated to `main`.
- Render build fails before the app starts: check the Render deploy logs and confirm Runtime/language is `Docker`, Root directory is `backend`, and Dockerfile path is `Dockerfile`.
- Render health check fails: confirm the health check path is `/health`, the service binds to `0.0.0.0`, and Render is providing `PORT`.
- The first request is slow or times out: the Render free service may be waking from sleep. Wait for the service to become live and retry.
- The app returns `401` or `403`: confirm `DEV_MODE=false` is expected and the request sends `X-API-Key` with a value present in Render `VALID_API_KEYS`.
- The frontend gets CORS errors: set Render `CORS_ORIGINS` to the exact frontend origin, for example `https://your-project.vercel.app`, with no trailing slash or path, then redeploy or restart the backend.
- Runtime config changes do not appear: restart or redeploy the Render service after changing environment variables.
