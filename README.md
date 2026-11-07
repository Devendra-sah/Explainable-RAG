# Explainable RAG

Explainable RAG is a private, multi-user document question-answering
application. Users upload PDF, DOCX, or TXT documents, ask grounded questions
in conversation-specific workspaces, and inspect why each retrieved chunk
supported an answer.

The project combines:

- FastAPI and PostgreSQL/pgvector for the backend
- Sentence Transformers for semantic embeddings
- Groq for grounded answer generation and claim verification
- React and Vite for the frontend
- Explainability scores, retrieval evidence, and grounding status for every
  answer

## Features

### Private workspaces

- User registration and login
- Bcrypt password hashing
- Short-lived opaque HttpOnly session cookies
- User-scoped documents, conversations, queries, and messages
- Cross-user access protection

### Conversation-scoped knowledge

- Upload documents directly from the active chat
- Documents are linked to the conversation where they were uploaded
- Retrieval only searches documents linked to the current conversation
- Returning to a conversation restores its messages and original document names
- New chat button for starting an isolated document context

### Grounded chat

- Sequential user and assistant messages
- PDF, DOCX, and TXT ingestion
- Chunking and vector embeddings
- Similarity retrieval with ownership and conversation filters
- Citation-aware answer generation
- Claim-level grounding verification
- Friendly responses to greetings such as `hi`, `hello`, and `hlo`

### Explainability

The **How was this answer generated?** panel reports:

- Retrieved document and chunk
- Rank and cosine similarity
- Semantic, keyword, and metadata scores
- Ranking and explainability scores
- Confidence level and score margin
- Evidence snippets
- Full **WHY RETRIEVED?** explanation
- Claim-level evidence and verification status
- Retrieval and verification latency

### Frontend experience

- Responsive Explainable RAG workspace
- Light and dark themes
- Shark/ocean ASCII visual design
- Conversation naming and renaming
- Per-chat document source display
- Documents panel
- Upload and delete controls
- Responsive authentication pages

## Project structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   └── services/
│   │       ├── claim_verification_service.py
│   │       ├── chunking_service.py
│   │       ├── context_builder.py
│   │       ├── document_extractor.py
│   │       ├── embedding_service.py
│   │       ├── explainability_service.py
│   │       ├── ingestion_service.py
│   │       ├── rag_service.py
│   │       └── retrieval_service.py
│   ├── scripts/
│   ├── tests/
│   ├── requirements.txt
│   └── .env
├── database/
│   ├── 01_schema.sql
│   ├── 02_indexes.sql
│   ├── 03_chunk_metadata.sql
│   ├── 04_explanation_evidence.sql
│   ├── 05_confidence_schema.sql
│   ├── 06_query_explanations.sql
│   └── 07_multi_user.sql
├── frontend/
│   ├── src/
│   │   ├── ascii-ocean/
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── package.json
│   └── .env.example
└── README.md
```

## Requirements

- Python 3.11+ recommended
- Node.js and npm
- PostgreSQL with the `vector` extension
- A Groq API key

The embedding model, tokenizer, and Groq client dependencies are loaded lazily
by the backend. This keeps startup and health checks fast. The first upload or
question may take longer while the embedding model/tokenizer is initialized.

## Configuration

Create `backend/.env`:

```env
DATABASE_URL=postgresql://user:password@host:5432/database
GROQ_API_KEY=your-groq-api-key

# Optional
GROQ_MODEL=openai/gpt-oss-120b
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
COOKIE_SECURE=false
```

Never commit `backend/.env`, database credentials, or API keys.

The frontend defaults to the current browser hostname on port `8000`. If an
override is needed, copy `frontend/.env.example` to `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Use the same hostname for the frontend and backend. Do not mix
`localhost` and `127.0.0.1`, because browser cookies are host-specific.

## Database setup

From the repository root, initialize the base schema:

```powershell
cd backend
.\venv\Scripts\python.exe -m scripts.init_database
```

Apply the supporting schemas when setting up a new database:

```powershell
.\venv\Scripts\python.exe -m scripts.init_indexes
.\venv\Scripts\python.exe -m scripts.init_explanation_schema
.\venv\Scripts\python.exe -m scripts.init_confidence_schema
.\venv\Scripts\python.exe -m scripts.init_claim_verification_schema
.\venv\Scripts\python.exe -m scripts.init_rag_schema
```

Apply the multi-user and conversation migration:

```powershell
.\venv\Scripts\python.exe -m scripts.init_multi_user
```

The migration is additive. It creates users, sessions, conversations,
messages, ownership fields, and conversation-document links. Legacy records
without an owner are not automatically assigned to users.

## Backend development

Create and activate a virtual environment if one does not already exist:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

For a faster, stable local run after development changes, omit the reload
watcher:

```powershell
uvicorn app.main:app
```

Use `--reload` only while actively editing backend files; its file watcher
starts a supervisor process and can make startup appear slower on Windows.

The API is available at:

