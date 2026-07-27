# =============================================================================
# PaperMind AI — Table Agent
# =============================================================================

from __future__ import annotations

from typing import Any

from papermind.agents.state import AgentState
from papermind.agents.tools.retrieval_tools import RetrievalTools
from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import ChunkType
from papermind.services.llm.base import BaseLLMProvider, LLMMessage, LLMRequest

log = get_logger(__name__)

_SYSTEM = (
    "You are PaperMind AI, specialised in analysing tables from academic papers. "
    "Explain table data clearly: identify the metric, columns, best/worst values, "
    "trends, and what conclusions the table supports."
)

_TABLE_PROMPT = """\
The following table(s) were extracted from a research paper.

TABLE DATA:
{table_context}

USER QUESTION: {query}

Provide:
1. A plain-English description of what the table shows.
2. Key values and their significance.
3. Any trend, comparison, or conclusion this table supports.
4. Cite which table you are referencing (e.g. [Source 1]).

EXPLANATION:"""


class TableAgent:
    """Specialist agent for table explanation and data analysis."""

    def __init__(self, llm: BaseLLMProvider, retrieval_tools: RetrievalTools) -> None:
        self.llm = llm
        self.tools = retrieval_tools

    async def __call__(self, state: AgentState) -> dict[str, Any]:
        query = state.get("query", "")
        filter_doc_ids = state.get("filter_doc_ids")
        path = state.get("agent_path", []) + ["table"]

        # Re-retrieve specifically table chunks
        hits = self.tools.search_by_chunk_type(
            query=query,
            chunk_type=ChunkType.TABLE,
            top_k=3,
            filter_doc_ids=filter_doc_ids,
        )

        # Fall back to general context if no dedicated table chunks found
        if not hits:
            hits_general = self.tools.search_vector_store(query=query, top_k=5, filter_doc_ids=filter_doc_ids)
            table_context = self.tools.format_context(hits_general)
            chunks = [h.chunk for h in hits_general]
        else:
            table_context = self.tools.format_context(hits)
            chunks = [h.chunk for h in hits]

        if not table_context:
            return {"table_explanation": "No table context found.", "agent_path": path}

        prompt = _TABLE_PROMPT.format(table_context=table_context, query=query)
        messages = [
            LLMMessage(role="system", content=_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]

        try:
            resp = await self.llm.complete(LLMRequest(messages=messages, temperature=0.1, max_tokens=800))
            explanation = resp.content
            confidence = 0.88
        except Exception as e:
            log.warning("TableAgent LLM call failed", error=str(e))
            explanation = f"[Table context retrieved]\n\n{table_context[:600]}"
            confidence = 0.5

        log.info("Table agent complete")
        return {
            "table_explanation": explanation,
            "answer": explanation,
            "retrieved_chunks": chunks,
            "confidence_score": confidence,
            "agent_path": path,
        }
