from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import uuid

from database import get_db
from auth import get_current_user
from models import User, AgentTrace
from agents.supervisor import run_agent

router = APIRouter(prefix="/agent", tags=["agent"])


class ChatRequest(BaseModel):
    query: str
    session_id: str = None


@router.post("/chat")
async def chat(req: ChatRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    session_id = req.session_id or str(uuid.uuid4())
    
    result = await run_agent(
        query=req.query,
        tenant_id=user.tenant_id,
        user_id=user.id,
        session_id=session_id,
        db=db
    )
    
    # Save trace for observability
    trace = AgentTrace(
        tenant_id=user.tenant_id,
        user_id=user.id,
        query=req.query,
        plan=str(result.get("plan", {})),
        retrieved_docs=result.get("retrieved_docs", 0),
        tool_calls=result.get("tool_calls", []),
        final_answer=result.get("answer", ""),
        eval_scores=result.get("eval_scores", {}),
        tokens_used=result.get("tokens_used", 0),
        latency_ms=result.get("latency_ms", 0)
    )
    db.add(trace)
    db.commit()
    
    return {
        "answer": result["answer"],
        "session_id": session_id,
        "validation": result.get("validation"),
        "eval": result.get("eval_scores"),
        "tool_calls": result.get("tool_calls", [])
    }
