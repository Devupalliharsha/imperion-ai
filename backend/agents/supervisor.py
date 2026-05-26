import os, time, json, re
from groq import AsyncGroq
from typing import Dict, Any, List
from sqlalchemy.orm import Session

client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY", ""))
MODEL = "llama-3.1-8b-instant"


async def call_llm(messages: List[Dict], system: str = "", max_tokens: int = 512) -> tuple[str, int]:
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.extend(messages)
    resp = await client.chat.completions.create(model=MODEL, messages=msgs, max_tokens=max_tokens, temperature=0.3)
    content = resp.choices[0].message.content or ""
    tokens = resp.usage.total_tokens if resp.usage else 0
    return content, tokens


async def run_agent(
    query: str,
    tenant_id: int,
    user_id: int,
    session_id: str,
    db: Session
) -> Dict[str, Any]:
    start = time.time()
    total_tokens = 0
    tool_calls_made = []

    # Import here to avoid circular imports
    from memory.memory_store import get_session_history, add_to_session, build_memory_context
    from rag.chroma_store import hybrid_search, rerank
    from tools.tool_registry import get_tools_description, execute_tool, TOOLS

    history = get_session_history(user_id, session_id)
    memory_ctx = build_memory_context(db, tenant_id, user_id)

    # ── STAGE 1: PLANNER ──────────────────────────────────────────────────────
    # Decides what steps to take and whether any tools are needed.
    planner_system = f"""You are a planning agent for a specialized system. Given the user query, output a JSON plan.
CRITICAL RULES:
1. ALWAYS set "needs_retrieval": true if the query asks about specific lore, people, rules, or internal concepts.
2. Only use the "web_search" tool if the query is explicitly about current real-world events.

Output JSON format:
- "steps": list of 1-3 short steps
- "needs_retrieval": true/false
- "needs_tool": tool name or null (available: {list(TOOLS.keys())})
- "tool_args": dict of args, or null

Respond ONLY with valid JSON. No explanation.{memory_ctx}"""

    plan_text, t = await call_llm([{"role": "user", "content": query}], system=planner_system, max_tokens=256)
    total_tokens += t

    try:
        plan_text_clean = re.sub(r"```json|```", "", plan_text).strip()
        plan = json.loads(plan_text_clean)
    except Exception:
        plan = {"steps": ["Answer directly"], "needs_retrieval": False, "needs_tool": None, "tool_args": None}

    # ── STAGE 2: RETRIEVER ────────────────────────────────────────────────────
    # Only hits ChromaDB if the plan says we need to search documents.
    retrieved_docs = []
    rag_context = ""

    if plan.get("needs_retrieval"):
        raw_results = hybrid_search(tenant_id, query, top_k=5)
        retrieved_docs = rerank(query, raw_results)[:3]
        if retrieved_docs:
            rag_context = "\n\n[Retrieved context]\n" + "\n---\n".join(
                f"Source: {d.get('metadata', {}).get('source', 'document')}\n{d['content']}"
                for d in retrieved_docs
            )

    # ── STAGE 3: EXECUTOR ─────────────────────────────────────────────────────
    # Runs the tool if needed, then calls the LLM for a final answer.
    tool_result_text = ""

    if plan.get("needs_tool") and plan["needs_tool"] in TOOLS:
        tool_name = plan["needs_tool"]
        tool_args = plan.get("tool_args") or {}
        tool_result = await execute_tool(tool_name, tool_args, db=db, tenant_id=tenant_id)
        tool_calls_made.append(tool_name)
        tool_result_text = f"\n\n[Tool result: {tool_name}]\n{json.dumps(tool_result.get('result', ''), indent=2)}"

    # Build conversation with all context
    conversation = history + [{"role": "user", "content": query}]
    executor_system = f"""You are a helpful AI assistant for a business. Answer the user's question clearly and concisely.
Use the retrieved context and tool results if provided. Cite sources when using retrieved documents.
If you don't know something, say so honestly. Do not hallucinate.{memory_ctx}{rag_context}{tool_result_text}"""

    answer, t = await call_llm(conversation, system=executor_system, max_tokens=800)
    total_tokens += t

    # ── STAGE 4: CRITIC ───────────────────────────────────────────────────────
    # Validates the answer quality and flags issues.
    critic_system = """You are a quality validator. Check if the Answer accurately uses the Context to answer the Query.
Respond with JSON:
{"quality": "good"|"acceptable"|"poor", "issue": null or short issue description, "confidence": 0.0-1.0}
Respond ONLY with valid JSON."""

    critic_input = f"Query: {query}\nContext: {rag_context}\nAnswer: {answer[:500]}"
    critic_text, t = await call_llm([{"role": "user", "content": critic_input}], system=critic_system, max_tokens=128)
    total_tokens += t

    try:
        critic_text_clean = re.sub(r"```json|```", "", critic_text).strip()
        validation = json.loads(critic_text_clean)
    except Exception:
        validation = {"quality": "acceptable", "issue": None, "confidence": 0.8}

    # If critic says poor quality, add a disclaimer
    if validation.get("quality") == "poor":
        answer += f"\n\n⚠️ Note: {validation.get('issue', 'Answer quality may be limited.')}"

    latency_ms = (time.time() - start) * 1000
    add_to_session(user_id, session_id, "user", query)
    add_to_session(user_id, session_id, "assistant", answer)

    from evaluation.evaluator import evaluate_response
    eval_scores = evaluate_response(query, answer, retrieved_docs, latency_ms, total_tokens)

    return {
        "answer": answer,
        "plan": plan,
        "retrieved_docs": len(retrieved_docs),
        "tool_calls": tool_calls_made,
        "validation": validation,
        "eval_scores": eval_scores,
        "tokens_used": total_tokens,
        "latency_ms": latency_ms
    }