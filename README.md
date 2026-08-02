# DanGlish

DanGlish is a Danish-focused YouGlish clone:
- Search for a Danish word.
- Match against pre-indexed YouTube transcript captions in PostgreSQL.
- Play matching videos starting 5 seconds before the word is spoken.

## Project Structure

```text
backend/
  main.py
  database.py
  ingest.py
  schema.sql
frontend/
  app/
  components/
  lib/
```

## Backend Setup (FastAPI + PostgreSQL)

1. Create a PostgreSQL database named `danglish`.
2. Copy `backend/.env.example` to `backend/.env` and set values.
3. Install dependencies:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

4. Run API server:

```bash
uvicorn main:app --reload --port 8000
```

API endpoint:
- `GET /api/search?q=ord`

## Ingestion Pipeline

From the `backend` folder:

```bash
python ingest.py --channel-ids UCxxxxxxxxxxxx,UCyyyyyyyyyyyy
```

Optional upload selection controls:

```bash
python ingest.py --channel-ids UCxxxxxxxxxxxx --older-first
python ingest.py --channel-ids UCxxxxxxxxxxxx --newer-first
python ingest.py --channel-ids UCxxxxxxxxxxxx --published-from 2020-01-01 --published-to 2021-12-31 --older-first
```

What it does:
- Uses `google-api-python-client` to list channel uploads.
- Uses `youtube-transcript-api` to fetch manually added Danish (`da`) transcripts.
- Stores `videos` and `captions` rows in PostgreSQL.
- Maintains a Danish full-text search GIN index via `schema.sql`.

## Caption Discovery

Before ingesting a new channel, generate a caption availability report:

```bash
python discover_captions.py --channel-ids UCxxxxxxxxxxxx,UCyyyyyyyyyyyy --output caption-report.csv
```

The discovery report scans older uploads first by default and records each video's:
- video id
- title
- channel name
- publish date
- Danish caption status: `manual_da`, `generated_da`, `no_da`, or `lookup_failed`

Use `--format json` for JSON output, `--newer-first` to reverse the scan order, and `--limit` for a smaller first pass.

## Frontend Setup (Next.js + Tailwind)

1. Copy `frontend/.env.example` to `frontend/.env.local`.
2. Install dependencies and run:

```bash
cd frontend
npm install
npm run dev
```

Open:
- [http://localhost:3000](http://localhost:3000)

## Database Schema

`backend/schema.sql` defines:
- `videos (id, title, channel_name)`
- `captions (id, video_id, text, start_time, duration, search_vector)`

`search_vector` is generated with:
- `to_tsvector('danish', text)`

And indexed with:
- `GIN (search_vector)`

## Deployment

For the first private launch on Vercel, Render Web Service, and any PostgreSQL-compatible provider, see [DEPLOYMENT.md](DEPLOYMENT.md).
