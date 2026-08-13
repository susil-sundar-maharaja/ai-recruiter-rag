"""
Retrieval Module
-----------------
Two jobs:
1. build_queries()            -> turns resume skills/tech + selected role into a few targeted search queries
2. retrieve_relevant_chunks() -> searches the FAISS index and returns only chunks tagged with the selected role

The vector store (index.faiss + chunks_metadata.json) must already exist in data/vectorstore/
— that's produced by the Colab ingestion notebook (Step 2) and downloaded here manually.
"""

import os
import json

import faiss
from sentence_transformers import SentenceTransformer

VECTORSTORE_DIR = os.path.join("data", "vectorstore")
INDEX_PATH = os.path.join(VECTORSTORE_DIR, "index.faiss")
METADATA_PATH = os.path.join(VECTORSTORE_DIR, "chunks_metadata.json")

# Loaded once and reused — loading the model/index on every call would be slow
_model = None
_index = None
_metadata = None


def _load():
    global _model, _index, _metadata
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    if _index is None:
        _index = faiss.read_index(INDEX_PATH)
    if _metadata is None:
        with open(METADATA_PATH, "r", encoding="utf-8") as f:
            _metadata = json.load(f)


def build_queries(resume_info: dict, role: str) -> list[str]:
    """Turn resume skills/tech + the selected role into a handful of targeted search queries."""
    queries = []
    top_skills = (resume_info.get("skills") or [])[:5]
    top_tech = (resume_info.get("technologies") or [])[:5]

    for skill in top_skills:
        queries.append(f"{role} interview questions about {skill}")
    for tech in top_tech:
        queries.append(f"{role} concepts related to {tech}")

    # Always include a general fallback query in case skills/tech lists are short
    queries.append(f"core {role} concepts and fundamentals")
    return queries


def retrieve_relevant_chunks(query: str, role: str, top_k: int = 5, search_multiplier: int = 6) -> list[dict]:
    """Searches the vector store for the query, but only keeps chunks tagged with the given role.

    FAISS itself has no concept of 'role' — it just returns the closest vectors overall.
    So we search wider than top_k (search_multiplier), then filter down to the role we want.
    """
    _load()
    query_embedding = _model.encode([query]).astype("float32")

    search_k = top_k * search_multiplier
    _distances, indices = _index.search(query_embedding, search_k)

    results = []
    for idx in indices[0]:
        if idx == -1:
            continue
        chunk = _metadata[idx]
        if chunk["role"] == role:
            results.append(chunk)
        if len(results) >= top_k:
            break

    return results
