# =============================================================================
# PaperMind AI — Citation Agent
# =============================================================================

from __future__ import annotations

from typing import Any

from papermind.agents.state import AgentState
from papermind.agents.tools.retrieval_tools import RetrievalTools
from papermind.core.logging.logger import get_logger
from papermind.services.llm.base import BaseLLMProvider, LLMMessage, LLMRequest

log = get_logger(__name__)

_SYSTEM = (
    "You are PaperMind AI, specialised in academic citation and reference analysis. "
    "Identify, explain, and contextualise citations within research papers. "
    "For each citation, describe who is cited, why, and in what context."
)

_CITATION_PROMPT = """\
The following reference and citation information was extracted from a research paper:

CITATION / REFERENCE DATA:
{citation_context}

USER QUESTION: {query}

Provide:
1. List key references cited in this context.
2. For each: author(s), year, and what contribution they make.
3. Explain WHY these works are cited here and how they relate to the paper's methodology.
4. Note any important datasets, benchmarks, or baseline methods referenced.

CITATION ANALYSIS:"""


class CitationAgent:
    """Specialist agent for citation and reference analysis."""

    def __init__(self, llm: BaseLLMProvider, retrieval_tools: RetrievalTools) -> None:
        self.llm = llm
        self.tools = retrieval_tools

    async def __call__(self, state: AgentState) -> dict[str, Any]:
        query = state.get("query", "")
        filter_doc_ids = state.get("filter_doc_ids")
        path = state.get("agent_path", []) + ["citation"]

        # Augment query with citation-specific terms
        augmented_query = f"citations references bibliography {query}"
        hits = self.tools.search_vector_store(
            query=augmented_query,
            top_k=6,
            filter_doc_ids=filter_doc_ids,
        )

        citation_context = self.tools.format_context(hits)
        chunks = [h.chunk for h in hits]

        if not citation_context:
            return {"citation_analysis": [], "agent_path": path}

        prompt = _CITATION_PROMPT.format(citation_context=citation_context, query=query)
        messages = [
            LLMMessage(role="system", content=_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]

        try:
            resp = await self.llm.complete(LLMRequest(messages=messages, temperature=0.1, max_tokens=900))
            analysis_text = resp.content
            confidence = 0.83
        except Exception as e:
            log.warning("CitationAgent LLM call failed", error=str(e))
            analysis_text = f"[Citation context retrieved]\n\n{citation_context[:600]}"
            confidence = 0.5

        # Return structured + text form
        citation_analysis = [
            {
                "doc_id": c.doc_id,
                "page_number": c.page_number,
                "chunk_type": c.chunk_type.value,
                "snippet": c.content[:200],
            }
            for c in chunks
        ]

        log.info("Citation agent complete", sources=len(citation_analysis))
        return {
            "citation_analysis": citation_analysis,
            "answer": analysis_text,
            "retrieved_chunks": chunks,
            "confidence_score": confidence,
            "agent_path": path,
        }
