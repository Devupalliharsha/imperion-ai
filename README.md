# Imperion AI Platform

Multi-tenant AI platform built for the Imperion Data Systems assessment.
Stack: FastAPI + SQLite + Groq + ChromaDB + React (all free).

---

## What's inside

```
backend/
  main.py           → FastAPI app, starts the server
  database.py       → SQLite connection
  models.py         → DB tables (Users, Tenants, Memory, Leads, Traces)
  auth.py           → JWT login + role-based access
  agents/
    supervisor.py   → The 4-stage pipeline (Planner→Retriever→Executor→Critic)
  rag/
    chroma_store.py → ChromaDB vector store + hybrid search + reranking
    embedder.py     → Local sentence-transformer embeddings (free, offline)
  memory/
    memory_store.py → Short-term (RAM) + long-term (SQLite) memory
  tools/
    tool_registry.py→ 4 tools: web_search, crm_lookup, send_email, calendar_check
  evaluation/
    evaluator.py    → Scores faithfulness, hallucination risk, latency, cost
  routers/
    auth_router.py  → POST /auth/register, POST /auth/login
    agent_router.py → POST /agent/chat
    docs_router.py  → POST /docs/upload, POST /docs/add-text
    metrics_router.py→ GET /metrics/dashboard, leads, memory
frontend/
  index.html        → Complete React UI served by FastAPI
```

---

## Step 1 — Get your free Groq API key

1. Go to https://console.groq.com
2. Sign up (free, no card needed)
3. Click "API Keys" → "Create API Key"
4. Copy it — you'll need it in Step 3

---

## Step 2 — Clone and install

```bash
git clone <your-repo>
cd imperion-ai

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

The first install takes 2-3 minutes. `sentence-transformers` downloads the embedding model (~90MB) on first run.

---

## Step 3 — Set environment variables

```bash
cp .env.example .env
```

Open `.env` and set:

```
GROQ_API_KEY=gsk_your_actual_key_here
SECRET_KEY=any-long-random-string-here
```

The `SECRET_KEY` can be anything — it's used to sign JWTs. Make it long and random.

---

## Step 4 — Run the server

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You'll see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Open http://localhost:8000 in your browser. You should see the login screen.

---

## Step 5 — First use walkthrough

**Register:**
- Click "Register"
- Username: anything (e.g. `admin`)
- Password: anything
- Company name: your tenant name (e.g. `acme-corp`)
- Role: `admin`
- Click "Create Account"

**Login** with the same credentials.

**Upload a document:**
- Click "Documents" in the sidebar
- Upload any `.txt` file (try a company FAQ, a product description, anything)
- Or paste text directly in the text box

**Chat:**
- Click "Chat"
- Ask something from your document — the agent will retrieve it
- Try: `search the web for latest AI news` — uses the real DuckDuckGo tool
- Try: `check my calendar for today` — uses the calendar tool
- Add a lead in CRM tab, then ask: `look up the lead named John`

**Metrics:**
- Click "Metrics" to see every agent run traced with latency, tokens, hallucination score

---

## How the agent pipeline works (simple version)

Every chat message goes through 4 stages:

1. **Planner** — asks the LLM: "what steps do we need? do we need to search docs? use a tool?"
2. **Retriever** — if docs are needed, searches ChromaDB using hybrid (semantic + keyword) search
3. **Executor** — runs the tool if needed, then calls Groq LLM with all context to generate the answer
4. **Critic** — asks a second LLM call: "is this answer good quality?" — adds a warning if not

The final answer, all scores, and tool calls are saved to SQLite as a trace.

---

## Multi-tenancy explained

Every user belongs to a `tenant_id`. Every query filters by `tenant_id`:
- ChromaDB: each tenant has its own collection (`tenant_1_docs`, `tenant_2_docs`)
- SQLite: all queries include `.filter(tenant_id == user.tenant_id)`
- JWT tokens carry the `tenant_id` so it can't be spoofed

Register with two different company names and the data never crosses.

---

## API reference (for your demo video)

All routes require `Authorization: Bearer <token>` except register and login.

| Method | Route | What it does |
|--------|-------|-------------|
| POST | /auth/register | Create user + tenant |
| POST | /auth/login | Returns JWT token |
| POST | /agent/chat | Main chat endpoint |
| POST | /docs/upload | Upload file to RAG |
| POST | /docs/add-text | Add raw text to RAG |
| GET | /metrics/dashboard | Traces + stats |
| GET | /metrics/leads | CRM leads |
| POST | /metrics/leads | Add a lead |
| POST | /metrics/memory | Save long-term memory |
| GET | /health | Health check |
| GET | /docs | FastAPI auto-docs (Swagger) |

Visit http://localhost:8000/docs to see and test every route interactively.

---

## Deploy to Render (free)

1. Push your code to GitHub:
   ```bash
   git init && git add . && git commit -m "init"
   gh repo create imperion-ai --public && git push
   ```

2. Go to https://render.com → "New Web Service"

3. Connect your GitHub repo

4. Render detects `render.yaml` automatically

5. Add environment variable: `GROQ_API_KEY` = your key

6. Click Deploy. Free tier URL: `https://imperion-ai.onrender.com`

**Note:** Free tier sleeps after 15 min inactivity. First request after sleep takes ~30 seconds (cold start). This is normal for free tier.

---

## Troubleshooting

**`ModuleNotFoundError`** — make sure you ran `pip install -r requirements.txt` inside the venv

**`GROQ_API_KEY not set`** — check your `.env` file is in the project root and you ran `cp .env.example .env`

**ChromaDB errors on first run** — normal, it creates `./chroma_data/` folder automatically

**`sqlite3.OperationalError`** — delete `imperion.db` and restart, it'll be recreated

**Frontend not loading** — make sure you're accessing `http://localhost:8000`, not `http://localhost:3000`

---

## What covers each rubric criterion

| Criterion | Where |
|-----------|-------|
| Multi-tenant architecture | `models.py` tenant_id on all tables, `chroma_store.py` per-tenant collections |
| Agent orchestration (4 stages) | `agents/supervisor.py` |
| RAG quality | `rag/chroma_store.py` hybrid_search + rerank |
| Memory | `memory/memory_store.py` short-term + long-term |
| Evaluation layer | `evaluation/evaluator.py` + `AgentTrace` model |
| Tool calling (4 tools) | `tools/tool_registry.py` |
| JWT + RBAC | `auth.py` + `require_role()` decorator |
| Observability | `AgentTrace` saved per run, `/metrics/dashboard` |
| Frontend/dashboard | `frontend/index.html` |
| Docker (optional) | See below |

### Optional Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t imperion-ai .
docker run -p 8000:8000 --env-file .env imperion-ai
```
