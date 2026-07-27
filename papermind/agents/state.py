# =============================================================================
# PaperMind AI — Shared Agent State Schema
# =============================================================================
# This TypedDict is the canonical state object threaded through all nodes in
# every PaperMind LangGraph workflow. Any field can be absent (total=False);
# nodes only read/write the fields they own.
# =============================================================================

from __future__ import annotations

from typing import Any, TypedDict

from papermind.models.domain.document import SemanticChunk


class AgentState(TypedDict, total=False):
    """Canonical shared state across all PaperMind LangGraph agent nodes."""

    # ── Input ──────────────────────────────────────────────────────────────
    query: str                           # User's natural-language question
    intent: str                          # Classified intent (qa, summary, table, ...)
    filter_doc_ids: list[str] | None     # Scope search to these document IDs

    # ── Retrieval ──────────────────────────────────────────────────────────
    retrieved_chunks: list[SemanticChunk]
    formatted_context: str               # Context block formatted for LLM

    # ── Specialised agent outputs ───────────────────────────────────────────
    summary: str                         # Summary agent output
    table_explanation: str               # Table agent output
    figure_explanation: str              # Figure agent output
    equation_explanation: str            # Equation agent output
    citation_analysis: list[dict[str, Any]]   # Citation agent output
    research_insights: str               # Research agent output

    # ── Final answer ────────────────────────────────────────────────────────
    answer: str
    citations: list[dict[str, Any]]      # Verified source evidence
    confidence_score: float

    # ── Metadata ────────────────────────────────────────────────────────────
    agent_path: list[str]                # Which agents were invoked
    error: str | None
