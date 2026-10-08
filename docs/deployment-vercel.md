# Deploy Sachet on Vercel

This configuration uses two Vercel projects from the same repository and a hosted
PostgreSQL database (for example Neon). The frontend calls the API through
`VITE_API_BASE_URL`; the `/api` proxy remains for local development only.

The hosted version uses operator-provisioned pilot accounts. There is no public
signup, role switcher, email recovery or MFA. Account creation, password resets
and role assignment happen through the CLI below. Use a separate database for
preview deployments; previews must not share production cases or credentials.

## 1. Create a database and initialize it

Create a Neon PostgreSQL project. Copy the **pooled** connection string with SSL
enabled. Keep the connection string in your password manager or environment,
never in source control. `DATABASE_URL` selects PostgreSQL; when it is absent,
local development continues to use SQLite. Vercel refuses to start without it.

From the repository root, install the API dependencies in your virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r services/api/requirements.txt
$env:PYTHONPATH = (Join-Path (Get-Location) 'services/api')
$env:DATABASE_URL = Read-Host 'Paste the PostgreSQL connection string' -MaskInput
.\.venv\Scripts\python.exe -m app.manage migrate
```

`-MaskInput` requires PowerShell 7; on older PowerShell set the variable through
your terminal's secure environment tooling. Do not paste credentials into a
committed script. The CLI reads the process environment, not `.env` automatically.

Migration is idempotent and creates schema version 1. It does not copy the local
SQLite demo data. Start with a fresh pilot database unless a separate data import
is required. Existing local SQLite files are preserved and upgraded additively.

## 2. Provision pilot accounts

With the same `PYTHONPATH` and `DATABASE_URL` set:

```powershell
.\.venv\Scripts\python.exe -m app.manage account pilot-user --role user
.\.venv\Scripts\python.exe -m app.manage account pilot-analyst --role analyst
.\.venv\Scripts\python.exe -m app.manage account pilot-admin --role admin
```

Each command prompts for a password twice without echoing it. Use unique passwords
of at least 12 characters. Passwords use PBKDF2-HMAC-SHA256 with 600,000 iterations
and random salts. The API assigns roles from the stored account, never from login
input. Successful login issues an eight-hour bearer session, stored in browser
session storage; only its hash is stored in the database.

Run `account` again to reset a password or change a role; previous sessions are
revoked and the account's cases remain attached to the same owner. Disable access:

```powershell
.\.venv\Scripts\python.exe -m app.manage disable pilot-user
```

Login attempts are limited in the shared database: 10 per username and 60 per
client address in 15 minutes, including successful attempts. Local demo sessions
remain available only when `DEMO_MODE=true` outside Vercel.

## 3. Import the backend into Vercel

Push the prepared code to your Git repository, excluding `.env`, databases,
`.venv`, `node_modules`, and `.vercel`. Import the repository as a Vercel project:

| Setting | Value |
| --- | --- |
| Root Directory | `services/api` |
| Framework | FastAPI |
| Entry point | automatically detected `app/main.py` |
| Python | 3.12, specified by `.python-version` |
| Build / Output overrides | leave at framework defaults |

Set these **backend-only** environment variables:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | PostgreSQL pooled SSL connection string |
| `DEMO_MODE` | `false` |
| `CRON_SECRET` | random secret, at least 32 characters |
| `SACHET_ALLOWED_ORIGINS` | exact frontend origin, e.g. `https://your-web.vercel.app` |
| `GROQ_API_KEY`, `GROQ_MODEL` | optional, both needed for Groq |
| `GEMINI_API_KEY`, `GEMINI_MODEL` | optional, both needed for Gemini |
| `SACHET_CLOUD_DAILY_REQUEST_LIMIT` | optional, defaults to 40 shared calls/day |

Generate `CRON_SECRET` locally with `python -c "import secrets; print(secrets.token_urlsafe(48))"`
and paste it into Vercel's backend environment settings. Do not put it in frontend
variables. Vercel sets `VERCEL=1` itself. A missing database, enabled demo mode,
missing schema, or short/missing cron secret prevents hosted startup.

