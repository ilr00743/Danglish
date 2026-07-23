# DanGlish Deployment

This runbook captures the first private deployment path:

- Frontend: Vercel, deployed from `frontend/`
- Backend: Render Web Service, deployed from `backend/`
- Database: PostgreSQL-compatible provider
- Ingestion: local manual CLI only
- Data: fresh curated ingest into an initially empty production database
- Domain: platform URLs first, no custom domain

The production data is disposable for this launch. It is okay to wipe and re-ingest while the channel set and ingestion process are still being shaped.

## PostgreSQL Database

1. Create a PostgreSQL database with any provider, such as Neon, Render PostgreSQL, Supabase, Railway, or a self-managed Postgres instance.
2. Copy the provider's connection string.
3. If the provider requires SSL, keep its SSL query parameters in the connection string, such as `sslmode=require`.

DanGlish initializes the schema automatically when the backend starts, using `backend/schema.sql`.

## Render Backend

Create a Render Web Service connected to this repository.

- Runtime: Python
- Root directory: `backend`
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Branch: `master`
- Auto-deploy: enabled

The repo pins Render's Python runtime with `.python-version` at the repository root. If the Render dashboard overrides this, set `PYTHON_VERSION` to a fully qualified Python 3.13 version, such as `3.13.5`.

Set these environment variables in Render:

```text
DATABASE_URL=<postgresql-connection-url>
BACKEND_CORS_ORIGINS=https://<vercel-app>.vercel.app,http://localhost:3000,http://127.0.0.1:3000
```

PostgreSQL providers may provide `DATABASE_URL` with a `postgres://` or `postgresql://` scheme and query parameters such as `sslmode=require`. The backend normalizes either scheme to SQLAlchemy's `postgresql+psycopg://` driver URL at startup while preserving query parameters.

Do not set `YOUTUBE_API_KEY` on the hosted backend for this private launch. There is no production web ingestion endpoint.

After the service deploys, check:

```text
https://<render-api-url>/api/health
```

Expected response:

```json
{ "status": "ok" }
```

In the Render service settings, set the HTTP health check path to:

```text
/api/health
```

Render uses this path to decide whether a newly deployed instance is ready for traffic and whether a running instance should be restarted.

## Pulsetic Backend Monitor

Use Pulsetic to monitor the hosted backend and send regular inbound traffic to the Render service.

Create a Pulsetic HTTP/API monitor with:

```text
URL: https://<render-api-url>/api/ready
Expected status: 200
Expected response body keyword: ok
Interval: 4 minutes
```

Pulsetic calls to `/api/ready` count as inbound HTTP traffic and run a cheap `SELECT 1` query against PostgreSQL. On a Render Free web service, this can keep the backend from idling out as long as the monitor keeps calling more often than Render's 15-minute idle window. For a Neon database with scale to zero enabled, the database query can also keep the compute active as long as the monitor runs more often than Neon's idle window. Neon Free computes suspend after 5 minutes of inactivity, so use a 4-minute interval instead of a 5-minute interval to leave room for monitor jitter.

If Pulsetic reports `/api/health` as online but `/api/ready` as offline, the backend process is reachable but the database connection is failing or Neon has not woken successfully.

Render can still restart or suspend Free services for platform maintenance, usage limits, or other Free-tier limits, and Neon can still suspend Free computes if no query reaches it within the idle window. This monitor is useful for a private launch but not a substitute for paid always-on instances.

## Vercel Frontend

Create a Vercel project connected to this repository.

- Framework preset: Next.js
- Root directory: `frontend`
- Branch: `master`
- Auto-deploy: enabled

Set this environment variable in Vercel:

```text
NEXT_PUBLIC_API_BASE_URL=https://<render-api-url>
```

After setting the environment variable, redeploy the frontend so the public API URL is baked into the Next.js build.

## Local Production Ingestion

The hosted backend only serves search and caption playback. Run ingestion locally against the production database.

Create or update `backend/.env` on your machine:

```text
DATABASE_URL=<postgresql-connection-url>
YOUTUBE_API_KEY=<your-local-youtube-api-key>
```

Then ingest one or more curated Danish channels:

```bash
cd backend
python ingest.py --channel-ids UCxxxx,UCyyyy
```

Channel IDs are passed manually for now. A channels table is intentionally deferred until ingestion becomes repeatable product behavior.

## Smoke Test

The first private deployment is successful when:

1. Render backend `/api/health` returns `{ "status": "ok" }`.
2. The production PostgreSQL database starts empty and the backend initializes the schema automatically.
3. Local ingestion adds captions for one curated Danish channel.
4. Vercel frontend search returns results for a known Danish word.
5. Clicking a Search Match loads YouTube and seeks near the caption.

## Reset And Reingest

While production data is disposable, use your database provider dashboard to reset the database, or connect with `psql` and clear the indexed content:

```sql
TRUNCATE captions, videos;
```

Restart the backend after a database reset so schema initialization runs again, then repeat local ingestion.

## Deferred

These are intentionally out of scope for the first private deployment:

- Docker
- Alembic migrations
- Channels table
- Hosted ingestion job
- Ingestion queue
- Custom domain
