# =============================================================================
# PaperMind AI — Citation & Reference Extractor
# =============================================================================
# Detects in-text citations (e.g. [1], (Author et al., 2020)) and parses
# structured references from the References section of research papers.
# Links citations to their corresponding reference entries.
# Produces Citation and Reference domain objects.
# =============================================================================

from __future__ import annotations

import re
import uuid

from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import (
    Citation,
    DocumentElement,
    ElementType,
    Reference,
)

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Citation patterns (in-text)
# ---------------------------------------------------------------------------

# Numeric: [1], [1,2], [1-3], [1, 2, 3]
_NUMERIC_CITE = re.compile(
    r"\[(\d+(?:\s*[,;–-]\s*\d+)*)\]"
)

# Author-year: (Author, 2020), (Author et al., 2020), (Author & Author, 2020)
_AUTHOR_YEAR_CITE = re.compile(
    r"\(([A-Z][a-zA-Z]+(?:\s+(?:et\s+al\.?|and|&)\s+[A-Z][a-zA-Z]+)?(?:\s*,\s*\d{4})?)\)"
)

# Author-year without parens: Author et al. (2020), Author (2020)
_AUTHOR_YEAR_INLINE = re.compile(
    r"([A-Z][a-zA-Z]+(?:\s+et\s+al\.?)?)\s+\((\d{4})\)"
)


# ---------------------------------------------------------------------------
# Reference parsing patterns
# ---------------------------------------------------------------------------

# Numbered reference: [1] Authors. Title. Venue, Year.
_NUMBERED_REF = re.compile(
    r"^\[(\d+)\]\s*(.+)", re.MULTILINE
)

# Year extraction
_YEAR_PATTERN = re.compile(r"\b(19|20)\d{2}\b")

# DOI pattern
_DOI_PATTERN = re.compile(
    r"(?:doi:\s*|https?://doi\.org/)(10\.\d{4,}/\S+)",
    re.IGNORECASE,
)

# URL pattern
_URL_PATTERN = re.compile(
    r"https?://\S+"
)

# arXiv pattern
_ARXIV_PATTERN = re.compile(
    r"arXiv:(\d{4}\.\d{4,5}(?:v\d+)?)",
    re.IGNORECASE,
)


