# embedder.py
# sentence-transformers runs a small neural network LOCALLY on your machine.
# It converts text into a list of numbers (a vector) that captures meaning.
# Similar meaning = similar numbers. That's how semantic search works.
# No API calls, no cost, runs offline.

from sentence_transformers import SentenceTransformer
from typing import List

# This model is 90MB and downloads once automatically.
# "all-MiniLM-L6-v2" is the sweet spot: fast, small, and good quality.
_model = None


def get_model() -> SentenceTransformer:
    """Lazy-load the model once, reuse forever."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Convert a list of strings to a list of embedding vectors.
    Returns: [[0.1, 0.3, ...], [0.2, 0.1, ...], ...]
    """
    model = get_model()
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


def embed_query(query: str) -> List[float]:
    """Embed a single query string."""
    return embed_texts([query])[0]
