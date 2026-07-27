# =============================================================================
# PaperMind AI — Document Knowledge Graph Builder
# =============================================================================
# Constructs a NetworkX-based knowledge graph from a fully processed Document.
# Creates typed nodes for sections, tables, figures, equations, citations,
# and references, with semantic edges representing relationships like
# CONTAINS, REFERENCES, FOLLOWS, DESCRIBES, etc.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import networkx as nx

from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import (
    Citation,
    Document,
    DocumentElement,
    ElementType,
    ExtractedEquation,
    ExtractedFigure,
    ExtractedTable,
    Reference,
)

log = get_logger(__name__)


class NodeType(str, Enum):
    """Types of nodes in the document knowledge graph."""

    DOCUMENT = "document"
    SECTION = "section"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    FIGURE = "figure"
    EQUATION = "equation"
    CITATION = "citation"
    REFERENCE = "reference"
    AUTHOR = "author"
    PAGE = "page"


class EdgeType(str, Enum):
    """Types of relationships between nodes."""

    CONTAINS = "contains"              # section -> paragraph, doc -> section
    FOLLOWS = "follows"                # sequential reading order
    REFERENCES = "references"          # citation -> reference
    APPEARS_IN = "appears_in"          # entity -> page
    DESCRIBES = "describes"            # caption -> figure/table
    USES = "uses"                      # section -> equation
    CITES = "cites"                    # paragraph -> citation
    AUTHORED_BY = "authored_by"        # document -> author
    RELATED_TO = "related_to"          # cross-section link


@dataclass
class GraphStats:
    """Statistics about the constructed knowledge graph."""

    total_nodes: int = 0
    total_edges: int = 0
    node_type_counts: dict[str, int] | None = None
    edge_type_counts: dict[str, int] | None = None
    connected_components: int = 0
    density: float = 0.0


