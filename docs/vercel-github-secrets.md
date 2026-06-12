# Vercel secrets for GitHub deployments

This guide lives at `docs/vercel-github-secrets.md` in this repository. It explains how to connect the GitHub Actions frontend deployment workflow to a Vercel project without committing credentials to git.

The workflow that consumes these values is `.github/workflows/frontend-deploy.yml`. It deploys the `frontend/` Vite application to Vercel when relevant changes reach `main` or when the workflow is run manually.

## Prerequisites

Before you start, make sure you have:

- Admin access to this GitHub repository, or permission to manage repository Actions secrets.
- Access to the Vercel account or team that owns the frontend project.
- A Vercel project created for the `frontend/` directory.
- The deployed backend URL, or a placeholder you will replace after the backend is deployed.
- A frontend API key value that matches one of the backend Render `VALID_API_KEYS` entries.

Do not paste real token values into issues, pull requests, commits, chat logs, or screenshots.

## Required GitHub Actions secrets

Add these secrets in GitHub under `Settings -> Secrets and variables -> Actions -> New repository secret`.

| GitHub secret | Where it comes from | Example placeholder |
| --- | --- | --- |
| `VERCEL_TOKEN` | Vercel account token used by the GitHub Action to run `vercel pull`, `vercel build`, and `vercel deploy`. | `vercel_token_from_account_settings` |
| `VERCEL_ORG_ID` | Vercel team or personal account ID for the project owner. | `team_xxxxxxxxxxxxxxxx` |
| `VERCEL_PROJECT_ID` | Vercel project ID for the frontend project. | `prj_xxxxxxxxxxxxxxxx` |
| `VITE_API_URL` | Public URL for the deployed backend API. | `https://your-backend.onrender.com` |
| `VITE_API_KEY` | Browser-exposed API key sent by the frontend as `X-API-Key`. Must match one of the backend Render `VALID_API_KEYS` values. | `public-demo-client-key-change-me` |

Related backend deployment secrets are documented in `docs/deployment-secrets.md`.

## Step 1: Create or confirm the Vercel project

1. Sign in to Vercel.
2. Create a new project from the GitHub repository, or open the existing project.
3. Set the project root directory to `frontend`.
4. Confirm the framework/build settings:
   - Framework preset: Vite
   - Build command: `npm run build`
   - Output directory: `dist`
5. Confirm `frontend/vercel.json` is present so client-side routes fall back to `index.html`.

You can let GitHub Actions handle production deploys. Avoid adding long-lived secrets to local `.env` files unless you need them for local testing, and never commit those files.

## Step 2: Find the Vercel IDs

Use either the Vercel dashboard or the Vercel CLI.

### Dashboard option

1. Open the Vercel project.
2. Go to `Settings -> General`.
3. Copy the project ID for `VERCEL_PROJECT_ID`.
4. Copy the team or account ID for `VERCEL_ORG_ID`.

### CLI option

From the repository root, run:

```bash
cd frontend
vercel login
vercel link
vercel pull --yes --environment=production
```

After linking, Vercel writes `.vercel/project.json` locally. Copy these values into GitHub secrets:

```json
{
  "orgId": "team_xxxxxxxxxxxxxxxx",
  "projectId": "prj_xxxxxxxxxxxxxxxx"
}
```

Use `orgId` for `VERCEL_ORG_ID` and `projectId` for `VERCEL_PROJECT_ID`.

Do not commit `.vercel/project.json`. It identifies the linked project and is local machine state.

## Step 3: Create the Vercel token

1. In Vercel, open `Account Settings -> Tokens`.
2. Create a token for GitHub Actions deployments.
3. Scope it to the smallest account/team and project access Vercel allows for this repository.
4. Copy the token once and save it as the GitHub secret `VERCEL_TOKEN`.

If a maintainer leaves the project or the token is exposed, revoke it in Vercel and replace the GitHub secret with a new token.

## Step 4: Set frontend runtime values

The frontend build uses Vite, so any variable whose name starts with `VITE_` is embedded into the static browser bundle.

Set these GitHub secrets:

- `VITE_API_URL`: the public backend API URL, for example `https://your-backend.onrender.com`.
- `VITE_API_KEY`: a public/demo client key that the backend accepts in Render `VALID_API_KEYS`.

Because `VITE_API_KEY` is shipped to every browser, do not use a private admin key. Treat it as public and rotate it if it is abused.

## Step 5: Add secrets in GitHub

1. Open the GitHub repository.
2. Go to `Settings -> Secrets and variables -> Actions`.
3. Select `New repository secret`.
4. Add each required secret exactly as named:
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`
   - `VITE_API_URL`
   - `VITE_API_KEY`
5. Save each secret.

GitHub only shows secret values once while you enter them. To change a value later, update or recreate the secret.

## Step 6: Verify the deployment

1. In GitHub, open `Actions -> Frontend Deploy`.
2. Run the workflow manually with `Run workflow`, or merge a frontend change to `main`.
3. Confirm these workflow steps pass:
   - `Install dependencies`
   - `Run linter`
   - `Pull Vercel environment`
   - `Build Vercel output`
   - `Deploy Vercel output`
4. Open the deployed Vercel URL.
5. In browser developer tools, confirm API requests go to the `VITE_API_URL` backend and not to `localhost:8000`.
6. If the app returns authentication errors, confirm `VITE_API_KEY` matches one of the backend Render `VALID_API_KEYS` values.

## Security notes

- Never commit real secrets, tokens, `.env` files, or `.vercel/project.json`.
- Use GitHub repository secrets, not plain workflow variables, for token and API key values.
- Keep placeholders obviously fake in documentation and examples.
- Rotate `VERCEL_TOKEN` after suspected exposure or staff changes.
- Remember that every `VITE_*` value is visible in the built frontend. Use it only for public client configuration.
- Prefer separate preview/staging and production projects if you need different credentials per environment.

## Troubleshooting

- `vercel pull` fails: check `VERCEL_TOKEN`, `VERCEL_ORG_ID`, and `VERCEL_PROJECT_ID`.
- `vercel build` cannot reach the API: confirm `VITE_API_URL` is set to the backend public URL.
- The deployed app shows `401` or `403`: confirm `VITE_API_KEY` is present and matches a backend key.
- The workflow does not run after a docs-only change: this is expected; `.github/workflows/frontend-deploy.yml` runs for frontend and workflow changes, or by manual dispatch.
