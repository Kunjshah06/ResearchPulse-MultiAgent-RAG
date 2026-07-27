# =============================================================================
# PaperMind AI — Citation Verifier Node
# =============================================================================
# Post-processes the final answer: extracts [Source N] references,
# maps them to retrieved chunks, and builds the structured citations list.
# =============================================================================

from __future__ import annotations

import re
from typing import Any

from papermind.agents.state import AgentState
from papermind.core.logging.logger import get_logger
from papermind.models.domain.document import SemanticChunk

log = get_logger(__name__)

_SOURCE_RE = re.compile(r"\[Source\s*(\d+)\]", re.IGNORECASE)


class CitationVerifier:
    """
    Extracts [Source N] references from the final answer and maps them
    to the retrieved chunks to produce structured evidence citations.
    """

    def __call__(self, state: AgentState) -> dict[str, Any]:
        answer = state.get("answer", "")
        chunks: list[SemanticChunk] = state.get("retrieved_chunks", [])

        # Find all [Source N] tags referenced in the answer
        cited_indices = {int(m) for m in _SOURCE_RE.findall(answer)}

        citations = []
        for idx, chunk in enumerate(chunks, 1):
            # Include if explicitly cited OR if there is only one chunk
            if idx in cited_indices or (not cited_indices and len(chunks) <= 2):
                citations.append(
                    {
                        "source_id": f"Source {idx}",
                        "doc_id": chunk.doc_id,
                        "page_number": chunk.page_number,
                        "section": chunk.section or "",
                        "chunk_type": chunk.chunk_type.value,
                        "bounding_box": (
                            {
                                "x0": chunk.bounding_box.x0,
                                "y0": chunk.bounding_box.y0,
                                "x1": chunk.bounding_box.x1,
                                "y1": chunk.bounding_box.y1,
                                "page": chunk.bounding_box.page,
                            }
                            if chunk.bounding_box
                            else None
                        ),
                        "snippet": chunk.content[:200],
                    }
                )

        log.info(
            "Citation verifier complete",
            cited=len(cited_indices),
            verified=len(citations),
        )
        return {"citations": citations}
