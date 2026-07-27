# =============================================================================
# PaperMind AI — Retrieval Agent
# =============================================================================
# Performs dense vector retrieval, formats context for downstream LLM nodes.
# Shared by most specialist agents as the first data-fetch step.
# =============================================================================

from __future__ import annotations

from typing import Any

from papermind.agents.state import AgentState
from papermind.agents.tools.retrieval_tools import RetrievalTools
from papermind.core.logging.logger import get_logger

log = get_logger(__name__)


class RetrievalAgent:
    """
    Retrieves top-k relevant chunks from the vector store and populates
    state["retrieved_chunks"] and state["formatted_context"].
    """

    def __init__(self, retrieval_tools: RetrievalTools, top_k: int = 3) -> None:
        self.tools = retrieval_tools
        self.top_k = top_k

    def __call__(self, state: AgentState) -> dict[str, Any]:
        query = state.get("query", "")
        filter_doc_ids = state.get("filter_doc_ids")

        hits = self.tools.search_vector_store(
            query=query,
            top_k=self.top_k,
            filter_doc_ids=filter_doc_ids,
        )

        chunks = [h.chunk for h in hits]
        formatted = self.tools.format_context(hits)

        path = state.get("agent_path", [])
        path = path + ["retrieval"]

        log.info("Retrieval agent complete", chunks=len(chunks))
        return {
            "retrieved_chunks": chunks,
            "formatted_context": formatted,
            "agent_path": path,
        }
