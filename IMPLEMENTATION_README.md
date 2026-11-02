# Explainable RAG Studio — implementation handoff

The application now uses authenticated, private workspaces. Run the new
ownership migration before starting the API:

```powershell
cd backend
.\venv\Scripts\python.exe -m scripts.init_multi_user
```

`database/07_multi_user.sql` is safe to apply to the existing schema and does
not delete legacy rows. Existing documents and queries with no owner remain
unavailable to registered users until an administrator explicitly migrates
their ownership. Do not assign legacy records to every user.

## What is included
- `backend/app/main.py`: FastAPI routes for health, document list/upload, semantic search with explainability, grounded RAG, and query history.
- `backend/scripts/evaluate_retrieval.py`: labeled retrieval benchmark with Precision@K, Recall@K, MRR, NDCG@K, median and p95 latency.
- `backend/experiments/retrieval_benchmark.json`: starter query list. Relevant chunk IDs are deliberately blank and must be labeled before metrics are meaningful.
- `frontend/`: React + Vite interface for uploads, asking questions, retrieval explanations, grounding/citation status, latency metrics, and query history.

## Backend setup (PowerShell)
From the `backend` folder, activate your existing virtual environment and install the new upload dependency if needed:
```powershell
pip install "python-multipart>=0.0.9"
```
Ensure the existing `.env` file is in `backend/` and contains `DATABASE_URL` and `GROQ_API_KEY`. Optionally set `FRONTEND_ORIGINS` and `COOKIE_SECURE=true` in production. Do not copy secrets into the frontend.
Start API:
```powershell
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000/docs`.

Authentication is handled by short-lived opaque, HttpOnly session cookies.
The frontend must use `credentials: include`; it never receives or stores a
password or API key. The main endpoints are `/api/auth/register`,
`/api/auth/login`, `/api/auth/logout`, `/api/auth/me`, `/api/conversations`,
`/api/chat`, and the user-scoped document/search routes.

## Frontend setup
From the project root:
```powershell
cd frontend
npm install
npm run dev
```
Frontend uses the current browser hostname on port 8000 by default, keeping the
authentication cookie on the same host. If needed, copy `.env.example` to
`.env` and set `VITE_API_URL`; use the same hostname for the frontend and API
(do not mix `localhost` and `127.0.0.1`).

## Explainability evaluation
First run a few searches from the UI so you can inspect the returned chunk IDs. Edit `backend/experiments/retrieval_benchmark.json` and populate `relevant_chunk_ids` with IDs you manually verified as relevant for each query. Then run from `backend`:
```powershell
python -m scripts.evaluate_retrieval --dataset experiments/retrieval_benchmark.json --top-k 5
```
This uses real retrieval and writes `experiments/retrieval_evaluation_results.json`. It records query embedding and vector SQL timings separately and end-to-end retrieval latency. It does not call Groq, so evaluation itself does not incur LLM verification costs.

## Performance notes
- The retrieval service already records embedding time, vector-search time, and total retrieval time.
- SentenceTransformer is lazy-loaded and shared between service instances, so
  importing FastAPI does not download or initialize the model. `/health/live`
  is process-only and `/health/ready` checks the database without loading the
  model.
- The RAG response already reports generation and claim-verification latency. The frontend displays these values.
- The benchmark reports median and p95 wall latency. Run several times and compare with the same labeled queries before changing indexes or thresholds.
- Grounding/citation checks and the 0.45 retrieval threshold are intentionally preserved.

## Important integration note
The API routes use the service interfaces present in the uploaded backend. Run the backend and verify `/docs` and `/health` first. A schema mismatch will be surfaced by the relevant route; do not change the Neon schema blindly. Keep `.env`, database credentials, and API keys out of this archive.
