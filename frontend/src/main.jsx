import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ChevronDown, FileText, LogOut, Menu, MessageSquarePlus, Paperclip,
  Send, ShieldCheck, Trash2, UploadCloud, X, LockKeyhole, Network,
  Sparkles, CheckCircle2, Gauge, Search, Database, History, BarChart3,
  RefreshCw, Moon, Sun, CircleAlert, Server
} from "lucide-react";
import "./styles.css";
import { AsciiOcean } from "./ascii-ocean/AsciiOcean";

const browserApi = `${window.location.protocol}//${window.location.hostname}:8000`;
const API = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL || browserApi;
const API_FALLBACK = API.includes("localhost")
  ? API.replace("localhost", "127.0.0.1")
  : API.includes("127.0.0.1")
    ? API.replace("127.0.0.1", "localhost")
    : null;

async function api(path, options = {}) {
  let response;
  for (const baseUrl of [API, API_FALLBACK].filter(Boolean)) {
    try {
      response = await fetch(`${baseUrl}${path}`, { credentials: "include", ...options });
      break;
    } catch {
    }
  }
  if (!response) {
    throw new Error(`Could not reach the API at ${API}. Start the backend on port 8000 and refresh the page.`);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || `Request failed (${response.status})`);
  return data;
}

function App() {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  useEffect(() => {
    api("/api/auth/me").then(data => setUser(data.user)).catch(() => {}).finally(() => setAuthLoading(false));
  }, []);
  if (authLoading) return <div className="loading-screen">Loading your private workspace…</div>;
  return user ? <Workspace user={user} onLogout={() => setUser(null)} /> : <Auth onAuthenticated={setUser} />;
}

