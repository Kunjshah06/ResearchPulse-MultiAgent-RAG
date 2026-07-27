# =============================================================================
# PaperMind AI — Router Agent
# =============================================================================
# Classifies the user query intent and routes to the correct specialist agent.
# Intent drives conditional_edges in the orchestration graph — no LLM call
# needed, pure heuristic keyword matching (fast & cheap at this layer).
# =============================================================================

from __future__ import annotations

import re
from typing import Any

from papermind.agents.state import AgentState
from papermind.core.logging.logger import get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Intent keyword mapping  (ordered: first match wins)
# ---------------------------------------------------------------------------
_INTENT_PATTERNS: list[tuple[str, list[str]]] = [
    ("summary",    ["summarize", "summary", "overview", "tldr", "tl;dr", "abstract", "brief"]),
    ("table",      ["table", "tabular", "row", "column", "cell", "dataset", "benchmark", "results table"]),
    ("figure",     ["figure", "diagram", "image", "plot", "graph", "chart", "illustration", "architecture"]),
    ("equation",   ["equation", "formula", "loss function", "math", "expression", "gradient", "latex"]),
    ("citation",   ["cite", "citation", "citations", "reference", "references", "bibliography", "doi", "who wrote"]),
    ("research",   ["compare", "comparison", "related work", "state of the art", "contribution", "novelty", "limitation"]),
    ("qa",         []),  # default fallback
]


def classify_intent(query: str) -> str:
    """Return the intent label for a given query string."""
    q = query.lower()
    for intent, keywords in _INTENT_PATTERNS:
        if any(kw in q for kw in keywords):
            return intent
    return "qa"


class RouterAgent:
    """
    Stateless router that classifies intent and populates state["intent"].
    This is the entry node in the orchestration graph.
    """

    def __call__(self, state: AgentState) -> dict[str, Any]:
        query = state.get("query", "")
        intent = classify_intent(query)

        log.info("Router classified intent", query=query[:80], intent=intent)

        return {
            "intent": intent,
            "agent_path": [f"router:{intent}"],
        }