- Application: <http://127.0.0.1:8000>
- Swagger UI: <http://127.0.0.1:8000/docs>
- Liveness: <http://127.0.0.1:8000/health/live>
- Readiness: <http://127.0.0.1:8000/health/ready>

Run backend validation:

```powershell
python -m compileall -q app
pytest
```

The multi-user security test requires a configured `DATABASE_URL` and an
initialized database.

## Frontend development

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal, normally
<http://localhost:5173>.

Create a production build:

```powershell
npm run build
```

Preview the production build:

```powershell
npm run preview
```

## Main API routes

### Authentication

| Method | Route | Purpose |
|---|---|---|
| `POST` | `/api/auth/register` | Create an account and session |
| `POST` | `/api/auth/login` | Sign in |
| `POST` | `/api/auth/logout` | End the current session |
| `GET` | `/api/auth/me` | Return the current user |

### Conversations and chat

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/conversations` | List the user’s conversations |
| `POST` | `/api/conversations` | Create a conversation |
| `GET` | `/api/conversations/{id}` | Load messages and linked documents |
| `PATCH` | `/api/conversations/{id}` | Rename a conversation |
| `DELETE` | `/api/conversations/{id}` | Delete a conversation |
| `POST` | `/api/chat` | Ask a grounded question |

### Documents and retrieval

| Method | Route | Purpose |
|---|---|---|
| `GET` | `/api/documents?conversation_id={id}` | List current-chat documents |
| `POST` | `/api/documents/upload` | Index a PDF, DOCX, or TXT file |
| `DELETE` | `/api/documents/{id}` | Delete an owned document |
| `POST` | `/api/search` | Run semantic search with explanations |
| `POST` | `/api/rag` | Run the RAG pipeline directly |
| `GET` | `/api/history` | Read query history |

All authenticated frontend requests use `credentials: "include"` so the
HttpOnly session cookie is sent to the API.

## Retrieval and answer pipeline

1. A user uploads a document in a conversation.
2. The extractor reads PDF, DOCX, or TXT content.
3. The chunking service creates overlapping text chunks.
4. Sentence Transformers creates vector embeddings.
5. The document, chunks, embeddings, and conversation link are stored.
6. A question is embedded and searched against only the active conversation’s
   documents.
7. Retrieved context is sent to the configured Groq model with citation
   constraints.
8. Citation validation checks that cited labels exist.
9. Claim verification checks answer claims against retrieved evidence.
10. Explainability records are generated and shown in the frontend.
11. The answer, metadata, sources, and verification details are persisted in
    the conversation.

If retrieval evidence is insufficient, the system abstains rather than
inventing an answer.

## Explainability and retrieval scripts

Run the explainability script after a query has been stored:

```powershell
cd backend
python -m scripts.test_explainability
```

Run the retrieval benchmark:

```powershell
python -m scripts.evaluate_retrieval `
  --dataset experiments/retrieval_benchmark.json `
  --top-k 5
```

Populate `relevant_chunk_ids` in the benchmark dataset before relying on its
precision, recall, MRR, or NDCG results.

Useful diagnostics include:

```powershell
python -m scripts.check_database
python -m scripts.check_embeddings
python -m scripts.check_ingestion
python -m scripts.check_retrieval
python -m scripts.check_explanations
python -m scripts.test_groq
```

## Security notes

- Passwords are hashed with bcrypt.
- Session tokens are stored as SHA-256 hashes, not plaintext tokens.
- Session cookies are HttpOnly and use `SameSite=Lax`.
- User ownership is enforced in API queries and vector retrieval.
- Conversation ownership is checked before loading or modifying chat data.
- Conversation-document links prevent documents from leaking between chats.
- Secrets are loaded only by the backend.
- Do not expose `GROQ_API_KEY` or `DATABASE_URL` in frontend files.
- Use HTTPS and set `COOKIE_SECURE=true` when deploying behind HTTPS.
- Configure explicit production CORS origins instead of relying on development
  localhost rules.

## Troubleshooting

### `Authentication required`

Use one hostname consistently:

```text
Frontend: http://localhost:5173
Backend:  http://localhost:8000
```

Then hard-refresh and sign in again. Switching between `localhost` and
`127.0.0.1` creates separate browser cookie scopes.

### `Failed to fetch`

Check:

1. The backend is running on port `8000`.
2. `/health/live` returns `{"status":"alive"}`.
3. The frontend API URL matches the backend hostname.
4. `FRONTEND_ORIGINS` includes the frontend origin.
5. Only one backend process is using port `8000`.

### Answers say there is insufficient evidence

Confirm that:

1. The document was uploaded in the current conversation.
2. The document appears under **Current chat sources**.
3. The multi-user migration was applied.
4. The question is supported by the uploaded content.
5. The database contains indexed chunks and embeddings.

### A document shows a temporary filename

Re-upload the document after applying the current backend. New uploads retain
the original browser filename. Older records may contain temporary names because
the original upload name was not stored at ingestion time.

## License and academic use

This repository is an academic DBMS/RAG implementation project. Add a project
license before distributing it outside its intended course or team context.
