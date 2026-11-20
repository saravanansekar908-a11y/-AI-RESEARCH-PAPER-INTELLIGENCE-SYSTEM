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

## Separate Render deployment

The included `render.yaml` defines separate frontend and backend services, plus a managed PostgreSQL database and persistent PDF upload disk. To deploy, connect the GitHub repository to Render and create a Blueprint from that file. The database and persistent disk use paid Render plans. Before confirming creation, review the current plan prices in Render. Set `GEMINI_API_KEY` in the backend service environment after the Blueprint is created; it is intentionally marked secret and is not stored in this repository. The frontend build receives `VITE_API_URL`, and backend CORS is restricted to the frontend service URL.

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
