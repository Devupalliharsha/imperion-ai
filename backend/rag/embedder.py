# embedder.py
# On Render free tier, we can't load sentence-transformers (too heavy).
# Instead we use a simple TF-IDF-style hash embedding that works offline,
# requires zero downloads, and is good enough for demo RAG retrieval.
# For production: swap this with OpenAI/Groq embeddings API.

import hashlib
import math
from typing import List

DIMS = 384  # same dimension as MiniLM so ChromaDB config stays the same


def _hash_embed(text: str) -> List[float]:
    """
    Deterministic pseudo-embedding: splits text into trigrams,
    hashes each, accumulates into a fixed-size float vector.
    Similar meaning = similar frequent words = similar vector.
    Not as good as a real model but works for demo purposes.
    """
    vec = [0.0] * DIMS
    words = text.lower().split()
    tokens = []
    for w in words:
        tokens.append(w)
        for i in range(len(w) - 2):
            tokens.append(w[i:i+3])

    for token in tokens:
        h = int(hashlib.md5(token.encode()).hexdigest(), 16)
        idx = h % DIMS
        vec[idx] += 1.0

    # L2 normalize
    norm = math.sqrt(sum(x*x for x in vec)) or 1.0
    return [x / norm for x in vec]


def embed_texts(texts: List[str]) -> List[List[float]]:
    return [_hash_embed(t) for t in texts]


def embed_query(query: str) -> List[float]:
    return _hash_embed(query)