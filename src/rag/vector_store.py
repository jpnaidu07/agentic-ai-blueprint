"""
Local Vector Store & Semantic Retrieval Engine.
Provides lightweight cosine similarity and semantic search over Dell Runbooks and incident logs.
"""

import math
import re
from typing import List, Dict, Any
from src.rag.knowledge_base import DELL_RUNBOOKS

def _tokenize(text: str) -> List[str]:
    return re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())

def _term_frequency(tokens: List[str]) -> Dict[str, float]:
    freq: Dict[str, float] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0.0) + 1.0
    total = float(len(tokens)) or 1.0
    return {k: v / total for k, v in freq.items()}

def _cosine_similarity(vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
    intersection = set(vec1.keys()) & set(vec2.keys())
    if not intersection:
        return 0.0
    dot_product = sum(vec1[k] * vec2[k] for k in intersection)
    norm1 = math.sqrt(sum(v * v for v in vec1.values()))
    norm2 = math.sqrt(sum(v * v for v in vec2.values()))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot_product / (norm1 * norm2)

class LocalVectorStore:
    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self._seed_documents()

    def _seed_documents(self):
        for doc in DELL_RUNBOOKS:
            tokens = _tokenize(f"{doc['title']} {doc['category']} {' '.join(doc['tags'])} {doc['content']}")
            self.documents.append({
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "tags": doc["tags"],
                "tf_vector": _term_frequency(tokens)
            })

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        query_tokens = _tokenize(query)
        query_vector = _term_frequency(query_tokens)

        scored: List[tuple[float, Dict[str, Any]]] = []
        for doc in self.documents:
            score = _cosine_similarity(query_vector, doc["tf_vector"])
            # Keyword tag boost
            for tag in doc["tags"]:
                if tag.lower() in query.lower():
                    score += 0.25
            scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, doc in scored[:top_k]:
            results.append({
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "similarity_score": round(score, 3)
            })
        return results

_vector_store_instance = LocalVectorStore()

def get_vector_store() -> LocalVectorStore:
    return _vector_store_instance