class DocumentGraphBuilder:
    """
    Builds a knowledge graph from a processed Document aggregate.

    The graph captures:
      - Document structure (sections, subsections, paragraphs)
      - Extracted entities (tables, figures, equations)
      - Citation network (in-text citations linked to references)
      - Sequential reading order (FOLLOWS edges)
      - Containment hierarchy (CONTAINS edges)
    """

    def build(self, document: Document) -> nx.DiGraph:
        """
        Construct a knowledge graph from a fully processed Document.

        Args:
            document: A Document aggregate with populated elements,
                      tables, figures, equations, citations, and references.

        Returns:
            A NetworkX directed graph with typed nodes and edges.
        """
        graph = nx.DiGraph()

        # 1. Document root node
        self._add_document_node(graph, document)

        # 2. Author nodes
        self._add_author_nodes(graph, document)

        # 3. Page nodes
        self._add_page_nodes(graph, document)

        # 4. Element nodes (sections, paragraphs)
        self._add_element_nodes(graph, document)

        # 5. Table nodes
        self._add_table_nodes(graph, document)

        # 6. Figure nodes
        self._add_figure_nodes(graph, document)

        # 7. Equation nodes
        self._add_equation_nodes(graph, document)

        # 8. Citation and reference nodes
        self._add_citation_nodes(graph, document)

        # 9. Sequential reading order edges
        self._add_reading_order_edges(graph, document)

        stats = self.compute_stats(graph)
        log.info(
            "Knowledge graph constructed",
            doc_id=document.id,
            nodes=stats.total_nodes,
            edges=stats.total_edges,
            components=stats.connected_components,
        )

        return graph

    def _add_document_node(self, graph: nx.DiGraph, doc: Document) -> None:
        """Add the document root node."""
        graph.add_node(
            doc.id,
            node_type=NodeType.DOCUMENT.value,
            label=doc.metadata.title or doc.filename,
            filename=doc.filename,
            page_count=doc.metadata.page_count,
            doc_type=doc.metadata.document_type.value,
            pipeline=doc.pipeline_type.value,
        )

    def _add_author_nodes(self, graph: nx.DiGraph, doc: Document) -> None:
        """Add author nodes and AUTHORED_BY edges."""
        for author in doc.metadata.authors:
            author_id = f"author:{author.lower().replace(' ', '_')}"
            graph.add_node(
                author_id,
                node_type=NodeType.AUTHOR.value,
                label=author,
            )
            graph.add_edge(
                doc.id,
                author_id,
                edge_type=EdgeType.AUTHORED_BY.value,
            )

    def _add_page_nodes(self, graph: nx.DiGraph, doc: Document) -> None:
        """Add page nodes and CONTAINS edges from document."""
        for page_num in range(1, doc.metadata.page_count + 1):
            page_id = f"page:{doc.id}:{page_num}"
            graph.add_node(
                page_id,
                node_type=NodeType.PAGE.value,
                label=f"Page {page_num}",
                page_number=page_num,
            )
            graph.add_edge(
                doc.id,
                page_id,
                edge_type=EdgeType.CONTAINS.value,
            )

    def _add_element_nodes(self, graph: nx.DiGraph, doc: Document) -> None:
        """Add section and paragraph nodes with containment edges."""
        current_section_id: str | None = None

        for element in doc.elements:
            node_id = f"element:{element.id}"

            if element.element_type in (
                ElementType.TITLE,
                ElementType.HEADING,
                ElementType.SUBHEADING,
                ElementType.ABSTRACT,
                ElementType.REFERENCES,
            ):
                node_type = NodeType.SECTION
                # Section is contained by document
                graph.add_node(
                    node_id,
                    node_type=node_type.value,
                    label=element.content[:80],
                    element_type=element.element_type.value,
                    page_number=element.page_number,
                    level=element.level,
                    content=element.content,
                )
                graph.add_edge(
                    doc.id,
                    node_id,
                    edge_type=EdgeType.CONTAINS.value,
                )
                # Link section to its page
                page_id = f"page:{doc.id}:{element.page_number}"
                if graph.has_node(page_id):
                    graph.add_edge(
                        node_id,
                        page_id,
                        edge_type=EdgeType.APPEARS_IN.value,
                    )
                current_section_id = node_id
            else:
                node_type = NodeType.PARAGRAPH
                graph.add_node(
                    node_id,
                    node_type=node_type.value,
                    label=element.content[:60],
                    element_type=element.element_type.value,
                    page_number=element.page_number,
                    content=element.content,
                )
                # Paragraph is contained by current section
                if current_section_id:
                    graph.add_edge(
                        current_section_id,
                        node_id,
                        edge_type=EdgeType.CONTAINS.value,
                    )
                # Link to page
                page_id = f"page:{doc.id}:{element.page_number}"
                if graph.has_node(page_id):
                    graph.add_edge(
                        node_id,
                        page_id,
                        edge_type=EdgeType.APPEARS_IN.value,
                    )

    def _add_table_nodes(self, graph: nx.DiGraph, doc: Document) -> None:
        """Add table nodes with containment and description edges."""
        for table in doc.tables:
            node_id = f"table:{table.id}"
            graph.add_node(
                node_id,
                node_type=NodeType.TABLE.value,
                label=table.caption or f"Table (p.{table.page_number})",
                page_number=table.page_number,
                rows=table.rows,
                cols=table.cols,
                caption=table.caption,
            )
            # Table appears on a page
            page_id = f"page:{doc.id}:{table.page_number}"
            if graph.has_node(page_id):
                graph.add_edge(
                    node_id,
                    page_id,
                    edge_type=EdgeType.APPEARS_IN.value,
                )
            # Document contains table
            graph.add_edge(
                doc.id,
                node_id,
                edge_type=EdgeType.CONTAINS.value,
            )

    def _add_figure_nodes(self, graph: nx.DiGraph, doc: Document) -> None:
        """Add figure nodes."""
        for figure in doc.figures:
            node_id = f"figure:{figure.id}"
            graph.add_node(
                node_id,
                node_type=NodeType.FIGURE.value,
                label=figure.caption or f"Figure (p.{figure.page_number})",
                page_number=figure.page_number,
                caption=figure.caption,
                figure_type=figure.figure_type,
                image_path=figure.image_path,
            )
            page_id = f"page:{doc.id}:{figure.page_number}"
            if graph.has_node(page_id):
                graph.add_edge(
                    node_id,
                    page_id,
                    edge_type=EdgeType.APPEARS_IN.value,
                )
            graph.add_edge(
                doc.id,
                node_id,
                edge_type=EdgeType.CONTAINS.value,
            )

    def _add_equation_nodes(self, graph: nx.DiGraph, doc: Document) -> None:
        """Add equation nodes."""
        for eq in doc.equations:
            node_id = f"equation:{eq.id}"
            graph.add_node(
                node_id,
                node_type=NodeType.EQUATION.value,
                label=eq.raw_text[:60],
                page_number=eq.page_number,
                latex=eq.latex,
                is_inline=eq.is_inline,
                variables=eq.variables,
            )
            page_id = f"page:{doc.id}:{eq.page_number}"
            if graph.has_node(page_id):
                graph.add_edge(
                    node_id,
                    page_id,
                    edge_type=EdgeType.APPEARS_IN.value,
                )
            graph.add_edge(
                doc.id,
                node_id,
                edge_type=EdgeType.CONTAINS.value,
            )

    def _add_citation_nodes(self, graph: nx.DiGraph, doc: Document) -> None:
        """Add citation and reference nodes with linking edges."""
        # Add reference nodes first
        ref_map: dict[str, str] = {}
        for ref in doc.references:
            node_id = f"reference:{ref.id}"
            ref_map[ref.id] = node_id
            graph.add_node(
                node_id,
                node_type=NodeType.REFERENCE.value,
                label=ref.title or ref.raw_text[:60],
                authors=ref.authors,
                year=ref.year,
                doi=ref.doi,
                venue=ref.venue,
                raw_text=ref.raw_text,
            )
            graph.add_edge(
                doc.id,
                node_id,
                edge_type=EdgeType.CONTAINS.value,
            )

        # Add citation nodes and link to references
        for cite in doc.citations:
            node_id = f"citation:{cite.id}"
            graph.add_node(
                node_id,
                node_type=NodeType.CITATION.value,
                label=cite.cite_key,
                page_number=cite.page_number,
                context=cite.context,
            )
            page_id = f"page:{doc.id}:{cite.page_number}"
            if graph.has_node(page_id):
                graph.add_edge(
                    node_id,
                    page_id,
                    edge_type=EdgeType.APPEARS_IN.value,
                )

            # Link citation to reference
            if cite.reference_id and cite.reference_id in ref_map:
                graph.add_edge(
                    node_id,
                    ref_map[cite.reference_id],
                    edge_type=EdgeType.REFERENCES.value,
                )

    def _add_reading_order_edges(
        self, graph: nx.DiGraph, doc: Document
    ) -> None:
        """Add sequential FOLLOWS edges between elements in reading order."""
        sorted_elements = sorted(
            doc.elements,
            key=lambda el: (el.page_number, el.reading_order),
        )

        for i in range(len(sorted_elements) - 1):
            curr_id = f"element:{sorted_elements[i].id}"
            next_id = f"element:{sorted_elements[i + 1].id}"
            if graph.has_node(curr_id) and graph.has_node(next_id):
                graph.add_edge(
                    curr_id,
                    next_id,
                    edge_type=EdgeType.FOLLOWS.value,
                )

    @staticmethod
    def compute_stats(graph: nx.DiGraph) -> GraphStats:
        """Compute summary statistics about the graph."""
        node_types: dict[str, int] = {}
        for _, data in graph.nodes(data=True):
            nt = data.get("node_type", "unknown")
            node_types[nt] = node_types.get(nt, 0) + 1

        edge_types: dict[str, int] = {}
        for _, _, data in graph.edges(data=True):
            et = data.get("edge_type", "unknown")
            edge_types[et] = edge_types.get(et, 0) + 1

        return GraphStats(
            total_nodes=graph.number_of_nodes(),
            total_edges=graph.number_of_edges(),
            node_type_counts=node_types,
            edge_type_counts=edge_types,
            connected_components=nx.number_weakly_connected_components(graph),
            density=nx.density(graph),
        )
