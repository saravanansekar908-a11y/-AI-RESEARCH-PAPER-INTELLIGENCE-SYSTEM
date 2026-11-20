# AI Research Paper Intelligence System

A private, evidence-grounded workspace for uploading scholarly PDFs, extracting their content, exploring them with RAG, comparing papers, drafting a source-linked literature review, and exporting findings.

## What is implemented

- Secure registration, login, logout, BCrypt password hashing, JWT sessions, CORS configuration, and owner-scoped records.
- PDF validation (type, signature, size), secure randomized storage, PyMuPDF text extraction, page-aware chunks, and explicit scanned-PDF/OCR status.
- Retrieval based on local embeddings. It uses Sentence Transformers when installed and falls back to a deterministic local hashing embedding so the application still works offline.
- Gemini integration controlled only by backend environment variables. Without a `GEMINI_API_KEY`, summaries and method extraction remain extractive and chat returns the relevant paper evidence instead of invented answers.
- Actual database-backed dashboard statistics, search, deletion, comparison, trend analytics, research-gap separation, literature-review draft generation, and PDF/DOCX exports.
- Responsive React/Vite dashboard with loading, empty, success, and error states.

## Run locally

Requirements: Python 3.12+, Node.js 20+, and optionally MySQL 8.

1. Configure the backend.

   ```powershell
   cd backend
   Copy-Item .env.example .env
   python -m pip install -r requirements.txt
   # Optional: use a Sentence Transformer instead of the local embedder
   # python -m pip install -r requirements-ai.txt
   uvicorn app.main:app --reload --port 8000
   ```

   The default `DATABASE_URL` is a local SQLite database to make first run immediate. For scanned PDFs, also install the [Tesseract OCR engine](https://github.com/tesseract-ocr/tesseract) and make it available on `PATH`. For MySQL, set the variable in `backend/.env` to:

   ```env
   DATABASE_URL=mysql+pymysql://research_user:strong-password@localhost:3306/research_intel
   JWT_SECRET=use-a-long-unique-random-value
   GEMINI_API_KEY=optional-google-api-key
   ```

   Create the MySQL database once with `CREATE DATABASE research_intel CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;`. Apply the included initial migration with `alembic upgrade head`. The development server also creates missing tables at startup to make the SQLite first run immediate.

2. Start the frontend in another terminal.

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   Open `http://localhost:5173`. The Vite dev server proxies API requests to port 8000. Set `VITE_API_URL` only when serving the frontend separately.

## API documentation

With the backend running, interactive OpenAPI documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs), and the schema is at `/openapi.json`.

## Deploy frontend and backend separately on Vercel

Vercel can deploy the Vite frontend and FastAPI backend as two projects from this repository. The backend uses Vercel's Python runtime through `backend/index.py`.

1. Create a PostgreSQL database through a Vercel Marketplace provider such as Neon, or another provider reachable from Vercel. Keep its connection URL private.
2. Import this GitHub repository into Vercel and create the backend project with **Root Directory** set to `backend`. Use the Python framework/runtime detection, then add these environment variables for Production (and Preview if desired):
   - `DATABASE_URL`: the provider's PostgreSQL connection string.
   - `JWT_SECRET`: a long, random secret.
   - `CORS_ORIGINS`: the exact production frontend origin, such as `https://your-frontend.vercel.app`.
   - `UPLOADS_DIR`: `/tmp/research-intel-uploads`.
   - `MAX_UPLOAD_MB`: `20`.
   - `GEMINI_API_KEY`: optional; add it only if you want Gemini-generated responses.
3. Deploy the backend project. Copy its production domain, then confirm `https://<backend-domain>/health` returns `{"status":"ok", ...}` and `/docs` opens.
4. Import the same GitHub repository a second time as a new Vercel project. Set **Root Directory** to `frontend`, choose Vite if prompted, and set `VITE_API_URL` to the backend's full origin, for example `https://your-api.vercel.app`.
5. Deploy the frontend. Update the backend's `CORS_ORIGINS` to the exact frontend production origin and redeploy the backend if needed.
6. Test registration, login, PDF upload, analysis, chat, and export from the frontend.

Vercel Functions have a read-only filesystem except for temporary `/tmp` storage. The app extracts and stores searchable paper sections in PostgreSQL, but the original PDF file itself is not durably retained on Vercel. If durable original-PDF retention is required, configure an external object store before using this deployment for long-term paper storage. The Python runtime and FastAPI support are documented in [Vercel's Python runtime guide](https://vercel.com/docs/functions/runtimes/python) and [FastAPI guide](https://vercel.com/docs/frameworks/backend/fastapi).

Key routes:

| Area | Routes |
| --- | --- |
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` |
| Papers | `POST /api/papers/upload`, `GET /api/papers`, `GET/DELETE /api/papers/{id}` |
| Analysis | `POST /api/analysis/{id}/summary`, `/methodology`, `/research-gaps` |
| Chat | `POST /api/chat/{id}`, `GET /api/chat/{id}/history` |
| Intelligence | `POST /api/compare`, `POST /api/literature-review/generate` |
| Metrics | `GET /api/dashboard/stats`, `GET /api/analytics/research-trends` |
| Export | `GET /api/exports/{id}/summary?format=pdf|docx` |

## Notes on AI and research integrity

Every chat call returns the supporting page excerpts used for retrieval. Gap analysis always separates paper-stated evidence from AI-generated hypotheses. No citations, bibliographic facts, or external results are fabricated. Add a Gemini key to enable model synthesis; keep it server-side in `backend/.env`.
