from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from auth import require_role
from models import User
from rag.chroma_store import add_documents

router = APIRouter(prefix="/docs", tags=["docs"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(require_role("admin", "agent")),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith((".txt", ".md", ".csv")):
        raise HTTPException(status_code=400, detail="Only .txt, .md, .csv files supported")
    
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    
    if len(text.strip()) < 10:
        raise HTTPException(status_code=400, detail="File is empty or too short")
    
    add_documents(
        tenant_id=user.tenant_id,
        documents=[text],
        metadatas=[{"filename": file.filename, "uploaded_by": user.username}],
        source=file.filename
    )
    
    return {"message": f"'{file.filename}' uploaded and indexed successfully"}


@router.post("/add-text")
async def add_text(
    payload: dict,
    user: User = Depends(require_role("admin", "agent")),
    db: Session = Depends(get_db)
):
    text = payload.get("text", "").strip()
    source = payload.get("source", "manual-entry")
    if len(text) < 10:
        raise HTTPException(status_code=400, detail="Text too short")
    
    add_documents(tenant_id=user.tenant_id, documents=[text], source=source)
    return {"message": "Text indexed successfully"}
