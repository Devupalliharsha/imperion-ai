from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import get_db
from models import User, Tenant
from auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    username: str
    password: str
    tenant_name: str
    role: str = "agent"


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    tenant = db.query(Tenant).filter(Tenant.name == req.tenant_name).first()
    if not tenant:
        tenant = Tenant(name=req.tenant_name)
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
    
    user = User(
        tenant_id=tenant.id,
        username=req.username,
        hashed_password=hash_password(req.password),
        role=req.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "Registered successfully", "tenant_id": tenant.id, "user_id": user.id}


@router.post("/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user.username, "tenant_id": user.tenant_id, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role, "tenant_id": user.tenant_id}
