# =============================================================================
# PaperMind AI — RAG Agent Workflow Unit Tests
# =============================================================================

from __future__ import annotations

import pytest

from papermind.agents.workflows.rag_workflow import PaperMindRAGWorkflow
from papermind.models.domain.document import ChunkType, SemanticChunk
from papermind.services.llm.base import BaseLLMProvider, LLMRequest, LLMResponse
from papermind.vectorstore.faiss.faiss_store import FAISSVectorStore


class MockLLMProvider(BaseLLMProvider):
    @property
    def provider_name(self) -> str:
        return "mock"

    @property
    def default_model(self) -> str:
        return "mock-model"

    @property
    def vision_model(self) -> str | None:
        return None

    async def complete(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            content="Based on [Source 1], attention mechanisms improve performance.",
            model="mock-model",
            provider="mock",
        )

    async def stream(self, request: LLMRequest):
        yield "Based on [Source 1]"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [[0.1] * 4 for _ in texts]


@pytest.mark.asyncio
async def test_rag_workflow_execution():
    # Setup mock vector store populated with sample chunk
    store = FAISSVectorStore(dimension=4)
    chunk = SemanticChunk(
        doc_id="doc123",
        chunk_type=ChunkType.TEXT,
        content="Attention mechanisms improve performance significantly.",
        page_number=1,
    )
    chunk.embedding = [1.0, 0.0, 0.0, 0.0]
    store.upsert_chunks([chunk])

    from papermind.agents.tools.retrieval_tools import RetrievalTools

    class MockEmbeddingService:
        def embed_query(self, query: str) -> list[float]:
            return [1.0, 0.0, 0.0, 0.0]

    tools = RetrievalTools(vector_store=store, embedding_service=MockEmbeddingService())
    workflow = PaperMindRAGWorkflow(llm_provider=MockLLMProvider(), retrieval_tools=tools)

    res = await workflow.run("What is attention mechanism?")

    assert "answer" in res
    assert len(res["retrieved_chunks"]) == 1
    assert res["citations"][0]["doc_id"] == "doc123"
