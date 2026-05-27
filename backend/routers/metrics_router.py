from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from auth import get_current_user
from models import User, AgentTrace, Lead, Memory

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/dashboard")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    traces = db.query(AgentTrace).filter(AgentTrace.tenant_id == user.tenant_id).all()
    
    total_queries = len(traces)
    avg_latency = round(sum(t.latency_ms for t in traces) / max(total_queries, 1), 1)
    total_tokens = sum(t.tokens_used for t in traces)
    lead_count = db.query(Lead).filter(Lead.tenant_id == user.tenant_id).count()
    memory_count = db.query(Memory).filter(Memory.tenant_id == user.tenant_id).count()
    
    recent = traces[-10:]
    recent_data = [{
        "query": t.query[:80],
        "latency_ms": t.latency_ms,
        "tokens": t.tokens_used,
        "tools": t.tool_calls,
        "eval": t.eval_scores,
        "created_at": t.created_at.isoformat() if t.created_at else ""
    } for t in reversed(recent)]
    
    return {
        "total_queries": total_queries,
        "avg_latency_ms": avg_latency,
        "total_tokens": total_tokens,
        "lead_count": lead_count,
        "memory_count": memory_count,
        "recent_traces": recent_data
    }


@router.get("/leads")
def get_leads(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    leads = db.query(Lead).filter(Lead.tenant_id == user.tenant_id).all()
    return [{"id": l.id, "name": l.name, "email": l.email, "status": l.status, "notes": l.notes} for l in leads]


@router.post("/leads")
def create_lead(payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    lead = Lead(tenant_id=user.tenant_id, name=payload.get("name",""), email=payload.get("email",""), notes=payload.get("notes",""))
    db.add(lead)
    db.commit()
    return {"message": "Lead created", "id": lead.id}


@router.post("/memory")
def add_memory(payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from memory.memory_store import save_long_term
    save_long_term(db, user.tenant_id, user.id, payload.get("content",""), payload.get("type","fact"))
    return {"message": "Memory saved"}

from models import ScheduledTask

@router.get("/tasks")
def get_tasks(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tasks = db.query(ScheduledTask).filter(ScheduledTask.tenant_id == user.tenant_id).order_by(ScheduledTask.created_at.desc()).all()
    return [{"id": t.id, "title": t.title, "description": t.description, "status": t.status, "scheduled_for": t.scheduled_for, "created_at": t.created_at.isoformat() if t.created_at else ""} for t in tasks]

@router.post("/tasks")
def create_task(payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = ScheduledTask(
        tenant_id=user.tenant_id,
        user_id=user.id,
        title=payload.get("title", ""),
        description=payload.get("description", ""),
        scheduled_for=payload.get("scheduled_for", ""),
        status="pending"
    )
    db.add(task)
    db.commit()
    return {"message": "Task created", "id": task.id}

@router.patch("/tasks/{task_id}")
def update_task_status(task_id: int, payload: dict, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    task = db.query(ScheduledTask).filter(ScheduledTask.id == task_id, ScheduledTask.tenant_id == user.tenant_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.status = payload.get("status", task.status)
    db.commit()
    return {"message": "Updated"}