import hashlib
import os
import re
import secrets
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import psycopg
from dotenv import load_dotenv
from fastapi import Cookie, Depends, FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from psycopg.errors import UniqueViolation
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.services.document_extractor import DocumentExtractor
from app.services.ingestion_service import DocumentIngestionService
from app.services.rag_service import RAGService
from app.services.retrieval_service import RetrievalService
from app.services.explainability_service import ExplainabilityService

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "")
SESSION_COOKIE = "explainable_rag_session"
SESSION_DAYS = 7
LOGIN_ATTEMPTS: dict[str, list[float]] = {}

app = FastAPI(
    title="Explainable Vector Database RAG",
    version="1.0.0",
    description="Private, multi-user document retrieval and grounded RAG.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv(
        "FRONTEND_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",") if origin.strip()],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=128)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


class RAGRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=10)


class ChatRequest(RAGRequest):
    conversation_id: int | None = None


class ConversationRequest(BaseModel):
    title: str = Field(default="New conversation", min_length=1, max_length=255)


def require_database() -> None:
    if not DATABASE_URL:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured.")


def db():
    require_database()
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


def validate_email(email: str) -> str:
    normalized = email.strip().casefold()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
        raise HTTPException(status_code=422, detail="Enter a valid email address.")
    return normalized


def validate_password(password: str) -> None:
    if len(password) < 8 or not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        raise HTTPException(
            status_code=422,
            detail="Password must be at least 8 characters and contain a letter and a number.",
        )


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_session(response: Response, user_id: int, secure: bool) -> None:
    token = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    with db() as connection, connection.cursor() as cursor:
        cursor.execute(
            "INSERT INTO auth_sessions (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
            (user_id, token_digest(token), expires_at),
        )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_DAYS * 86400,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def current_user(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)) -> dict:
    if not session:
        raise HTTPException(status_code=401, detail="Authentication required.")
    with db() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT u.user_id, u.full_name, u.email
            FROM auth_sessions s JOIN users u ON u.user_id = s.user_id
            WHERE s.token_hash = %s AND s.expires_at > CURRENT_TIMESTAMP
            """,
            (token_digest(session),),
        )
        user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Session expired. Please sign in again.")
    return user


def owned_conversation(cursor, conversation_id: int, user_id: int) -> dict:
    cursor.execute(
        "SELECT conversation_id, title FROM conversations WHERE conversation_id = %s AND user_id = %s",
        (conversation_id, user_id),
    )
    conversation = cursor.fetchone()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return conversation


@app.get("/")
def root():
    return {"project": "Explainable Vector Database Management Framework", "status": "running"}


@app.get("/health/live")
def liveness():
    return {"status": "alive"}


@app.get("/health/ready")
def readiness():
    require_database()
    started = time.perf_counter()
    try:
        with db() as connection:
            connection.execute("SELECT 1")
        return {"status": "ready", "database": "connected", "database_latency_ms": round((time.perf_counter() - started) * 1000, 2)}
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {type(exc).__name__}")


@app.get("/health")
def health_check():
    return readiness()


@app.post("/api/auth/register", status_code=201)
def register(request: RegisterRequest, response: Response, http_request: Request):
    email = validate_email(request.email)
    validate_password(request.password)
    if request.password != request.confirm_password:
        raise HTTPException(status_code=422, detail="Passwords do not match.")
    password_hash = bcrypt.hashpw(request.password.encode(), bcrypt.gensalt()).decode()
    try:
        with db() as connection, connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s) RETURNING user_id, full_name, email",
                (request.full_name.strip(), email, password_hash),
            )
            user = cursor.fetchone()
    except UniqueViolation:
        raise HTTPException(status_code=409, detail="An account with that email already exists.")
    issue_session(response, user["user_id"], http_request.url.scheme == "https")
    return {"user": user}


@app.post("/api/auth/login")
def login(request: LoginRequest, response: Response, http_request: Request):
    now = time.time()
    source = http_request.client.host if http_request.client else "unknown"
    recent = [attempt for attempt in LOGIN_ATTEMPTS.get(source, []) if now - attempt < 60]
    if len(recent) >= 10:
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again shortly.")
    LOGIN_ATTEMPTS[source] = recent
    email = validate_email(request.email)
    with db() as connection, connection.cursor() as cursor:
        cursor.execute("SELECT user_id, full_name, email, password_hash FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
    if not user or not bcrypt.checkpw(request.password.encode(), user["password_hash"].encode()):
        LOGIN_ATTEMPTS[source].append(now)
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    issue_session(response, user["user_id"], http_request.url.scheme == "https")
    return {"user": {key: user[key] for key in ("user_id", "full_name", "email")}}


@app.post("/api/auth/logout")
def logout(response: Response, session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    if session:
        with db() as connection, connection.cursor() as cursor:
            cursor.execute("DELETE FROM auth_sessions WHERE token_hash = %s", (token_digest(session),))
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@app.get("/api/auth/me")
def me(user: dict = Depends(current_user)):
    return {"user": user}


@app.get("/api/documents")
def list_documents(user: dict = Depends(current_user)):
    with db() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT d.document_id, d.title, d.file_name, d.file_type, d.created_at,
                   COUNT(DISTINCT c.chunk_id) AS chunk_count
            FROM documents d LEFT JOIN chunks c ON c.document_id = d.document_id
            WHERE d.user_id = %s
            GROUP BY d.document_id ORDER BY d.created_at DESC
            """,
            (user["user_id"],),
        )
        return {"documents": cursor.fetchall()}


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...), user: dict = Depends(current_user)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(status_code=415, detail="Only PDF, DOCX, and TXT files are supported.")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit.")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        result = DocumentIngestionService(DATABASE_URL).ingest_document(tmp_path, user["user_id"])
        return {"ok": True, "file_name": file.filename, "status": "indexed", "result": result}
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {type(exc).__name__}: {str(exc)[:250]}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.delete("/api/documents/{document_id}")
def delete_document(document_id: int, user: dict = Depends(current_user)):
    with db() as connection, connection.cursor() as cursor:
        cursor.execute("DELETE FROM documents WHERE document_id = %s AND user_id = %s RETURNING document_id", (document_id, user["user_id"]))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Document not found.")
    return {"ok": True}


