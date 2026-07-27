# =============================================================================
# PaperMind AI — Document Tree Builder
# =============================================================================
# Constructs a hierarchical section tree from flat DocumentElements.
# Uses heading levels (TITLE → HEADING → SUBHEADING → PARAGRAPH) to
# determine parent-child nesting, producing a traversable tree structure
# that captures the logical organization of the document.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass, field

from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import DocumentElement, ElementType

log = get_logger(__name__)


# Hierarchy ranking — lower number = higher in the tree
_LEVEL_MAP: dict[ElementType, int] = {
    ElementType.TITLE: 0,
    ElementType.HEADING: 1,
    ElementType.SUBHEADING: 2,
    ElementType.ABSTRACT: 1,
    ElementType.REFERENCES: 1,
    ElementType.APPENDIX: 1,
    ElementType.PARAGRAPH: 3,
    ElementType.TABLE: 3,
    ElementType.FIGURE: 3,
    ElementType.EQUATION: 3,
    ElementType.CAPTION: 4,
    ElementType.CITATION: 4,
    ElementType.AUTHORS: 1,
    ElementType.HEADER: 5,
    ElementType.FOOTER: 5,
    ElementType.PAGE_NUMBER: 5,
    ElementType.UNKNOWN: 3,
}


@dataclass
class TreeNode:
    """A node in the document section tree."""

    element: DocumentElement | None = None
    section_title: str = ""
    level: int = 0
    children: list[TreeNode] = field(default_factory=list)
    parent: TreeNode | None = field(default=None, repr=False)

    @property
    def is_root(self) -> bool:
        return self.parent is None and self.element is None

    @property
    def is_leaf(self) -> bool:
        return len(self.children) == 0

    @property
    def depth(self) -> int:
        """Distance from the root node."""
        count = 0
        node = self.parent
        while node is not None:
            count += 1
            node = node.parent
        return count

    def get_all_text(self) -> str:
        """Recursively collect all text from this node and its descendants."""
        parts: list[str] = []
        if self.element:
            parts.append(self.element.content)
        for child in self.children:
            parts.append(child.get_all_text())
        return "\n".join(parts)

    def get_section_elements(self) -> list[DocumentElement]:
        """Collect all elements in this subtree (depth-first)."""
        elements: list[DocumentElement] = []
        if self.element:
            elements.append(self.element)
        for child in self.children:
            elements.extend(child.get_section_elements())
        return elements

    def walk(self) -> list[TreeNode]:
        """Depth-first traversal of the subtree rooted at this node."""
        result: list[TreeNode] = [self]
        for child in self.children:
            result.extend(child.walk())
        return result

    def get_sections(self, max_level: int = 2) -> list[TreeNode]:
        """Return all nodes at or above the specified hierarchy level."""
        return [
            node for node in self.walk()
            if node.level <= max_level and node.section_title
        ]


@dataclass
class DocumentTree:
    """A hierarchical representation of a document's logical structure."""

    root: TreeNode = field(default_factory=TreeNode)
    total_nodes: int = 0
    max_depth: int = 0

    @property
    def sections(self) -> list[TreeNode]:
        """Return all heading-level sections."""
        return self.root.get_sections(max_level=2)

    def flatten(self) -> list[DocumentElement]:
        """Return all elements in reading order."""
        return self.root.get_section_elements()


class DocumentTreeBuilder:
    """
    Builds a hierarchical document tree from a flat list of DocumentElements.

    The algorithm uses a stack-based approach:
    - Structural elements (titles, headings, subheadings) create new branches.
    - Content elements (paragraphs, tables, figures) are attached as children
      of the nearest preceding structural element.
    """

    def build(self, elements: list[DocumentElement]) -> DocumentTree:
        """
        Construct a document tree from a flat, reading-order list of elements.

        Args:
            elements: List of DocumentElements sorted by reading order.

        Returns:
            A DocumentTree with the hierarchical structure.
        """
        # Sort by page, then by reading order
        sorted_elements = sorted(
            elements,
            key=lambda el: (el.page_number, el.reading_order),
        )

        root = TreeNode(section_title="__root__", level=-1)
        tree = DocumentTree(root=root)

        # Stack tracks the current path from root to the deepest open section
        # Each entry is (level, node)
        stack: list[tuple[int, TreeNode]] = [(-1, root)]

        for element in sorted_elements:
            level = _LEVEL_MAP.get(element.element_type, 3)

            node = TreeNode(
                element=element,
                section_title=element.content if level <= 2 else "",
                level=level,
            )

            # Pop the stack until we find a parent at a strictly higher level
            while len(stack) > 1 and stack[-1][0] >= level:
                stack.pop()

            # Attach to the current top of stack
            parent_node = stack[-1][1]
            node.parent = parent_node
            parent_node.children.append(node)

            # If this is a structural element, push it onto the stack
            if level <= 2:
                stack.append((level, node))

            tree.total_nodes += 1

        # Compute max depth
        if tree.total_nodes > 0:
            tree.max_depth = max(node.depth for node in root.walk())

        log.info(
            "Document tree constructed",
            total_nodes=tree.total_nodes,
            max_depth=tree.max_depth,
            sections=len(tree.sections),
        )

        return tree
