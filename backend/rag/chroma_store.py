# chroma_store.py
# ChromaDB stores document embeddings and lets us search by meaning (semantic search).
# We add BM25 (keyword search) on top — combining both is "hybrid retrieval".
# Hybrid = catches exact keyword matches AND conceptually similar text.

import chromadb
from chromadb.config import Settings
from rank_bm25 import BM25Okapi
from typing import List, Dict, Any, Optional
import re

# Runs entirely in-memory/local — no external service needed.
# persist_directory saves to disk so data survives restarts.
_client = None


def get_chroma_client():
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path="./chroma_data",
            settings=Settings(anonymized_telemetry=False)
        )
    return _client


def _collection_name(tenant_id: int) -> str:
    """
    Each tenant gets their own ChromaDB collection.
    This is the core of tenant isolation for documents —
    TenantA's collection never touches TenantB's.
    """
    return f"tenant_{tenant_id}_docs"


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
    """
    Split a long document into overlapping chunks.
    Why overlap? So sentences that span a chunk boundary don't lose context.
    chunk_size=400 tokens ≈ ~300 words — good for most LLM context windows.
    """
    # Split by sentences first (rough split)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks = []
    current = []
    current_len = 0

    for sentence in sentences:
        words = sentence.split()
        if current_len + len(words) > chunk_size:
            if current:
                chunks.append(" ".join(current))
            # Overlap: keep last `overlap` words for next chunk
            current = current[-overlap:] + words
            current_len = len(current)
        else:
            current.extend(words)
            current_len += len(words)

    if current:
        chunks.append(" ".join(current))

    return chunks if chunks else [text]


def add_documents(tenant_id: int, documents: List[str], metadatas: List[Dict] = None, source: str = "upload"):
    """
    Takes raw text documents, chunks them, embeds them, stores in ChromaDB.
    metadatas: optional extra info per doc (filename, date, etc.)
    """
    from rag.embedder import embed_texts

    collection = get_chroma_client().get_or_create_collection(
        name=_collection_name(tenant_id),
        metadata={"hnsw:space": "cosine"}  # cosine similarity for embeddings
    )

    all_chunks = []
    all_metas = []
    all_ids = []

    for i, doc in enumerate(documents):
        chunks = chunk_text(doc)
        for j, chunk in enumerate(chunks):
            chunk_id = f"doc_{i}_chunk_{j}_{hash(chunk) % 100000}"
            meta = (metadatas[i] if metadatas else {}) or {}
            meta["source"] = source
            meta["chunk_index"] = j
            all_chunks.append(chunk)
            all_metas.append(meta)
            all_ids.append(chunk_id)

    if not all_chunks:
        return

    embeddings = embed_texts(all_chunks)
    collection.add(
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metas,
        ids=all_ids
    )


def hybrid_search(tenant_id: int, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Hybrid retrieval = Semantic search (ChromaDB) + Keyword search (BM25).
    
    Why hybrid?
    - Semantic search finds "heart attack" when query says "myocardial infarction"
    - BM25 finds exact matches like product codes or names that embeddings might miss
    - Combining both gives better coverage
    
    We merge results by rank (Reciprocal Rank Fusion).
    """
    from rag.embedder import embed_query

    collection = get_chroma_client().get_or_create_collection(
        name=_collection_name(tenant_id)
    )

    total_docs = collection.count()
    if total_docs == 0:
        return []

    fetch_k = min(top_k * 3, total_docs)

    # --- Semantic search ---
    query_embedding = embed_query(query)
    semantic_results = collection.query(
        query_embeddings=[query_embedding],
        n_results=fetch_k,
        include=["documents", "metadatas", "distances"]
    )

    semantic_docs = semantic_results["documents"][0]
    semantic_metas = semantic_results["metadatas"][0]
    semantic_scores = semantic_results["distances"][0]

    # --- BM25 keyword search ---
    # Get all docs in the collection for BM25 corpus
    all_data = collection.get(include=["documents"])
    all_docs = all_data["documents"]

    tokenized_corpus = [doc.lower().split() for doc in all_docs]
    bm25 = BM25Okapi(tokenized_corpus)
    bm25_scores = bm25.get_scores(query.lower().split())

    # Get top BM25 indices
    top_bm25_idx = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:fetch_k]
    bm25_docs = [all_docs[i] for i in top_bm25_idx]

    # --- Reciprocal Rank Fusion (RRF) ---
    # RRF: score = sum(1 / (rank + 60)) for each list the doc appears in.
    # k=60 is standard — it dampens the effect of very high ranks.
    rrf_scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict] = {}

    for rank, (doc, meta, dist) in enumerate(zip(semantic_docs, semantic_metas, semantic_scores)):
        key = doc[:100]  # use first 100 chars as dedup key
        rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (rank + 60)
        doc_map[key] = {"content": doc, "metadata": meta, "semantic_score": 1 - dist}

    for rank, doc in enumerate(bm25_docs):
        key = doc[:100]
        rrf_scores[key] = rrf_scores.get(key, 0) + 1 / (rank + 60)
        if key not in doc_map:
            doc_map[key] = {"content": doc, "metadata": {}, "semantic_score": 0}

    # Sort by combined RRF score
    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    results = []
    for key, rrf_score in ranked:
        entry = doc_map[key].copy()
        entry["rrf_score"] = rrf_score
        results.append(entry)

    return results


def rerank(query: str, results: List[Dict]) -> List[Dict]:
    """
    Simple cross-encoder-style reranking using word overlap.
    In production you'd use a cross-encoder model, but this is free and good enough.
    Scores each result by how many query words appear in it (normalized).
    """
    query_words = set(query.lower().split())
    for result in results:
        content_words = set(result["content"].lower().split())
        overlap = len(query_words & content_words)
        result["rerank_score"] = overlap / (len(query_words) + 1)

    return sorted(results, key=lambda x: x["rerank_score"], reverse=True)
