# tool_registry.py
# Tools are functions the agent can call to do real things.
# Each tool has a name, description (used in the LLM prompt), and an execute() method.
#
# Real tools: DuckDuckGo search (actually works, free, no API key)
# Mock tools: Email, CRM, Calendar — they return realistic fake responses
#             so you can demo without SMTP/OAuth setup. Easy to make real later.

import httpx
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from models import Lead


# ─── Tool definitions ──────────────────────────────────────────────────────────

async def tool_web_search(query: str, **kwargs) -> Dict[str, Any]:
    """
    Real web search using DuckDuckGo's free instant answer API.
    No API key needed. Returns top abstract/answer if available.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_redirect": "1", "t": "imperion"}
            )
            data = resp.json()
            abstract = data.get("AbstractText") or data.get("Answer") or ""
            related = [r.get("Text", "") for r in data.get("RelatedTopics", [])[:3]]
            result_text = abstract or " | ".join(filter(None, related)) or "No results found."
            return {"tool": "web_search", "query": query, "result": result_text}
    except Exception as e:
        return {"tool": "web_search", "query": query, "result": f"Search failed: {str(e)}"}


async def tool_crm_lookup(name: str = None, email: str = None, db: Session = None, tenant_id: int = None, **kwargs) -> Dict[str, Any]:
    """
    Look up a lead in the CRM (our SQLite leads table).
    Real tool — actually queries the database.
    """
    if not db:
        return {"tool": "crm", "result": "DB not available"}

    query = db.query(Lead).filter(Lead.tenant_id == tenant_id)
    if name:
        query = query.filter(Lead.name.ilike(f"%{name}%"))
    if email:
        query = query.filter(Lead.email.ilike(f"%{email}%"))

    leads = query.limit(5).all()
    if not leads:
        return {"tool": "crm", "result": "No matching leads found"}

    results = [{"name": l.name, "email": l.email, "status": l.status, "notes": l.notes} for l in leads]
    return {"tool": "crm", "result": results}


async def tool_send_email(to: str, subject: str, body: str, **kwargs) -> Dict[str, Any]:
    """
    Mock email tool. In production: replace with smtplib or SendGrid.
    Returns success so the agent can continue its flow.
    """
    # To make this real: use smtplib.SMTP with env vars from .env
    print(f"[EMAIL MOCK] To: {to} | Subject: {subject} | Body: {body[:80]}")
    return {
        "tool": "email",
        "result": f"Email sent to {to} with subject '{subject}'",
        "status": "sent"
    }


async def tool_calendar_check(date: str = "today", **kwargs) -> Dict[str, Any]:
    """
    Mock calendar tool. Returns fake schedule data.
    Replace with Google Calendar API or Calendly API when ready.
    """
    mock_schedule = {
        "today": ["10:00 AM - Team standup", "2:00 PM - Client call", "4:00 PM - Review session"],
        "tomorrow": ["9:00 AM - Planning meeting", "3:00 PM - Demo with prospect"]
    }
    events = mock_schedule.get(date.lower(), ["No events found for that date"])
    return {"tool": "calendar", "date": date, "result": events}


# ─── Registry ──────────────────────────────────────────────────────────────────

TOOLS = {
    "web_search": {
        "fn": tool_web_search,
        "description": "Search the web for current information. Args: query (str)",
        "args": ["query"]
    },
    "crm_lookup": {
        "fn": tool_crm_lookup,
        "description": "Look up customer/lead records. Args: name (str) or email (str)",
        "args": ["name", "email"]
    },
    "send_email": {
        "fn": tool_send_email,
        "description": "Send an email. Args: to (email str), subject (str), body (str)",
        "args": ["to", "subject", "body"]
    },
    "calendar_check": {
        "fn": tool_calendar_check,
        "description": "Check calendar events. Args: date (str, e.g. 'today' or 'tomorrow')",
        "args": ["date"]
    }
}


def get_tools_description() -> str:
    """Returns a formatted list of tools to inject into the LLM prompt."""
    lines = []
    for name, info in TOOLS.items():
        lines.append(f"- {name}: {info['description']}")
    return "\n".join(lines)


async def execute_tool(tool_name: str, args: Dict, db: Session = None, tenant_id: int = None) -> Dict[str, Any]:
    """
    Calls the tool function with the given args.
    Injects db and tenant_id for tools that need them (like crm_lookup).
    """
    if tool_name not in TOOLS:
        return {"tool": tool_name, "result": f"Unknown tool: {tool_name}"}

    tool_fn = TOOLS[tool_name]["fn"]
    try:
        result = await tool_fn(db=db, tenant_id=tenant_id, **args)
        return result
    except Exception as e:
        return {"tool": tool_name, "result": f"Tool error: {str(e)}"}
