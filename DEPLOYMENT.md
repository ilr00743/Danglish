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
- Monitoring and alerting
- Custom domain
