import time
from typing import Dict, Any, List

def evaluate_response(query: str, answer: str, retrieved_docs: List[Dict], latency_ms: float, tokens_used: int) -> Dict[str, Any]:
    query_words = set(query.lower().split())
    answer_words = set(answer.lower().split())
    
    # Faithfulness: how many answer words appear in retrieved docs
    all_doc_words = set()
    for doc in retrieved_docs:
        all_doc_words.update(doc.get("content", "").lower().split())
    
    grounded_words = answer_words & all_doc_words
    faithfulness = round(len(grounded_words) / (len(answer_words) + 1), 3)
    
    # Hallucination heuristic: low faithfulness + long answer = likely hallucination
    hallucination_risk = "low" if faithfulness > 0.3 or not retrieved_docs else "medium" if faithfulness > 0.1 else "high"
    
    # Retrieval quality: did we find anything?
    retrieval_quality = min(1.0, len(retrieved_docs) / 5.0)
    
    # Cost estimate (Groq free tier: $0 but let's track token usage)
    estimated_cost = round(tokens_used * 0.0000002, 6)
    
    return {
        "faithfulness": faithfulness,
        "hallucination_risk": hallucination_risk,
        "retrieval_quality": round(retrieval_quality, 3),
        "latency_ms": round(latency_ms, 1),
        "tokens_used": tokens_used,
        "estimated_cost_usd": estimated_cost,
        "docs_retrieved": len(retrieved_docs)
    }
