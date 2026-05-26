<div align="center">

# IMPERION AI PLATFORM

### Multi-Tenant AI Agent Platform with RAG, Memory, Tool Calling & Evaluation

<p align="center">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/React-Frontend-20232A?style=for-the-badge&logo=react&logoColor=61DAFB"/>
  <img src="https://img.shields.io/badge/Groq-LLM-F55036?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/ChromaDB-VectorDB-6E44FF?style=for-the-badge"/>
  <img src="https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white"/>
  <img src="https://img.shields.io/badge/Render-Deploy-46E3B7?style=for-the-badge&logo=render&logoColor=black"/>
  <img src="https://img.shields.io/badge/JWT-Authentication-black?style=for-the-badge&logo=jsonwebtokens"/>
</p>

<p align="center">
Built for the <b>Imperion Data Systems AI Platform Assessment</b>
</p>

</div>

---

# Overview

Imperion AI Platform is a full-stack, multi-tenant AI orchestration system built using FastAPI, React, ChromaDB, and Groq.

The platform combines:

- Multi-agent orchestration
- Retrieval-Augmented Generation (RAG)
- Long-term memory
- Tool calling
- JWT authentication
- Multi-tenancy isolation
- AI evaluation & observability
- Real-time metrics dashboard

All built using free and open-source technologies.

---

# Core Features

## Multi-Agent AI Pipeline

Every user query passes through a structured 4-stage orchestration pipeline:

```text
User Query
    ↓
Planner
    ↓
Retriever (RAG)
    ↓
Executor (LLM + Tools)
    ↓
Critic (Validation Layer)
    ↓
Final Response
```

---

## Retrieval-Augmented Generation (RAG)

- ChromaDB vector database
- Hybrid semantic + keyword retrieval
- Local embeddings using sentence-transformers
- Tenant-specific document isolation
- Reranking pipeline for improved relevance

---

## Memory System

### Short-Term Memory
- Session-level memory
- Context-aware conversations

### Long-Term Memory
- SQLite persistence
- Tenant-aware storage
- Retrieval during future interactions

---

## Tool Calling System

Integrated tools include:

| Tool | Purpose |
|------|----------|
| `web_search` | Internet search |
| `crm_lookup` | CRM lead retrieval |
| `send_email` | Email simulation |
| `calendar_check` | Calendar availability |

---

## Authentication & RBAC

- JWT Authentication
- Role-Based Access Control
- Tenant-level data isolation
- Secure multi-user architecture

---

## Evaluation Layer

Every AI response is automatically scored for:

- Faithfulness
- Hallucination risk
- Latency
- Retrieval quality
- Estimated cost

All traces are persisted for observability.

---

# Tech Stack

| Layer | Technology |
|------|-------------|
| Backend | FastAPI |
| Frontend | React |
| Database | SQLite |
| Vector Store | ChromaDB |
| LLM Provider | Groq |
| Embeddings | sentence-transformers |
| Authentication | JWT |
| Deployment | Render |

---

# Project Structure

```text
imperion-ai/
│
├── backend/
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── auth.py
│   │
│   ├── agents/
│   │   └── supervisor.py
│   │
│   ├── rag/
│   │   ├── chroma_store.py
│   │   └── embedder.py
│   │
│   ├── memory/
│   │   └── memory_store.py
│   │
│   ├── tools/
│   │   └── tool_registry.py
│   │
│   ├── evaluation/
│   │   └── evaluator.py
│   │
│   └── routers/
│       ├── auth_router.py
│       ├── agent_router.py
│       ├── docs_router.py
│       └── metrics_router.py
│
├── frontend/
│   └── index.html
│
├── requirements.txt
├── render.yaml
├── .env.example
└── README.md
```

---

# System Architecture

## Agent Flow

| Stage | Responsibility |
|------|----------------|
| Planner | Breaks queries into actionable steps |
| Retriever | Retrieves relevant context from ChromaDB |
| Executor | Runs tools + generates LLM response |
| Critic | Evaluates answer quality |

---

# API Endpoints

## Authentication

| Method | Endpoint | Description |
|------|-----------|-------------|
| POST | `/auth/register` | Register user |
| POST | `/auth/login` | Login and receive JWT |

---

## Agent

| Method | Endpoint | Description |
|------|-----------|-------------|
| POST | `/agent/chat` | Main AI chat endpoint |

---

## Documents

| Method | Endpoint | Description |
|------|-----------|-------------|
| POST | `/docs/upload` | Upload documents |
| POST | `/docs/add-text` | Add raw text |

