# =============================================================================
# PaperMind AI — Summary Agent
# =============================================================================

from __future__ import annotations

from typing import Any

from papermind.agents.state import AgentState
from papermind.core.logging.logger import get_logger
from papermind.services.llm.base import BaseLLMProvider, LLMMessage, LLMRequest

log = get_logger(__name__)

_SYSTEM = (
    "You are PaperMind AI, an expert research paper analyst. "
    "Generate clear, structured, and concise summaries of academic documents."
)

_SUMMARY_PROMPT = """\
Using ONLY the document context provided below, generate a comprehensive summary.

Structure your summary as:
• **Core Contribution**: What problem does this paper solve?
• **Methodology**: What approach or method is proposed?
• **Key Results**: What are the main findings/metrics?
• **Significance**: Why does this work matter?

DOCUMENT CONTEXT:
{context}

SUMMARY:"""


class SummaryAgent:
    """Generates a structured paper summary from retrieved context."""

    def __init__(self, llm: BaseLLMProvider) -> None:
        self.llm = llm

    async def __call__(self, state: AgentState) -> dict[str, Any]:
        context = state.get("formatted_context", "")
        query = state.get("query", "")
        path = state.get("agent_path", []) + ["summary"]

        if not context:
            return {"summary": "No document context available for summarisation.", "agent_path": path}

        prompt = _SUMMARY_PROMPT.format(context=context)
        messages = [
            LLMMessage(role="system", content=_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]

        try:
            resp = await self.llm.complete(LLMRequest(messages=messages, temperature=0.2, max_tokens=800))
            summary = resp.content
        except Exception as e:
            log.warning("SummaryAgent LLM call failed", error=str(e))
            summary = f"Context retrieved ({len(context)} chars). LLM unavailable: {e}"

        log.info("Summary agent complete", length=len(summary))
        return {
            "summary": summary,
            "answer": summary,
            "confidence_score": 0.85,
            "agent_path": path,
        }
