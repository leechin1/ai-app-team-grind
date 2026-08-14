# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Notiq is an AI study platform (flashcards, quizzes, match games) generated from uploaded documents, with SM-2 spaced repetition. Two-part app: a FastAPI backend (`backend/`) and a Vite/React frontend (`frontend/`), backed by Supabase (Postgres + auth).

## Commands

### Backend (run from `backend/`, with `notiq_env` activated)

```bash
notiq_env\Scripts\activate        # from repo root, Windows
cd backend
python main.py                    # runs the API on http://0.0.0.0:8000 (Swagger UI at /docs)
```

There is no backend test framework (no pytest) — `backend/scripts/test_*.py` and `backend/test_database.py` are standalone scripts run directly, e.g.:

```bash
python backend/scripts/test_ai_generator.py
python backend/test_database.py
```

`backend/requirements.txt` only lists observability/HTTP dependencies (langfuse, opentelemetry, httpx, etc.) — it does **not** include `fastapi`, `uvicorn`, `supabase`, `google-genai`, `python-dotenv`, `PyPDF2`, `python-docx`, or `Pillow`, all of which `backend/` imports. Check `notiq_env` for what's actually installed rather than trusting the file, and add packages manually with `pip install` if setting up fresh.

### Frontend (run from `frontend/`)

```bash
npm run dev        # Vite dev server on http://localhost:8080 (NOT 5173 — README is stale on this)
npm run build
npm run lint
npm run preview
```

The dev server proxies `/api/*` to `http://127.0.0.1:8000` (see `frontend/vite.config.ts`), so the backend must be running separately for API calls to work. There is no frontend test script.

### Env vars (`.env` in repo root, read by the backend)

`GEMINI_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`, `DATABASE_URL`, and optionally `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST`.

## Architecture

### Backend

All routes live in one file, `backend/main.py`, grouped by `# ==== Section ====` comments (Projects, Notes, Documents, Flashcards, Chat/RAG, Quiz, Match Quiz, Study Stats). Business logic is factored into `backend/core/`:

- `supabase_client.py` — the `db` object (`SupabaseService`), all persistence. This is the single Supabase client wired into `main.py`.
- `auth.py` — `get_current_user` FastAPI dependency. **When no `Authorization` header is sent, it silently returns a hardcoded mock user instead of rejecting the request** — this is intentional for local dev but means auth bugs won't surface without deliberately sending a bearer token.
- `ai_generator.py` — Gemini calls via the `google.genai` client (not the older `google-generativeai` package). Langfuse tracing (`@observe`) is wrapped in a try/import so the app runs fine without Langfuse installed/configured.
- `embeddings_service_supabase.py`, `document_processor.py` (+ `utils/text_extraction.py`, `utils/gemini_vision.py`) — document ingestion pipeline: extract text/PDF/DOCX/image → chunk → embed.
- `spaced_repetition.py` — SM-2 algorithm implementation used by the flashcard review endpoints.
- `db_models.py` vs `models.py` — `db_models.py` are the Supabase row shapes (Create/Update/DB variants per table); `models.py` are the AI-generation/domain models (e.g. `FlashCard`, `QuizQuestion`, generation requests). Don't conflate the two when adding a field — it usually needs updating in both places plus the Supabase schema.
- `supabase_client.py` prefers `SUPABASE_SERVICE_KEY` over `SUPABASE_ANON_KEY` specifically to bypass Postgres RLS in dev; using the anon key in production relies on RLS policies actually being correct.

### Frontend

Vite + React 18 + TypeScript, shadcn/ui (Radix primitives) + Tailwind, TanStack Query for server state, react-router-dom for routing. Path alias `@/*` → `frontend/src/*`.

- `src/pages/` — one component per route (Dashboard, StudyHub, Flashcards, Quiz, MatchQuiz, Review, Editor, ChatIQ, StudyStats, etc.).
- `src/lib/api.ts` — the typed fetch client for the backend; request/response interfaces here should stay in sync with `backend/core/models.py` / `db_models.py`.
- `src/lib/auth.ts` — Supabase auth session handling on the client side, paired with `ProtectedRoute.tsx`.

### Data flow

Frontend → `/api/*` (proxied to FastAPI) → `core/*` services → Supabase (Postgres tables + pgvector-less embeddings) and the Gemini API for generation. Review events (flashcard/quiz/match) are also logged to `backend/data/review_events.jsonl` via `review_logger.py` for future ML training (see `backend/scripts/analyze_review_data.py` and `check_ml_readiness.py`).

Supabase schema reference: `SUPABASE_SCHEMA.md` (table-by-table docs) and `SUPABASE_SETUP_GUIDE.md` (how to provision a project from scratch), both at repo root.

The DB schema itself lives in the root `.sql` files, which are the only way to rebuild the database — `supabase_schema_v2_no_vector.sql` is the complete current schema (embeddings without pgvector), while `supabase_schema_v2_step1.sql` + `step2.sql` are the alternative two-stage path for a pgvector-enabled project. `disable_rls_for_dev.sql`, `create_mock_user_final.sql`, and `add_auto_profile_creation.sql` are re-runnable operational scripts (the first two support the dev-mode mock user described under `auth.py`).

There is no generated API reference in the repo — FastAPI serves the live one at `/docs` while the backend is running.
