# =============================================================================
# PaperMind AI — Equation Agent
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
    "You are PaperMind AI, specialised in mathematical analysis of academic papers. "
    "Explain equations clearly for both technical and semi-technical audiences: "
    "define variables, explain what the expression computes, its role in the method, "
    "and any special cases or constraints."
)

_EQUATION_PROMPT = """\
The following equation(s) were extracted from a research paper:

EQUATION DATA:
{equation_context}

USER QUESTION: {query}

Provide:
1. The equation in readable form (render LaTeX if present).
2. Variable definitions (what each symbol means).
3. What the equation computes or optimises.
4. Its role within the paper's methodology.
5. Cite using [Source N] notation.

EXPLANATION:"""


class EquationAgent:
    """Specialist agent for explaining mathematical equations and formulas."""

    def __init__(self, llm: BaseLLMProvider, retrieval_tools: RetrievalTools) -> None:
        self.llm = llm
        self.tools = retrieval_tools

    async def __call__(self, state: AgentState) -> dict[str, Any]:
        query = state.get("query", "")
        filter_doc_ids = state.get("filter_doc_ids")
        path = state.get("agent_path", []) + ["equation"]

        hits = self.tools.search_by_chunk_type(
            query=query,
            chunk_type=ChunkType.EQUATION,
            top_k=3,
            filter_doc_ids=filter_doc_ids,
        )

        if not hits:
            hits = self.tools.search_vector_store(query=query, top_k=5, filter_doc_ids=filter_doc_ids)

        equation_context = self.tools.format_context(hits)
        chunks = [h.chunk for h in hits]

        if not equation_context:
            return {"equation_explanation": "No equation context found.", "agent_path": path}

        prompt = _EQUATION_PROMPT.format(equation_context=equation_context, query=query)
        messages = [
            LLMMessage(role="system", content=_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]

        try:
            resp = await self.llm.complete(LLMRequest(messages=messages, temperature=0.1, max_tokens=700))
            explanation = resp.content
            confidence = 0.87
        except Exception as e:
            log.warning("EquationAgent LLM call failed", error=str(e))
            explanation = f"[Equation context retrieved]\n\n{equation_context[:600]}"
            confidence = 0.5

        log.info("Equation agent complete")
        return {
            "equation_explanation": explanation,
            "answer": explanation,
            "retrieved_chunks": chunks,
            "confidence_score": confidence,
            "agent_path": path,
        }
