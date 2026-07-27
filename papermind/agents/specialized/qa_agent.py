# =============================================================================
# PaperMind AI — QA Agent (default for general questions)
# =============================================================================

from __future__ import annotations

from typing import Any

from papermind.agents.state import AgentState
from papermind.core.logging.logger import get_logger
from papermind.services.llm.base import BaseLLMProvider, LLMMessage, LLMRequest

log = get_logger(__name__)

_SYSTEM = (
    "You are PaperMind AI, a precise and evidence-grounded document analysis assistant. "
    "Answer questions using ONLY the provided document context. "
    "Always cite sources using [Source N] inline notation. "
    "If the context does not contain the answer, say so clearly — do NOT hallucinate."
)

_QA_PROMPT = """\
DOCUMENT CONTEXT:
{context}

USER QUESTION: {query}

Instructions:
- Answer directly and concisely.
- Cite every factual claim with [Source N] where N is the source number above.
- If context is insufficient, state: "The provided documents do not contain enough information to answer this question."

ANSWER:"""


class QAAgent:
    """General-purpose question-answering agent grounded in retrieved context with general LLM fallback."""

    def __init__(self, llm: BaseLLMProvider) -> None:
        self.llm = llm

    async def __call__(self, state: AgentState) -> dict[str, Any]:
        context = state.get("formatted_context", "")
        query = state.get("query", "")
        path = state.get("agent_path", []) + ["qa"]

        if not context:
            # Fallback to general LLM scientific knowledge if document context is absent
            general_prompt = f"Answer the following user question clearly and accurately using scientific knowledge:\n\nQUESTION: {query}"
            messages = [
                LLMMessage(role="system", content="You are PaperMind AI, an expert scientific and research assistant. Provide clear, well-structured, informative answers."),
                LLMMessage(role="user", content=general_prompt),
            ]
            try:
                resp = await self.llm.complete(LLMRequest(messages=messages, temperature=0.2, max_tokens=300))
                answer = resp.content
                confidence = 0.85
            except Exception as e:
                log.warning("QAAgent general fallback call failed", error=str(e))
                answer = f"I could not locate specific context for '{query}' in the uploaded document."
                confidence = 0.3

            return {
                "answer": answer,
                "confidence_score": confidence,
                "agent_path": path,
            }

        prompt = _QA_PROMPT.format(context=context, query=query)
        messages = [
            LLMMessage(role="system", content=_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]

        try:
            resp = await self.llm.complete(LLMRequest(messages=messages, temperature=0.1, max_tokens=300))
            answer = resp.content
            confidence = 0.94
        except Exception as e:
            log.warning("QAAgent LLM call failed", error=str(e))
            answer = f"[Context retrieved from document]\n\n{context[:800]}"
            confidence = 0.5

        log.info("QA agent complete", length=len(answer))
        return {
            "answer": answer,
            "confidence_score": confidence,
            "agent_path": path,
        }