Deploy and check `https://YOUR-API.vercel.app/health`. It should report
`demo_mode: false` and `capabilities.storage: postgresql`.

## 4. Import the frontend

Create another Vercel project using the same repository:

| Setting | Value |
| --- | --- |
| Root Directory | `apps/web` |
| Framework | Vite |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Node.js | 22 or a supported newer version |

Set **frontend** `VITE_API_BASE_URL=https://YOUR-API.vercel.app` with no `/api` or
`/v1` suffix. The value is public and included in the frontend build; API keys,
database passwords and cron secrets must never use a `VITE_` variable.
The Vercel build fails if the API origin is absent or not HTTPS.

After Vercel assigns the frontend domain, set that exact origin in the backend's
`SACHET_ALLOWED_ORIGINS` and redeploy the backend. Multiple allowed origins may be
comma-separated, with no wildcard. Changing `VITE_API_BASE_URL` requires rebuilding
the frontend. Direct browser API requests require CORS and app authentication;
CORS is not an access-control substitute.

If Vercel Deployment Protection intercepts cross-project requests, use the intended
production API endpoint with Sachet authentication enabled, or configure the
platform's server-side protection integration. Never embed a protection-bypass
secret in `VITE_` settings.

## 5. Expiry and data deletion

`services/api/vercel.json` schedules `GET /internal/cron/expire` daily at 03:00 UTC.
Vercel supplies `Authorization: Bearer <CRON_SECRET>`. Requests without the secret
are rejected. The endpoint is idempotent and write transactions serialize across
serverless instances.

Hosted startup does not launch an endless cleanup task. Case access checks reject
expired cases immediately. Case and candidate lists also trigger cleanup. The daily
job removes expired cases and linked contributions, invalidates affected pattern
bundles, and expires sessions and login-attempt records. Physical removal can lag
the logical expiry until the next cleanup; a daily schedule is compatible with
Vercel Hobby but is not a promise of exact-minute deletion. For stricter deletion
timing, configure a scheduler/plan with the required interval.

Cases last seven days; candidate contributions have a maximum of 30 days and are
withdrawn earlier when their source case is deleted or expires.

## 6. Optional payment test integration

Only when testing the existing Razorpay integration, set `RAZORPAY_KEY_ID`,
`RAZORPAY_KEY_SECRET`, and `RAZORPAY_WEBHOOK_SECRET` on the backend. Use test keys;
the application rejects live keys. Configure the gateway webhook to
`https://YOUR-API.vercel.app/v1/webhooks/payments/razorpay` and verify its signature flow. No live payment capability
is enabled by this deployment work.

## 7. Verify before sharing the link

- Sign in as each assigned role. Users must not see a demo role switcher.
- Create a case, add evidence and correct it. Sign out/in and confirm the same
  account retains its case. Confirm another account cannot access it.
- Check analyst review and administrator release controls.
- Confirm an expired/revoked session returns to sign-in.
- Check screenshot extraction and configured cloud assessment. Keep the existing
  synthetic/public restriction for the free cloud route.
- Invoke the protected cleanup job and verify an expired case is removed.
- Redeploy, sign in again and confirm data persists in PostgreSQL.

## Local verification

```powershell
npm test
npm --prefix apps/web run build
```

To rerun tests on PostgreSQL, set `SACHET_TEST_DATABASE_URL` to a **disposable**
database whose name ends with `_test`. The test fixture clears its tables before
every test. The default suite deliberately ignores any real `DATABASE_URL`.

PostgreSQL uses a shared transaction advisory lock for modifying operations to
preserve the prototype's serialized SQLite write behavior across function
instances. Model API calls execute outside that lock. This is appropriate for
the initial pilot; larger workloads should use finer-grained locking and capacity
testing. No real-world detection accuracy is established by deployment checks.

Official references: [FastAPI](https://vercel.com/docs/frameworks/backend/fastapi),
[Vite](https://vercel.com/docs/frameworks/frontend/vite),
[Cron jobs](https://vercel.com/docs/cron-jobs/manage-cron-jobs).
