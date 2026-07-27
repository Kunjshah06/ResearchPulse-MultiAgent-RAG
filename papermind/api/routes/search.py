# =============================================================================
# PaperMind AI — Search API Routes
# =============================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from papermind.embeddings.embedding_service import EmbeddingService
from papermind.vectorstore.factory import get_vector_store

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(..., description="The user query string")
    top_k: int = Field(default=5, ge=1, le=50)
    filter_doc_ids: list[str] | None = Field(default=None)


class SearchHit(BaseModel):
    chunk_id: str
    doc_id: str
    chunk_type: str
    content: str
    page_number: int
    score: float


class SearchResponse(BaseModel):
    query: str
    total_hits: int
    hits: list[SearchHit]


@router.post("/", response_model=SearchResponse)
async def search_documents(request: SearchRequest) -> SearchResponse:
    """Perform dense vector similarity search across indexed document chunks."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    embedder = EmbeddingService()
    query_vec = embedder.embed_query(request.query)

    vector_store = get_vector_store()
    results = vector_store.search(
        query_vector=query_vec,
        top_k=request.top_k,
        filter_doc_ids=request.filter_doc_ids,
    )

    hits = [
        SearchHit(
            chunk_id=r.chunk.id,
            doc_id=r.chunk.doc_id,
            chunk_type=r.chunk.chunk_type.value,
            content=r.chunk.content,
            page_number=r.chunk.page_number,
            score=r.score,
        )
        for r in results
    ]

    return SearchResponse(query=request.query, total_hits=len(hits), hits=hits)
