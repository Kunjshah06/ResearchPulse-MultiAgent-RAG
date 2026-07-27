# =============================================================================
# PaperMind AI — Multi-Agent Orchestration Workflow (LangGraph)
# =============================================================================
#
# Graph Architecture:
#
#   START
#     │
#   [router]            ← classifies intent, sets state["intent"]
#     │
#   [retrieval]         ← dense vector fetch, populates context
#     │
#   conditional_dispatch ──► [summary]    (intent=summary)
#                        ──► [table]      (intent=table)
#                        ──► [figure]     (intent=figure)
#                        ──► [equation]   (intent=equation)
#                        ──► [citation]   (intent=citation)
#                        ──► [research]   (intent=research)
#                        ──► [qa]         (intent=qa, default)
#     │
#   [verify_citations]  ← maps [Source N] to structured evidence
#     │
#   END
#
# All specialist nodes are async; retrieval node is sync.
# =============================================================================

from __future__ import annotations

from typing import Any

from langgraph.graph import END, START, StateGraph

from papermind.agents.specialized.citation_agent import CitationAgent
from papermind.agents.specialized.citation_verifier import CitationVerifier
from papermind.agents.specialized.equation_agent import EquationAgent
from papermind.agents.specialized.figure_agent import FigureAgent
from papermind.agents.specialized.qa_agent import QAAgent
from papermind.agents.specialized.research_agent import ResearchAgent
from papermind.agents.specialized.retrieval_agent import RetrievalAgent
from papermind.agents.specialized.router_agent import RouterAgent
from papermind.agents.specialized.summary_agent import SummaryAgent
from papermind.agents.state import AgentState
from papermind.agents.tools.retrieval_tools import RetrievalTools
from papermind.core.logging.logger import get_logger
from papermind.services.llm.base import BaseLLMProvider
from papermind.services.llm.factory import create_llm_provider

log = get_logger(__name__)


def _route_by_intent(state: AgentState) -> str:
    """Conditional edge function: returns which specialist node to invoke."""
    return state.get("intent", "qa")


class PaperMindRAGWorkflow:
    """
    Production-grade multi-agent RAG orchestration using LangGraph.

    Instantiates all specialist agents once; the compiled graph is reused
    across requests (thread-safe via LangGraph's checkpointing model).
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider | None = None,
        retrieval_tools: RetrievalTools | None = None,
    ) -> None:
        self.llm = llm_provider or create_llm_provider()
        self.tools = retrieval_tools or RetrievalTools()

        # Instantiate all agents
        self._router = RouterAgent()
        self._retrieval = RetrievalAgent(self.tools, top_k=5)
        self._qa = QAAgent(self.llm)
        self._summary = SummaryAgent(self.llm)
        self._table = TableAgent(self.llm, self.tools)
        self._figure = FigureAgent(self.llm, self.tools)
        self._equation = EquationAgent(self.llm, self.tools)
        self._citation = CitationAgent(self.llm, self.tools)
        self._research = ResearchAgent(self.llm, self.tools)
        self._verifier = CitationVerifier()

        self.graph = self._build_graph()

    def _build_graph(self):
        """Compile the full multi-agent LangGraph StateGraph."""
        wf = StateGraph(AgentState)

        # ── Nodes ──────────────────────────────────────────────────────────
        wf.add_node("router", self._router)
        wf.add_node("retrieval", self._retrieval)
        wf.add_node("qa", self._qa)
        wf.add_node("summary", self._summary)
        wf.add_node("table", self._table)
        wf.add_node("figure", self._figure)
        wf.add_node("equation", self._equation)
        wf.add_node("citation", self._citation)
        wf.add_node("research", self._research)
        wf.add_node("verify_citations", self._verifier)

        # ── Entry ──────────────────────────────────────────────────────────
        wf.add_edge(START, "router")
        wf.add_edge("router", "retrieval")

        # ── Conditional dispatch from retrieval → specialist ───────────────
        wf.add_conditional_edges(
            "retrieval",
            _route_by_intent,
            {
                "qa":       "qa",
                "summary":  "summary",
                "table":    "table",
                "figure":   "figure",
                "equation": "equation",
                "citation": "citation",
                "research": "research",
            },
        )

        # ── All specialists → citation verifier → END ──────────────────────
        for node in ("qa", "summary", "table", "figure", "equation", "citation", "research"):
            wf.add_edge(node, "verify_citations")

        wf.add_edge("verify_citations", END)

        return wf.compile()

    async def run(
        self,
        query: str,
        filter_doc_ids: list[str] | None = None,
    ) -> AgentState:
        """
        Execute the full multi-agent workflow.

        Args:
            query: User natural-language question.
            filter_doc_ids: Scope retrieval to specific document IDs.

        Returns:
            Final AgentState with answer, citations, and full agent trace.
        """
        initial: AgentState = {
            "query": query,
            "filter_doc_ids": filter_doc_ids,
            "retrieved_chunks": [],
            "formatted_context": "",
            "answer": "",
            "citations": [],
            "confidence_score": 0.0,
            "agent_path": [],
            "error": None,
        }

        result = await self.graph.ainvoke(initial)
        log.info(
            "Workflow complete",
            intent=result.get("intent"),
            agents=result.get("agent_path"),
            confidence=result.get("confidence_score"),
        )
        return result


# ---------------------------------------------------------------------------
# Avoid circular import: import table/figure/equation agents after class defs
# ---------------------------------------------------------------------------
from papermind.agents.specialized.table_agent import TableAgent      # noqa: E402
from papermind.agents.specialized.figure_agent import FigureAgent    # noqa: E402
from papermind.agents.specialized.equation_agent import EquationAgent  # noqa: E402
