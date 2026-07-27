# =============================================================================
# PaperMind AI — RAG Query API Routes
# =============================================================================

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from papermind.agents.workflows.rag_workflow import PaperMindRAGWorkflow

router = APIRouter()


class RAGQueryRequest(BaseModel):
    query: str = Field(..., description="Natural language question")
    filter_doc_ids: list[str] | None = Field(default=None)


class RAGQueryResponse(BaseModel):
    query: str
    answer: str
    confidence_score: float
    citations: list[dict[str, Any]]
    chunks_retrieved: int


@router.post("", response_model=RAGQueryResponse)
@router.post("/", response_model=RAGQueryResponse)
async def query_rag_agent(request: RAGQueryRequest) -> RAGQueryResponse:
    """Execute the multi-step agentic RAG workflow to generate grounded answers with citations."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query string cannot be empty.")

    workflow = PaperMindRAGWorkflow()
    result = await workflow.run(
        query=request.query,
        filter_doc_ids=request.filter_doc_ids,
    )

    return RAGQueryResponse(
        query=request.query,
        answer=result.get("answer", ""),
        confidence_score=result.get("confidence_score", 0.0),
        citations=result.get("citations", []),
        chunks_retrieved=len(result.get("retrieved_chunks", [])),
    )


class PeerReviewRequest(BaseModel):
    doc_id: str


@router.post("/peer-review")
@router.post("/peer-review/")
async def evaluate_peer_review(request: PeerReviewRequest) -> dict[str, Any]:
    """Execute the Autonomous Peer Review Agent to evaluate a research manuscript."""
    from papermind.api.routes.documents import fetch_document_entity
    from papermind.agents.specialized.peer_review_agent import PeerReviewAgent
    from papermind.services.llm.factory import create_llm_provider

    doc = await fetch_document_entity(request.doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document '{request.doc_id}' not found.")

    llm = create_llm_provider()
    agent = PeerReviewAgent(llm)
    report = await agent.evaluate_document(doc)
    return report