@app.post("/api/search")
def semantic_search(request: SearchRequest, user: dict = Depends(current_user)):
    try:
        retrieval = RetrievalService(DATABASE_URL).search(request.query.strip(), request.top_k, user["user_id"])
        explanations = (
            ExplainabilityService(DATABASE_URL).explain_query(retrieval["query_id"])
            if retrieval["results"]
            else []
        )
        return {"retrieval": retrieval, "explanations": explanations}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Search failed: {type(exc).__name__}: {str(exc)[:250]}")


@app.post("/api/rag")
def answer_question(request: RAGRequest, user: dict = Depends(current_user)):
    try:
        return RAGService(DATABASE_URL).generate_answer(request.question.strip(), request.top_k, user["user_id"])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG request failed: {type(exc).__name__}: {str(exc)[:250]}")


@app.get("/api/history")
def query_history(limit: int = 20, user: dict = Depends(current_user)):
    limit = max(1, min(limit, 100))
    with db() as connection, connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT q.query_id, q.query_text, q.created_at,
                   COALESCE(rl.total_latency_ms, 0) AS retrieval_latency_ms,
                   ra.answer_id, ra.abstained, ra.grounding_status, ra.generation_latency_ms
            FROM queries q
            LEFT JOIN retrieval_logs rl ON rl.query_id = q.query_id
            LEFT JOIN rag_answers ra ON ra.query_id = q.query_id
            WHERE q.user_id = %s ORDER BY q.created_at DESC LIMIT %s
            """,
            (user["user_id"], limit),
        )
        return {"history": cursor.fetchall()}


@app.get("/api/conversations")
def list_conversations(user: dict = Depends(current_user)):
    with db() as connection, connection.cursor() as cursor:
        cursor.execute(
            "SELECT conversation_id, title, created_at, updated_at FROM conversations WHERE user_id = %s ORDER BY updated_at DESC",
            (user["user_id"],),
        )
        return {"conversations": cursor.fetchall()}


@app.post("/api/conversations", status_code=201)
def create_conversation(request: ConversationRequest | None = None, user: dict = Depends(current_user)):
    title = (request.title if request else "New conversation").strip() or "New conversation"
    with db() as connection, connection.cursor() as cursor:
        cursor.execute("INSERT INTO conversations (user_id, title) VALUES (%s, %s) RETURNING conversation_id, title, created_at, updated_at", (user["user_id"], title))
        return {"conversation": cursor.fetchone()}


@app.get("/api/conversations/{conversation_id}")
def get_conversation(conversation_id: int, user: dict = Depends(current_user)):
    with db() as connection, connection.cursor() as cursor:
        conversation = owned_conversation(cursor, conversation_id, user["user_id"])
        cursor.execute("SELECT message_id, role, content, metadata, created_at FROM messages WHERE conversation_id = %s AND user_id = %s ORDER BY created_at", (conversation_id, user["user_id"]))
        conversation["messages"] = cursor.fetchall()
        return {"conversation": conversation}


@app.patch("/api/conversations/{conversation_id}")
def rename_conversation(conversation_id: int, request: ConversationRequest, user: dict = Depends(current_user)):
    with db() as connection, connection.cursor() as cursor:
        owned_conversation(cursor, conversation_id, user["user_id"])
        cursor.execute("UPDATE conversations SET title = %s, updated_at = CURRENT_TIMESTAMP WHERE conversation_id = %s AND user_id = %s RETURNING conversation_id, title, updated_at", (request.title.strip(), conversation_id, user["user_id"]))
        return {"conversation": cursor.fetchone()}


@app.delete("/api/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, user: dict = Depends(current_user)):
    with db() as connection, connection.cursor() as cursor:
        owned_conversation(cursor, conversation_id, user["user_id"])
        cursor.execute("DELETE FROM conversations WHERE conversation_id = %s AND user_id = %s", (conversation_id, user["user_id"]))
    return {"ok": True}


@app.post("/api/chat")
def chat(request: ChatRequest, user: dict = Depends(current_user)):
    with db() as connection, connection.cursor() as cursor:
        if request.conversation_id is None:
            cursor.execute("INSERT INTO conversations (user_id, title) VALUES (%s, %s) RETURNING conversation_id", (user["user_id"], request.question[:80]))
            conversation_id = cursor.fetchone()["conversation_id"]
        else:
            owned_conversation(cursor, request.conversation_id, user["user_id"])
            conversation_id = request.conversation_id
        cursor.execute("INSERT INTO messages (conversation_id, user_id, role, content) VALUES (%s, %s, 'user', %s)", (conversation_id, user["user_id"], request.question.strip()))
    try:
        result = RAGService(DATABASE_URL).generate_answer(request.question.strip(), request.top_k, user["user_id"], conversation_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    metadata = {
        "sources": result.get("sources", []),
        "retrieval": result.get("retrieval", {}),
        "citation_validation": result.get("citation_validation"),
        "claim_verification": result.get("claim_verification"),
    }
    with db() as connection, connection.cursor() as cursor:
        cursor.execute("INSERT INTO messages (conversation_id, user_id, role, content, metadata) VALUES (%s, %s, 'assistant', %s, %s::jsonb)", (conversation_id, user["user_id"], result.get("answer", ""), Jsonb(metadata)))
        cursor.execute("UPDATE conversations SET updated_at = CURRENT_TIMESTAMP WHERE conversation_id = %s AND user_id = %s", (conversation_id, user["user_id"]))
    result["conversation_id"] = conversation_id
    return result
