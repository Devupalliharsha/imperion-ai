import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from database import engine, Base
import models  # registers all tables

# Create all SQLite tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Imperion AI Platform", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routers
from routers.auth_router import router as auth_router
from routers.agent_router import router as agent_router
from routers.docs_router import router as docs_router
from routers.metrics_router import router as metrics_router

app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(docs_router)
app.include_router(metrics_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "Imperion AI Platform"}


# Serve frontend
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))
