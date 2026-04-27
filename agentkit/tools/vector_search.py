from __future__ import annotations

import os

from langchain_core.tools import tool

from agentkit.guardrails.middleware import wrap_tool_call


@tool
@wrap_tool_call()
def vector_search(query: str, top_k: int = 5) -> str:
    """Search the vector store for chunks semantically similar to the query.

    Returns top_k results with their text and metadata.
    """
    from qdrant_client import QdrantClient
    from langchain_openai import OpenAIEmbeddings

    client = QdrantClient(url=os.getenv("QDRANT_URL", "http://localhost:6333"))
    collection = os.getenv("QDRANT_COLLECTION", "agentkit_docs")
    embedder = OpenAIEmbeddings(model="text-embedding-3-small")

    vector = embedder.embed_query(query)
    results = client.search(
        collection_name=collection,
        query_vector=vector,
        limit=top_k,
        with_payload=True,
    )

    if not results:
        return "(no results found)"

    lines: list[str] = []
    for i, hit in enumerate(results, 1):
        payload = hit.payload or {}
        text = payload.get("text", "(no text)")
        source = payload.get("source", "unknown")
        score = round(hit.score, 3)
        lines.append(f"[chunk:{i}] score={score} source={source}\n{text}")

    return "\n\n".join(lines)
