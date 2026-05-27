# models.py
# Each class = one table in SQLite.
# SQLAlchemy turns these Python classes into SQL CREATE TABLE statements automatically.

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from database import Base


class Tenant(Base):
    """
    A tenant = one business using the platform.
    Multi-tenancy means every other table filters by tenant_id,
    so TenantA never sees TenantB's data.
    """
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    plan = Column(String, default="free")          # free / pro / enterprise
    created_at = Column(DateTime, server_default=func.now())


class User(Base):
    """
    Users belong to exactly one tenant.
    role: "admin" can manage docs, "agent" can only chat, "viewer" read-only.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="agent")         # admin | agent | viewer
    created_at = Column(DateTime, server_default=func.now())


class Memory(Base):
    """
    Long-term memory for each user.
    We store key facts the agent should remember across sessions.
    memory_type: "preference" | "fact" | "history"
    """
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)
    memory_type = Column(String, default="fact")
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class Lead(Base):
    """
    CRM leads — tenant-isolated.
    The CRM tool creates/reads these.
    """
    __tablename__ = "leads"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True)
    name = Column(String)
    email = Column(String)
    status = Column(String, default="new")         # new | contacted | converted
    notes = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())


class AgentTrace(Base):
    """
    Every agent run is logged here for observability.
    This is how we track latency, token usage, and failures.
    """
    __tablename__ = "agent_traces"
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)
    query = Column(Text)
    plan = Column(Text)
    retrieved_docs = Column(Integer, default=0)
    tool_calls = Column(JSON, default=[])          # list of tool names used
    final_answer = Column(Text)
    eval_scores = Column(JSON, default={})         # faithfulness, latency, etc
    tokens_used = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    
