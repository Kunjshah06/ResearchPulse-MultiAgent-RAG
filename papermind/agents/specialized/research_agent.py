# =============================================================================
# PaperMind AI — Research Agent
# =============================================================================
# Handles comparative analysis, novelty assessment, limitations, related work.
# =============================================================================

from __future__ import annotations

from typing import Any

from papermind.agents.state import AgentState
from papermind.agents.tools.retrieval_tools import RetrievalTools
from papermind.core.logging.logger import get_logger
from papermind.services.llm.base import BaseLLMProvider, LLMMessage, LLMRequest

log = get_logger(__name__)

_SYSTEM = (
    "You are PaperMind AI, specialised in deep research analysis of academic papers. "
    "Provide rigorous, critical analysis: assess contributions, compare methods, "
    "identify limitations, and situate the work within the broader field."
)

_RESEARCH_PROMPT = """\
Using the following document context from a research paper, perform a deep research analysis.

DOCUMENT CONTEXT:
{context}

USER QUESTION: {query}

Provide a structured analysis covering:
1. **Core Contribution**: What is genuinely new here?
2. **Methodology Analysis**: How does the approach work? What are its key design choices?
3. **Comparison to Related Work**: How does this compare to prior methods? [Source N]
4. **Limitations**: What are the weaknesses or open questions?
5. **Future Directions**: What research directions does this open?

RESEARCH ANALYSIS:"""


class ResearchAgent:
    """Specialist agent for deep research and comparative analysis."""

    def __init__(self, llm: BaseLLMProvider, retrieval_tools: RetrievalTools) -> None:
        self.llm = llm
        self.tools = retrieval_tools

    async def __call__(self, state: AgentState) -> dict[str, Any]:
        query = state.get("query", "")
        filter_doc_ids = state.get("filter_doc_ids")
        path = state.get("agent_path", []) + ["research"]

        # Use a broader retrieval for comparative analysis
        hits = self.tools.search_vector_store(
            query=query,
            top_k=8,
            filter_doc_ids=filter_doc_ids,
        )
        context = self.tools.format_context(hits)
        chunks = [h.chunk for h in hits]

        if not context:
            return {"research_insights": "No context available for research analysis.", "agent_path": path}

        prompt = _RESEARCH_PROMPT.format(context=context, query=query)
        messages = [
            LLMMessage(role="system", content=_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]

        try:
            resp = await self.llm.complete(LLMRequest(messages=messages, temperature=0.3, max_tokens=1200))
            insights = resp.content
            confidence = 0.82
        except Exception as e:
            log.warning("ResearchAgent LLM call failed", error=str(e))
            insights = f"[Research context retrieved]\n\n{context[:800]}"
            confidence = 0.5

        log.info("Research agent complete", length=len(insights))
        return {
            "research_insights": insights,
            "answer": insights,
            "retrieved_chunks": chunks,
            "confidence_score": confidence,
            "agent_path": path,
        }