class CitationExtractor:
    """
    Extracts in-text citations and structured references from document elements.

    Detection strategies:
      1. Numeric citations: [1], [1,2], [1-3]
      2. Author-year citations: (Author et al., 2020)
      3. Reference section parsing: structured entries from References/Bibliography
    """

    def extract_citations(
        self,
        elements: list[DocumentElement],
    ) -> list[Citation]:
        """
        Extract all in-text citations from document elements.

        Args:
            elements: Flat list of document elements.

        Returns:
            List of Citation domain objects.
        """
        citations: list[Citation] = []

        for element in elements:
            # Skip reference section elements themselves
            if element.element_type == ElementType.REFERENCES:
                continue

            content = element.content

            # Numeric citations [1], [1,2], [1-3]
            for match in _NUMERIC_CITE.finditer(content):
                cite_key = match.group(0)

                # Extract surrounding context (±50 chars)
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end].strip()

                citations.append(
                    Citation(
                        id=str(uuid.uuid4()),
                        cite_key=cite_key,
                        page_number=element.page_number,
                        context=context,
                    )
                )

            # Author-year citations (Author et al., 2020)
            for match in _AUTHOR_YEAR_CITE.finditer(content):
                cite_key = match.group(0)
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end].strip()

                citations.append(
                    Citation(
                        id=str(uuid.uuid4()),
                        cite_key=cite_key,
                        page_number=element.page_number,
                        context=context,
                    )
                )

            # Inline author-year: Author et al. (2020)
            for match in _AUTHOR_YEAR_INLINE.finditer(content):
                cite_key = f"{match.group(1)} ({match.group(2)})"
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end].strip()

                citations.append(
                    Citation(
                        id=str(uuid.uuid4()),
                        cite_key=cite_key,
                        page_number=element.page_number,
                        context=context,
                    )
                )

        log.info(
            "Citation extraction complete",
            total_citations=len(citations),
        )
        return citations

    def extract_references(
        self,
        elements: list[DocumentElement],
    ) -> list[Reference]:
        """
        Extract structured references from the References section.

        Finds the REFERENCES element, then parses subsequent paragraph elements
        as individual reference entries.

        Args:
            elements: Flat list of document elements.

        Returns:
            List of Reference domain objects.
        """
        references: list[Reference] = []

        # Find the start of the references section
        ref_start_idx = None
        for idx, el in enumerate(elements):
            if el.element_type == ElementType.REFERENCES:
                ref_start_idx = idx
                break

        if ref_start_idx is None:
            # Try content-based detection
            for idx, el in enumerate(elements):
                if el.content.strip().lower() in ("references", "bibliography", "works cited"):
                    ref_start_idx = idx
                    break

        if ref_start_idx is None:
            log.debug("No references section found")
            return references

        # Collect reference text entries after the header
        ref_elements = elements[ref_start_idx + 1:]
        ref_entries: list[str] = []

        for el in ref_elements:
            # Stop at next major section
            if el.element_type in (
                ElementType.HEADING,
                ElementType.TITLE,
                ElementType.APPENDIX,
            ):
                break
            if el.content.strip():
                ref_entries.append(el.content.strip())

        # Parse each entry
        for entry_text in ref_entries:
            ref = self._parse_reference_entry(entry_text)
            if ref:
                references.append(ref)

        log.info(
            "Reference extraction complete",
            total_references=len(references),
        )
        return references

    def link_citations_to_references(
        self,
        citations: list[Citation],
        references: list[Reference],
    ) -> list[Citation]:
        """
        Link citations to their corresponding reference entries.

        For numeric citations [n], links to the reference with index=n.
        For author-year citations, attempts fuzzy matching on author names.

        Args:
            citations: List of extracted citations.
            references: List of extracted references.

        Returns:
            Citations with reference_id populated where matches are found.
        """
        # Build index lookup for numbered references
        index_to_ref: dict[int, Reference] = {}
        for ref in references:
            if ref.index is not None:
                index_to_ref[ref.index] = ref

        for citation in citations:
            # Try numeric matching: [1] -> reference with index 1
            numeric_match = re.match(r"\[(\d+)\]", citation.cite_key)
            if numeric_match:
                idx = int(numeric_match.group(1))
                if idx in index_to_ref:
                    citation.reference_id = index_to_ref[idx].id
                continue

            # Author-year matching
            for ref in references:
                if self._author_matches(citation.cite_key, ref):
                    citation.reference_id = ref.id
                    break

        linked = sum(1 for c in citations if c.reference_id is not None)
        log.info(
            "Citation-reference linking complete",
            total_citations=len(citations),
            linked=linked,
        )
        return citations

    def _parse_reference_entry(self, text: str) -> Reference | None:
        """Parse a single reference entry string into a Reference object."""
        if len(text) < 10:
            return None

        ref = Reference(
            id=str(uuid.uuid4()),
            raw_text=text,
        )

        # Extract index: [1], [2], etc.
        num_match = _NUMBERED_REF.match(text)
        if num_match:
            ref.index = int(num_match.group(1))
            text = num_match.group(2).strip()

        # Extract DOI
        doi_match = _DOI_PATTERN.search(text)
        if doi_match:
            ref.doi = doi_match.group(1)

        # Extract URL
        url_match = _URL_PATTERN.search(text)
        if url_match:
            ref.url = url_match.group(0).rstrip(".")

        # Extract arXiv ID
        arxiv_match = _ARXIV_PATTERN.search(text)
        if arxiv_match:
            ref.url = f"https://arxiv.org/abs/{arxiv_match.group(1)}"

        # Extract year
        years = _YEAR_PATTERN.findall(text)
        if years:
            try:
                ref.year = int(years[-1] + years[-1][-2:]) if len(years[-1]) == 2 else int(f"{years[-1][:2]}{years[-1]}")
            except (ValueError, IndexError):
                pass
            # Simpler approach
            all_years = [int(f"{prefix}{y}") for prefix, y in zip(years[::2], years[1::2]) if True]
            if not all_years:
                # Try extracting full 4-digit years directly
                full_years = re.findall(r"\b((?:19|20)\d{2})\b", text)
                if full_years:
                    ref.year = int(full_years[-1])

        # Simple author/title split heuristic:
        # Common pattern: "Authors. Title. Venue, Year."
        parts = text.split(".")
        if len(parts) >= 2:
            # First segment is usually authors
            author_text = parts[0].strip()
            ref.authors = self._parse_authors(author_text)

            # Second segment is usually the title
            if len(parts) >= 3:
                ref.title = parts[1].strip()
                # Third segment and beyond: venue info
                venue_text = ".".join(parts[2:]).strip()
                # Remove DOI/URL from venue
                venue_text = _DOI_PATTERN.sub("", venue_text)
                venue_text = _URL_PATTERN.sub("", venue_text).strip().rstrip(".")
                if venue_text:
                    ref.venue = venue_text

        return ref

    @staticmethod
    def _parse_authors(text: str) -> list[str]:
        """Parse author string into individual author names."""
        # Remove common prefixes like [1]
        text = re.sub(r"^\[\d+\]\s*", "", text)

        # Split by common author separators
        separators = re.compile(r"\s*(?:,\s*and\s+|,\s*&\s*|\s+and\s+|\s*;\s*|,\s*)")
        parts = separators.split(text)

        authors = []
        for part in parts:
            name = part.strip().rstrip(".")
            if name and len(name) > 1:
                authors.append(name)

        return authors

    @staticmethod
    def _author_matches(cite_key: str, ref: Reference) -> bool:
        """Check if a citation key matches a reference by author name."""
        # Extract author surname from citation
        cite_clean = re.sub(r"[(),]", " ", cite_key).strip()
        cite_parts = cite_clean.split()

        if not cite_parts or not ref.authors:
            return False

        first_cite_word = cite_parts[0].lower()

        # Check if the first word of the citation matches any author surname
        for author in ref.authors:
            surname = author.split()[-1].lower() if author.split() else ""
            if surname and surname == first_cite_word:
                return True

        return False
