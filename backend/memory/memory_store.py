# memory_store.py
# Two types of memory, mirroring how humans work:
#
# SHORT-TERM: The current conversation. Stored in a Python dict (RAM).
#   Lost when server restarts. Used to give the LLM conversation context.
#   Think: "what did the user say 3 messages ago?"
#
# LONG-TERM: Facts about the user across all sessions. Stored in SQLite.
#   "User prefers formal tone", "User is in SaaS industry", etc.
#   The agent reads these at the start of every conversation.

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from models import Memory


# Short-term: { "user_id_session": [{"role": "user", "content": "..."}, ...] }
_session_memory: Dict[str, List[Dict]] = {}
MAX_HISTORY = 10  # keep last 10 messages to avoid token overflow


def get_session_history(user_id: int, session_id: str) -> List[Dict]:
    """Returns the conversation history for this user's current session."""
    key = f"{user_id}_{session_id}"
    return _session_memory.get(key, [])


def add_to_session(user_id: int, session_id: str, role: str, content: str):
    """Appends a message to session history, trimming if too long."""
    key = f"{user_id}_{session_id}"
    if key not in _session_memory:
        _session_memory[key] = []
    _session_memory[key].append({"role": role, "content": content})
    # Keep only the last MAX_HISTORY messages
    if len(_session_memory[key]) > MAX_HISTORY:
        _session_memory[key] = _session_memory[key][-MAX_HISTORY:]


def clear_session(user_id: int, session_id: str):
    key = f"{user_id}_{session_id}"
    _session_memory.pop(key, None)


def save_long_term(db: Session, tenant_id: int, user_id: int, content: str, memory_type: str = "fact"):
    """Save an important fact to long-term memory in SQLite."""
    mem = Memory(
        tenant_id=tenant_id,
        user_id=user_id,
        memory_type=memory_type,
        content=content
    )
    db.add(mem)
    db.commit()


def get_long_term(db: Session, tenant_id: int, user_id: int, limit: int = 10) -> List[str]:
    """
    Load the user's long-term memories.
    We inject these into the system prompt so the agent 'remembers' the user.
    """
    memories = (
        db.query(Memory)
        .filter(Memory.tenant_id == tenant_id, Memory.user_id == user_id)
        .order_by(Memory.created_at.desc())
        .limit(limit)
        .all()
    )
    return [m.content for m in memories]


def build_memory_context(db: Session, tenant_id: int, user_id: int) -> str:
    """
    Returns a formatted string of long-term memories to inject into the system prompt.
    """
    memories = get_long_term(db, tenant_id, user_id)
    if not memories:
        return ""
    lines = "\n".join(f"- {m}" for m in memories)
    return f"\n\n[Long-term memory about this user]\n{lines}"
