# AI Assistant — Psychoeducation Chatbot

> A clinically-aware conversational AI for psychoeducation about depression, built for the Colombian context.

![Python](https://img.shields.io/badge/Python-3.14%2B-blue?logo=python)
![LangGraph](https://img.shields.io/badge/LangGraph-0.4%2B-purple)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi)
![React](https://img.shields.io/badge/React-TypeScript-61DAFB?logo=react)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What is this?

This project is a full-stack AI chatbot that combines **clinical knowledge**, **crisis detection**, and **long-term memory** to provide psychoeducational support about depression. It is not a therapy replacement — it is an educational tool designed to inform, guide, and safely escalate when needed.

Key capabilities:
- **Clinical assessments** (PHQ-9 and ASQ) on first login, used to adapt all subsequent responses
- **Crisis detection** with an empathic de-escalation agent that has access to emergency resources
- **RAG over curated collections** — clinical knowledge, CBT techniques, pseudoscience debunking, emergency resources
- **Persistent memory** — remembers past sessions and builds a clinical profile per user
- **Hallucination evaluation** — automatically regenerates responses that are unfaithful to retrieved documents
- **PDF ingestion** — upload your own documents into any collection

---

## Architecture

The core is a **LangGraph `StateGraph`** compiled at startup. Every user message flows through 8 nodes:

```
START → load_user_context → crisis_detector
          ├─[crisis]──→ crisis_agent ⟲ crisis_tool_executor   (ReAct mini-loop)
          │                  └─[done]→ memory_updater → END
          └─[no crisis]→ agent_reasoner ⟲ tool_executor       (ReAct loop)
                            └─[done]→ hallucination_evaluator
                                        ├─[faithful / no docs]→ memory_updater → END
                                        └─[not faithful, regen<2]→ agent_reasoner
```

| Node | Role |
|------|------|
| `load_user_context` | Reads long-term profile + session summaries from PostgreSQL store |
| `crisis_detector` | Fast LLM classification — routes crisis vs. normal path |
| `crisis_agent` | Empathic ReAct agent with restricted access to `emergencia` collection only |
| `crisis_tool_executor` | Executes emergency RAG tool calls, loops back to `crisis_agent` |
| `agent_reasoner` | Main reasoning LLM — decides whether to use RAG tools or respond directly |
| `tool_executor` | Executes RAG tool calls, accumulates retrieved documents |
| `hallucination_evaluator` | Verifies response faithfulness; injects feedback for regeneration |
| `memory_updater` | Extracts session metadata, merges into short-term + long-term memory |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Orchestration** | LangGraph 0.4 + LangChain Core |
| **LLM Providers** | Ollama (local/cloud), Groq, Google Gemini |
| **Backend API** | FastAPI + FastAPI-Users (JWT auth) |
| **Database** | PostgreSQL 17 (users + graph checkpointing) |
| **Vector Store** | ChromaDB (embeddings via `gemini-embedding-2-preview`) |
| **PDF Ingestion** | Docling + Gemini for image captioning |
| **Frontend** | React 18 + TypeScript + Vite |
| **Package Manager** | `uv` (Python) / npm (frontend) |
| **Deployment** | Docker Compose (isolated `app_net` network) |

### RAG Collections

| Collection | Contents |
|-----------|----------|
| `clinico` | Clinical knowledge about depression |
| `tecnicas_tcc` | CBT techniques and psychoeducation |
| `pseudociencia` | Pseudoscience debunking |
| `emergencia` | Crisis resources (hotlines, emergency services) |

---

## Quick Start

### With Docker (recommended)

```bash
# 1. Clone the repo
git clone https://github.com/DanielPantoja08/AI_assistant.git
cd AI_assistant

# 2. Copy and fill in environment variables
cp .env.example .env
# Edit .env — see Configuration section below

# 3. Build and start all services
docker compose build
docker compose up
```

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:3000/api/docs *(proxied through nginx)*

> The API is internal-only — only the frontend port (`3000`) is publicly exposed.

Migrations run automatically on startup via `docker-entrypoint.sh`.

#### Ollama Cloud models (optional, one-time setup)

```bash
# After docker compose up, authenticate once:
docker exec -it <project>-ollama-1 ollama signin
# Opens OAuth in browser — session persists in a named volume across restarts
```

Models are selected via `.env` as usual: `LG_AGENT_MODEL=gemma4:31b-cloud`.

---

### Local Development

Requirements: Python 3.14+, `uv`, Node.js, a running PostgreSQL instance, Ollama (optional for local LLM).

```bash
# Backend
uv sync
docker compose up -d          # starts PostgreSQL only
uv run alembic upgrade head   # run migrations (first time)
uv run logic-graph-api        # API on http://localhost:8000

# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env          # set VITE_API_URL=http://localhost:8000
npm run dev                   # http://localhost:5173

# Optional: MCP RAG server
uv run logic-graph-mcp
```

---

## Configuration

Copy `.env.example` to `.env` and fill in the required values:

```env
# --- Required ---
LG_DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
LG_JWT_SECRET=your-secret-key

# --- Google Gemini (embeddings + PDF ingestion) ---
LG_GOOGLE_API_KEY=your-google-api-key

# --- Groq (crisis detector, hallucination evaluator, memory) ---
LG_GROQ_API_KEY=your-groq-api-key

# --- ChromaDB ---
LG_CHROMA_DB_PATH=./chroma_db          # use absolute path inside Docker: /app/chroma_db

# --- Ollama (local dev default; overridden to http://ollama:11434 in Docker Compose) ---
LG_OLLAMA_BASE_URL=http://localhost:11434

# --- Optional: override any node's LLM ---
LG_AGENT_PROVIDER=ollama
LG_AGENT_MODEL=gemma4:e4b
LG_CRISIS_DETECTOR_PROVIDER=groq
LG_CRISIS_DETECTOR_MODEL=meta-llama/llama-4-scout-17b-16e-instruct
```

**Default LLM configuration:**

| Node | Provider | Model |
|------|---------|-------|
| `agent_reasoner` | ollama | gemma4:e4b |
| `crisis_detector` | groq | llama-4-scout-17b-16e-instruct |
| `crisis_agent` | ollama | gemma4:e4b |
| `hallucination_evaluator` | groq | llama-4-scout-17b-16e-instruct |
| `memory_summarizer` | groq | llama-4-scout-17b-16e-instruct |

Any node can be overridden via `LG_<NODE>_PROVIDER` / `LG_<NODE>_MODEL` env vars.

---

## API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/auth/register` | — | Register a new user |
| `POST` | `/auth/jwt/login` | — | Login, returns JWT |
| `GET` | `/users/me` | JWT | Current user info |
| `POST` | `/chat` | JWT | Send a message, returns streamed response |
| `POST` | `/chat/end-session` | JWT | Finalize session, save long-term summary |
| `POST` | `/ingest/pdf` | JWT | Upload a PDF for ingestion into a collection |

Interactive docs available at `/docs` (Swagger) and `/redoc`.

---

## Project Structure

```
.
├── src/logic_graph/
│   ├── app.py               # Graph compilation (build_graph)
│   ├── state.py             # GraphState TypedDict
│   ├── config.py            # Settings (pydantic-settings)
│   ├── llm_factory.py       # Multi-provider LLM factory
│   ├── nodes/               # One file per graph node
│   ├── routing/             # Conditional edge functions
│   ├── memory/              # Short-term + long-term memory
│   ├── ingest/              # PDF ingestion + ChromaDB clients
│   ├── tools/               # LangChain RAG tools
│   ├── api/                 # FastAPI app + routers
│   ├── auth/                # FastAPI-Users models + manager
│   ├── db/                  # SQLAlchemy engine + base
│   └── mcp_rag/             # FastMCP server (same RAG tools)
├── frontend/                # React + TypeScript (Vite)
├── tests/                   # Pytest suite
├── alembic/                 # DB migrations
├── Dockerfile
├── docker-compose.yml
└── docker-entrypoint.sh
```

---

## Testing

```bash
# Unit tests (no database required)
uv run pytest tests/ -m "not integration"

# Integration tests (requires running PostgreSQL)
uv run pytest tests/ -m integration

# Single file
uv run pytest tests/test_routing.py -v
```

The test suite mocks LLMs at the node module level. Both `agent_reasoner` and `crisis_agent` use `lru_cache` — tests clear the cache with a per-file autouse fixture.

---

## Memory System

Each user gets two persistent memory namespaces in PostgreSQL:

- **`(user_id, "profile")`** — `ClinicalProfile`: distress level, recurring themes, preferred techniques, comorbidities
- **`(user_id, "sessions")`** — timestamped `SessionSummary` entries built at session end

Short-term memory accumulates topics, techniques, and `crisis_activated` flag across turns within a single session. The `session_finalizer` (called on `POST /chat/end-session`) generates a narrative summary and updates the clinical profile with a weighted-average distress score.

---

## Clinical Assessments

On first login, users complete:

- **PHQ-9** — Patient Health Questionnaire for depression severity
- **ASQ** — Ask Suicide-Screening Questions

Results are stored scoped to the user ID and surfaced to the crisis detector and agents as additional context for every subsequent interaction.

---

## License

MIT — see [LICENSE](LICENSE) for details.