---

## Metrics

| Method | Endpoint | Description |
|------|-----------|-------------|
| GET | `/metrics/dashboard` | System metrics |
| GET | `/metrics/leads` | CRM leads |
| POST | `/metrics/leads` | Add lead |
| POST | `/metrics/memory` | Save memory |

---

# Local Development Setup

---

## 1. Clone Repository

```bash
git clone https://github.com/devupalliharsha/imperion-ai.git

cd imperion-ai
```

---

## 2. Create Virtual Environment

### Windows (PowerShell)

```powershell
python -m venv venv

.\venv\Scripts\Activate
```

### Mac/Linux

```bash
python -m venv venv

source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### Windows bcrypt Fix

```bash
pip install "bcrypt==3.2.2" --force-reinstall
```

> Required for resolving passlib/bcrypt compatibility issues on Windows.

---

## 4. Configure Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_long_random_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

---

## 5. Run the Server

```bash
cd backend

uvicorn main:app --host 127.0.0.1 --port 8000
```

Server starts at:

```text
http://127.0.0.1:8000
```

---

# First Use Walkthrough

---

## Register

Create a new account:

| Field | Example |
|------|----------|
| Username | `admin` |
| Password | `password123` |
| Company Name | `acme-corp` |
| Role | `admin` |

---

## Upload Documents

Navigate to:

```text
Documents → Upload
```

You can:

- Upload `.txt` files
- Paste raw text directly
- Embed documents into ChromaDB

---

## Chat with the Agent

Example prompts:

```text
Summarize the uploaded document
```

```text
Search the web for latest AI news
```

```text
Check my calendar for today
```

```text
Look up the lead named John
```

---

# Multi-Tenancy Architecture

Each user belongs to a `tenant_id`.

All systems are tenant-isolated:

| System | Isolation Strategy |
|------|--------------------|
| SQLite | tenant_id filtering |
| ChromaDB | Separate collections |
| JWT | tenant_id embedded in token |

Example:

```text
tenant_1_docs
tenant_2_docs
tenant_3_docs
```

No tenant data crosses boundaries.

---

# Render Deployment

---

## 1. Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

---

## 2. Create Render Web Service

Go to:

```text
https://render.com
```

Create:

```text
New → Web Service
```

Connect the repository:

```text
devupalliharsha/imperion-ai
```

---

## 3. Configure Render

### Build Command

```bash
pip install -r requirements.txt
```

### Start Command

```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## 4. Add Environment Variables

In Render dashboard:

| Key | Value |
|------|------|
| GROQ_API_KEY | your_api_key |
| SECRET_KEY | your_secret |
| ALGORITHM | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | 60 |

---

## 5. Deploy

Click:

```text
Create Web Service
```

Render automatically builds and deploys the platform.

---

# Observability & Metrics

Every AI interaction stores:

- Prompt
- Response
- Tool calls
- Latency
- Evaluation scores
- Hallucination risk
- Memory usage

Accessible via:

```text
/metrics/dashboard
```

---

# Troubleshooting

## bcrypt/passlib error

```bash
pip install "bcrypt==3.2.2" --force-reinstall
```

---

## GROQ_API_KEY not found

Ensure:

- `.env` exists
- Environment variables are configured on Render

---

## SQLite Operational Error

Delete:

```text
imperion.db
```

and restart the server.

---

## ChromaDB Initialization Error

Normal during first run.

The application automatically creates:

```text
/chroma_data
```

---

# Optional Docker Deployment

## Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Build & Run

```bash
docker build -t imperion-ai .

docker run -p 8000:8000 --env-file .env imperion-ai
```

---

# Rubric Coverage

| Criterion | Implementation |
|------|----------------|
| Multi-Tenant Architecture | tenant_id isolation |
| Agent Orchestration | agents/supervisor.py |
| RAG Pipeline | rag/chroma_store.py |
| Memory System | memory/memory_store.py |
| Evaluation Layer | evaluation/evaluator.py |
| Tool Calling | tools/tool_registry.py |
| JWT + RBAC | auth.py |
| Observability | AgentTrace + metrics |
| Frontend Dashboard | frontend/index.html |

---

# Future Improvements

- Streaming responses
- Redis caching
- PostgreSQL support
- Docker Compose
- Real email integrations
- WebSocket support
- Multi-model orchestration
- Advanced reranking
- Monitoring dashboard

---

# License

MIT License

---

<div align="center">

</div>
