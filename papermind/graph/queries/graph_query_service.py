# =============================================================================
# PaperMind AI — Graph Query Service
# =============================================================================
# Provides query methods over the document knowledge graph.
# Supports neighborhood queries, path finding, subgraph extraction,
# and typed node/edge filtering.
# =============================================================================

from __future__ import annotations

from typing import Any

import networkx as nx

from papermind.core.logging.logger import get_logger
from papermind.graph.builders.document_graph_builder import EdgeType, NodeType

log = get_logger(__name__)


class GraphQueryService:
    """
    Query interface for the document knowledge graph.

    Provides methods for:
      - Neighborhood exploration (k-hop neighbors)
      - Shortest path finding
      - Subgraph extraction by node/edge type
      - Content search across graph nodes
      - Structure analysis
    """

    def __init__(self, graph: nx.DiGraph) -> None:
        self._graph = graph

    @property
    def graph(self) -> nx.DiGraph:
        return self._graph

    # ------------------------------------------------------------------
    # Node Queries
    # ------------------------------------------------------------------

    def get_nodes_by_type(
        self,
        node_type: NodeType | str,
    ) -> list[dict[str, Any]]:
        """
        Get all nodes of a specific type.

        Args:
            node_type: The NodeType enum or string value.

        Returns:
            List of node attribute dictionaries with 'id' key added.
        """
        type_str = node_type.value if isinstance(node_type, NodeType) else node_type
        results = []
        for node_id, data in self._graph.nodes(data=True):
            if data.get("node_type") == type_str:
                results.append({"id": node_id, **data})
        return results

    def get_node(self, node_id: str) -> dict[str, Any] | None:
        """Get a single node's attributes by ID."""
        if self._graph.has_node(node_id):
            return {"id": node_id, **self._graph.nodes[node_id]}
        return None

    def search_nodes(
        self,
        query: str,
        node_type: NodeType | str | None = None,
        search_fields: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for nodes whose attributes contain the query string.

        Args:
            query: Text to search for (case-insensitive).
            node_type: Optional filter by node type.
            search_fields: Attribute keys to search in. Defaults to
                           ['label', 'content', 'raw_text', 'caption'].

        Returns:
            List of matching node dictionaries.
        """
        if search_fields is None:
            search_fields = ["label", "content", "raw_text", "caption", "context"]

        query_lower = query.lower()
        type_str = (
            node_type.value if isinstance(node_type, NodeType) else node_type
        )

        results = []
        for node_id, data in self._graph.nodes(data=True):
            if type_str and data.get("node_type") != type_str:
                continue

            for field in search_fields:
                value = data.get(field, "")
                if isinstance(value, str) and query_lower in value.lower():
                    results.append({"id": node_id, **data})
                    break

        return results

    # ------------------------------------------------------------------
    # Neighborhood Queries
    # ------------------------------------------------------------------

    def get_neighbors(
        self,
        node_id: str,
        edge_type: EdgeType | str | None = None,
        direction: str = "both",
    ) -> list[dict[str, Any]]:
        """
        Get neighbor nodes, optionally filtered by edge type and direction.

        Args:
            node_id: The source node ID.
            edge_type: Optional filter by edge type.
            direction: 'out' (successors), 'in' (predecessors), or 'both'.

        Returns:
            List of neighbor node attribute dictionaries.
        """
        if not self._graph.has_node(node_id):
            return []

        type_str = (
            edge_type.value if isinstance(edge_type, EdgeType) else edge_type
        )

        neighbors: set[str] = set()

        if direction in ("out", "both"):
            for _, target, data in self._graph.out_edges(node_id, data=True):
                if type_str is None or data.get("edge_type") == type_str:
                    neighbors.add(target)

        if direction in ("in", "both"):
            for source, _, data in self._graph.in_edges(node_id, data=True):
                if type_str is None or data.get("edge_type") == type_str:
                    neighbors.add(source)

        return [
            {"id": nid, **self._graph.nodes[nid]}
            for nid in neighbors
            if self._graph.has_node(nid)
        ]

    def get_k_hop_neighborhood(
        self,
        node_id: str,
        k: int = 2,
    ) -> nx.DiGraph:
        """
        Extract the k-hop neighborhood subgraph around a node.

        Args:
            node_id: Center node ID.
            k: Number of hops.

        Returns:
            A subgraph containing all nodes within k hops.
        """
        if not self._graph.has_node(node_id):
            return nx.DiGraph()

        # Get nodes within k hops in the undirected version
        undirected = self._graph.to_undirected()
        reachable = nx.single_source_shortest_path_length(undirected, node_id, cutoff=k)
        subgraph_nodes = list(reachable.keys())

        return self._graph.subgraph(subgraph_nodes).copy()

    # ------------------------------------------------------------------
    # Path Queries
    # ------------------------------------------------------------------

    def find_shortest_path(
        self,
        source: str,
        target: str,
    ) -> list[str] | None:
        """
        Find the shortest path between two nodes.

        Returns:
            List of node IDs forming the path, or None if no path exists.
        """
        try:
            return nx.shortest_path(self._graph, source, target)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    def find_all_paths(
        self,
        source: str,
        target: str,
        max_length: int = 5,
    ) -> list[list[str]]:
        """
        Find all simple paths between two nodes up to a maximum length.

        Returns:
            List of paths, where each path is a list of node IDs.
        """
        try:
            return list(
                nx.all_simple_paths(
                    self._graph, source, target, cutoff=max_length
                )
            )
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    # ------------------------------------------------------------------
    # Subgraph Extraction
    # ------------------------------------------------------------------

    def extract_subgraph(
        self,
        node_types: list[NodeType | str] | None = None,
        edge_types: list[EdgeType | str] | None = None,
    ) -> nx.DiGraph:
        """
        Extract a subgraph filtered by node and/or edge types.

        Args:
            node_types: Keep only these node types.
            edge_types: Keep only these edge types.

        Returns:
            A filtered subgraph.
        """
        subgraph = self._graph.copy()

        if node_types:
            type_strs = {
                t.value if isinstance(t, NodeType) else t for t in node_types
            }
            remove_nodes = [
                nid
                for nid, data in subgraph.nodes(data=True)
                if data.get("node_type") not in type_strs
            ]
            subgraph.remove_nodes_from(remove_nodes)

        if edge_types:
            type_strs = {
                t.value if isinstance(t, EdgeType) else t for t in edge_types
            }
            remove_edges = [
                (u, v)
                for u, v, data in subgraph.edges(data=True)
                if data.get("edge_type") not in type_strs
            ]
            subgraph.remove_edges_from(remove_edges)

        return subgraph

    def get_page_subgraph(self, doc_id: str, page_number: int) -> nx.DiGraph:
        """
        Extract a subgraph containing all nodes that appear on a specific page.

        Args:
            doc_id: Document ID.
            page_number: Page number to filter by.

        Returns:
            Subgraph of the specified page.
        """
        page_node_id = f"page:{doc_id}:{page_number}"
        if not self._graph.has_node(page_node_id):
            return nx.DiGraph()

        # Get all nodes linked to this page
        page_nodes = {page_node_id}
        for source, _, data in self._graph.in_edges(page_node_id, data=True):
            if data.get("edge_type") == EdgeType.APPEARS_IN.value:
                page_nodes.add(source)

        return self._graph.subgraph(page_nodes).copy()

    # ------------------------------------------------------------------
    # Analysis
    # ------------------------------------------------------------------

    def get_section_content(self, section_node_id: str) -> list[dict[str, Any]]:
        """
        Get all content nodes contained within a section.

        Follows CONTAINS edges recursively to collect all nested content.
        """
        content: list[dict[str, Any]] = []

        def _collect(node_id: str) -> None:
            for _, target, data in self._graph.out_edges(node_id, data=True):
                if data.get("edge_type") == EdgeType.CONTAINS.value:
                    if self._graph.has_node(target):
                        content.append(
                            {"id": target, **self._graph.nodes[target]}
                        )
                        _collect(target)

        _collect(section_node_id)
        return content

    def get_citation_network(self) -> nx.DiGraph:
        """
        Extract the citation network subgraph (citations → references).
        """
        return self.extract_subgraph(
            node_types=[NodeType.CITATION, NodeType.REFERENCE],
            edge_types=[EdgeType.REFERENCES],
        )

    def summary(self) -> dict[str, Any]:
        """Return a summary of the graph structure."""
        from papermind.graph.builders.document_graph_builder import DocumentGraphBuilder

        stats = DocumentGraphBuilder.compute_stats(self._graph)
        return {
            "total_nodes": stats.total_nodes,
            "total_edges": stats.total_edges,
            "node_types": stats.node_type_counts,
            "edge_types": stats.edge_type_counts,
            "connected_components": stats.connected_components,
            "density": round(stats.density, 6),
        }