function Auth({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ full_name: "", email: "", password: "", confirm_password: "" });
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async event => {
    event.preventDefault(); setError(""); setBusy(true);
    try {
      const data = await api(`/api/auth/${mode}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(form) });
      onAuthenticated(data.user);
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  };
  const isLogin = mode === "login";
  return <main className="auth-shell">
    <section className="auth-brand-panel">
      <AsciiOcean className="auth-ocean" />
      <div className="auth-brand-content">
        <div className="auth-brand-mark"><ShieldCheck size={20} /></div>
        <div className="auth-brand-name">Explainable <span>RAG</span></div>
        <div className="auth-brand-kicker">PRIVATE KNOWLEDGE INTELLIGENCE</div>
        <h1>Your knowledge.<br /><span>Connected.</span></h1>
        <p className="auth-description">Transform your documents into an intelligent, searchable knowledge base. Ask questions, discover relevant information, and understand why every answer was generated.</p>
        <div className="auth-features">
          <Feature icon={LockKeyhole} title="Private Knowledge Base">Your documents and conversations stay within your account.</Feature>
          <Feature icon={Network} title="Explainable Retrieval">Understand which documents support every answer.</Feature>
          <Feature icon={Sparkles} title="Grounded AI Responses">Get answers backed by relevant document evidence.</Feature>
        </div>
      </div>
      <div className="auth-graph" aria-hidden="true"><GraphIllustration /></div>
      <div className="auth-brand-footer"><span><span className="pulse-dot" /> Evidence-first intelligence</span><span>Explainable RAG · 2026</span></div>
    </section>
    <section className="auth-form-panel"><div className="auth-form-wrap" key={mode}>
      <div className="mobile-brand"><div className="auth-brand-mark"><ShieldCheck size={19} /></div><strong>Explainable <span>RAG</span></strong></div>
      <div className="auth-form-heading"><span className="auth-form-kicker">{isLogin ? "WELCOME BACK" : "GET STARTED"}</span><h2>{isLogin ? "Welcome back" : "Create your workspace"}</h2><p>{isLogin ? "Sign in to continue to your private knowledge assistant." : "Start building your private AI-powered knowledge base."}</p></div>
      {error && <div className="notice error"><X size={15} />{error}</div>}
      <form className="auth-form" onSubmit={submit}>{!isLogin && <label>Full name<div className="input-wrap"><input required value={form.full_name} onChange={field(setForm, "full_name")} placeholder="Your name" /></div></label>}
        <label>Email address<div className="input-wrap"><input required type="email" value={form.email} onChange={field(setForm, "email")} placeholder="you@company.com" /></div></label>
        <label>Password<div className="input-wrap"><input required type="password" value={form.password} onChange={field(setForm, "password")} placeholder="Enter your password" /></div></label>
        {!isLogin && <label>Confirm password<div className="input-wrap"><input required type="password" value={form.confirm_password} onChange={field(setForm, "confirm_password")} placeholder="Repeat your password" /></div></label>}
        <button className="primary full auth-submit" disabled={busy}>{busy ? "Please wait…" : isLogin ? "Sign in to workspace" : "Create private workspace"}<span>→</span></button>
      </form>
      <div className="auth-privacy"><CheckCircle2 size={14} /> {isLogin ? "Your documents and conversations are private to your account." : "Your knowledge base is private and accessible only through your account."}</div>
      <div className="auth-switch"><span>{isLogin ? "New to Explainable RAG?" : "Already have an account?"}</span><button type="button" className="link-button" onClick={() => { setMode(isLogin ? "register" : "login"); setError(""); }}>{isLogin ? "Create an account" : "Sign in instead"}</button></div>
    </div></section>
  </main>;
}

const field = (setForm, name) => event => setForm(form => ({ ...form, [name]: event.target.value }));

function Feature({ icon: Icon, title, children }) {
  return <div className="auth-feature"><div className="feature-icon"><Icon size={16} /></div><div><strong>{title}</strong><p>{children}</p></div></div>;
}

function GraphIllustration() {
  return <svg viewBox="0 0 640 230" role="img" aria-label="Documents connected through retrieval to grounded answers">
    <defs><linearGradient id="graph-line" x1="0" x2="1"><stop stopColor="#4f75f2" stopOpacity=".08" /><stop offset=".5" stopColor="#7887f7" stopOpacity=".7" /><stop offset="1" stopColor="#4f75f2" stopOpacity=".1" /></linearGradient><filter id="node-glow"><feGaussianBlur stdDeviation="3" result="blur" /><feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge></filter></defs>
    <g fill="none" stroke="url(#graph-line)" strokeWidth="1"><path d="M75 91L220 52L326 112L450 63L570 110" /><path d="M75 151L220 52M75 91L220 178L326 112M220 178L450 63M326 112L450 170L570 110" /><path d="M220 52L450 170M220 178L450 63" /></g>
    <g fill="#111827" stroke="#4f75f2" strokeWidth="1.5"><rect x="44" y="77" width="62" height="43" rx="7" /><rect x="44" y="137" width="62" height="43" rx="7" /><rect x="540" y="89" width="62" height="43" rx="7" /></g>
    <g fill="#7887f7" filter="url(#node-glow)"><circle cx="220" cy="52" r="4" /><circle cx="326" cy="112" r="5" /><circle cx="450" cy="63" r="4" /><circle cx="220" cy="178" r="3" /><circle cx="450" cy="170" r="3" /></g>
    <g fill="none" stroke="#9eafff" strokeWidth="1.5" opacity=".8"><path d="M60 91h28M60 151h28M557 103h28v18h-28z" /><path d="M557 103l14 9-14 9" /></g>
    <g fill="#8f9ab0" fontSize="9" fontFamily="DM Mono, monospace" letterSpacing="1"><text x="43" y="68">SOURCE</text><text x="281" y="99">EMBEDDINGS</text><text x="535" y="80">ANSWER</text></g>
  </svg>;
}

function Workspace({ user, onLogout }) {
  const [tab, setTab] = useState("overview");
  const [theme, setTheme] = useState(() => localStorage.getItem("explainable-rag-theme") || "light");
  const [conversations, setConversations] = useState([]);
  const [active, setActive] = useState(null);
  const [messages, setMessages] = useState([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [sidebar, setSidebar] = useState(true);
  const [documents, setDocuments] = useState([]);
  const [showLibrary, setShowLibrary] = useState(false);
  const fileRef = useRef(null);
  useEffect(() => { document.documentElement.dataset.theme = theme; localStorage.setItem("explainable-rag-theme", theme); }, [theme]);
  useEffect(() => { loadConversations(); loadDocuments(); }, []);
  async function loadConversations() { try { setConversations((await api("/api/conversations")).conversations || []); } catch (e) { setNotice(e.message); } }
  async function loadDocuments() { try { setDocuments((await api("/api/documents")).documents || []); } catch (e) { setNotice(e.message); } }
  async function selectConversation(id) {
    try { const data = await api(`/api/conversations/${id}`); setActive(data.conversation); setMessages(data.conversation.messages || []); setNotice(""); } catch (e) { setNotice(e.message); }
  }
  async function newChat() { setActive(null); setMessages([]); setDraft(""); setNotice(""); }
  async function send() {
    const question = draft.trim(); if (!question || busy) return;
    setBusy(true); setDraft(""); setMessages(items => [...items, { role: "user", content: question }]);
    try {
      const data = await api("/api/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question, conversation_id: active?.conversation_id || null, top_k: 5 }) });
      setActive(current => ({ ...(current || {}), conversation_id: data.conversation_id }));
      setMessages(items => [...items, { role: "assistant", content: data.answer, metadata: { ...data } }]);
      await loadConversations();
    } catch (e) {
      setMessages(items => items.slice(0, -1));
      if (e.message === "Authentication required." || e.message.includes("Session expired")) {
        setNotice("Your session has expired. Please sign in again.");
        onLogout();
      } else {
        setNotice(e.message);
      }
    } finally { setBusy(false); }
  }
  async function upload(event) {
    const file = event.target.files?.[0]; if (!file) return;
    setNotice(`Indexing ${file.name}…`);
    const body = new FormData(); body.append("file", file);
    try { const data = await api("/api/documents/upload", { method: "POST", body }); setNotice(`${data.file_name} was indexed successfully.`); await loadDocuments(); }
    catch (e) { setNotice(e.message); } finally { event.target.value = ""; }
  }
  async function removeConversation(id) {
    if (!window.confirm("Delete this conversation? Documents will not be deleted.")) return;
    try { await api(`/api/conversations/${id}`, { method: "DELETE" }); if (active?.conversation_id === id) newChat(); await loadConversations(); } catch (e) { setNotice(e.message); }
  }
  async function removeDocument(id) {
    if (!window.confirm("Delete this document and its indexed chunks?")) return;
    try { await api(`/api/documents/${id}`, { method: "DELETE" }); setNotice("Document deleted."); await loadDocuments(); }
    catch (e) { setNotice(e.message); }
  }
  async function logout() { await api("/api/auth/logout", { method: "POST" }).catch(() => {}); onLogout(); }
  const navigate = next => { setTab(next); if (next !== "documents") setShowLibrary(false); };
  return <div className={`workspace dashboard-shell ${tab === "overview" ? "is-overview" : ""}`}>
    <aside className={`sidebar ${sidebar ? "" : "collapsed"}`}>
      <div className="brand"><div className="brand-icon"><Database size={19} /></div>{sidebar && <div><strong>Explainable RAG</strong><small>Vector Database<br />Management</small></div>}<button className="icon-button menu-button" onClick={() => setSidebar(!sidebar)}><Menu size={18} /></button></div>
      {sidebar && <><div className="sidebar-label workspace-label">WORKSPACE</div>{[["overview","Overview",Gauge],["documents","Documents",FileText]].map(([id,label,Icon]) => <button key={id} className={`nav-item ${tab === id ? "active" : ""}`} onClick={() => navigate(id)}><Icon size={16} />{label}</button>)}<div className="sidebar-label workspace-label conversation-label">RECENT CONVERSATIONS</div><div className="conversation-list">{conversations.slice(0, 4).map(conversation => <div className={`conversation ${active?.conversation_id === conversation.conversation_id && tab === "overview" ? "selected" : ""}`} key={conversation.conversation_id}><button onClick={() => { selectConversation(conversation.conversation_id); navigate("overview"); }}><MessageSquarePlus size={14} />{conversation.title}</button><button className="delete-chat" onClick={() => removeConversation(conversation.conversation_id)} title="Delete conversation"><Trash2 size={13} /></button></div>)}</div></>}
      <div className="profile">{sidebar && <><div className="avatar">{user.full_name.slice(0, 1).toUpperCase()}</div><div><strong>{user.full_name}</strong><small>{user.email}</small></div><button className="icon-button" title="Log out" onClick={logout}><LogOut size={15} /></button></>}</div>
    </aside>
    <main className="main-content"><header className="topbar"><div><span className="eyebrow">DATABASE INTELLIGENCE</span><h1>{tab === "overview" ? active?.title || "Overview" : "Documents"}</h1><p>{tab === "overview" ? "Ask questions and explore grounded answers from your private knowledge base." : "Manage your private source material and indexed chunks."}</p></div><div className="top-actions"><span className="environment">Development</span><button className="icon-button top-control" onClick={() => { loadDocuments(); loadConversations(); }} title="Refresh"><RefreshCw size={16} /></button><span className="api-status connected"><span className="status-dot connected" /> Online</span><button className="theme-toggle" onClick={() => setTheme(theme === "light" ? "dark" : "light")} aria-label="Toggle theme">{theme === "light" ? <Moon size={17} /> : <Sun size={17} />}</button></div></header>
      {notice && <div className="notice inline">{notice}<button onClick={() => setNotice("")}><X size={14} /></button></div>}
      {tab === "overview" && <OverviewDashboard documents={documents} conversations={conversations} messages={messages} draft={draft} setDraft={setDraft} send={send} busy={busy} upload={() => fileRef.current?.click()} />}
      {tab === "documents" && <LibraryPanel documents={documents} removeDocument={removeDocument} upload={() => fileRef.current?.click()} />}
      <input ref={fileRef} hidden type="file" accept=".pdf,.docx,.txt" onChange={upload} />
    </main>
  </div>;
}

function OverviewDashboard({ documents, conversations, messages, draft, setDraft, send, busy, upload }) {
  const totalChunks = documents.reduce((sum, doc) => sum + (Number(doc.chunk_count) || 0), 0);
  return <div className="dashboard-body"><section className={`pond-hero ${messages.length ? "pond-has-messages" : ""}`}><AsciiOcean className="pond-canvas" /><div className="pond-grid" /><div className="pond-content"><span className="pond-kicker">EXPLAINABLE RAG · DIGITAL POND</span>{messages.length > 0 && <div className="pond-chat-sequence">{messages.map((message, index) => <Message key={`${message.message_id || index}`} message={message} />)}{busy && <div className="pond-thinking">Thinking<span>.</span><span>.</span><span>.</span></div>}</div>}<form className="pond-ask" onSubmit={event => { event.preventDefault(); send(); }}><textarea value={draft} onChange={event => setDraft(event.target.value)} onKeyDown={event => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder="Start typing — they’ll make room..." rows={1} /><button type="button" onClick={upload} title="Upload document"><UploadCloud size={17} /></button><button type="submit" disabled={busy || !draft.trim()} title="Send question"><Send size={20} /></button><div className="pond-hint"><span>↵</span> send <span>⌘K</span> focus</div></form></div></section><div className="metric-grid"><Metric label="Total documents" value={documents.length} /><Metric label="Indexed chunks" value={totalChunks || "N/A"} /><Metric label="Conversations" value={conversations.length || "N/A"} /><Metric label="Workspace status" value="Ready" /></div><div className="dashboard-panels"><section className="panel"><div className="section-heading"><h2>Quick actions</h2></div><div className="quick-actions"><button onClick={upload}><UploadCloud size={18} /><span><b>Upload document</b><small>Add PDF, DOCX, or TXT source</small></span></button><button onClick={() => document.querySelector(".pond-ask textarea")?.focus()}><Search size={18} /><span><b>Ask a question</b><small>Continue your grounded conversation</small></span></button></div></section><section className="panel"><div className="section-heading"><h2>Workspace status</h2></div><div className="status-card"><CheckCircle2 size={18} /><div><strong>Private workspace ready</strong><small>Your documents and conversations are scoped to your account.</small></div></div></section></div></div>;
}

function Metric({ label, value }) { return <div className="metric-card"><span>{label}</span><b>{value}</b></div>; }

function ChatPanel({ messages, draft, setDraft, send, busy, upload }) {
  return <section className="chat-panel"><div className="chat-panel-head"><span className="eyebrow">GROUNDED QUESTION ANSWERING</span><h2>Ask your knowledge base</h2><p>Retrieve evidence, generate an answer, and inspect how it was grounded.</p></div><div className="chat-panel-messages">{!messages.length && <div className="chat-empty"><ShieldCheck size={26} /><p>Ask a question about your private documents.</p></div>}{messages.map((message, index) => <Message key={`${message.message_id || index}`} message={message} />)}{busy && <div className="typing">Thinking<span>.</span><span>.</span><span>.</span></div>}</div><form className="composer dashboard-composer" onSubmit={event => { event.preventDefault(); send(); }}><button type="button" className="icon-button" onClick={upload}><Paperclip size={19} /></button><textarea value={draft} onChange={event => setDraft(event.target.value)} onKeyDown={event => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); send(); } }} placeholder="Ask a question about your documents…" rows={1} /><button className="send-button" disabled={busy || !draft.trim()}><Send size={17} /></button></form></section>;
}

function LibraryPanel({ documents, removeDocument }) {
  return <div className="library-panel"><div className="welcome-icon"><FileText size={23} /></div><h1>Your documents</h1><p>Only documents uploaded to your account appear here.</p>{documents.length ? documents.map(doc => <div className="library-row" key={doc.document_id}><FileText size={17} /><div><strong>{doc.file_name}</strong><small>{String(doc.file_type || "").toUpperCase()} · {doc.chunk_count ?? 0} indexed chunks</small></div><button className="icon-button" title="Delete document" onClick={() => removeDocument(doc.document_id)}><Trash2 size={15} /></button></div>) : <div className="empty-library">No documents uploaded yet.</div>}</div>;
}

function Message({ message }) {
  const [expanded, setExpanded] = useState(message.role === "assistant");
  const meta = message.metadata || {};
  const sources = meta.sources || [];
  return <article className={`message ${message.role}`}><div className="message-avatar">{message.role === "assistant" ? <ShieldCheck size={16} /> : "You"}</div><div className="message-body"><div className="message-role">{message.role === "assistant" ? "Explainable RAG" : "You"}</div><div className="message-content">{message.content}</div>{message.role === "assistant" && <details open={expanded} onToggle={event => setExpanded(event.currentTarget.open)}><summary>How was this answer generated? <ChevronDown size={14} /></summary><div className="evidence">{sources.length ? sources.map(source => <div className="source" key={source.citation_label}><strong>[{source.citation_label}] {source.file_name}</strong><span>Rank {source.rank} · Similarity {Number(source.similarity_score).toFixed(3)} · Chunk {source.chunk_id}</span></div>) : <span>No source evidence returned.</span>}{meta.retrieval?.total_latency_ms && <small>Retrieval latency: {Number(meta.retrieval.total_latency_ms).toFixed(0)} ms</small>}</div></details>}</div></article>;
}

createRoot(document.getElementById("root")).render(<App />);
