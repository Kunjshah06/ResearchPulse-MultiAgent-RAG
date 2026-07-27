# =============================================================================
# PaperMind AI — Domain Exceptions
# =============================================================================
# Centralized, typed exception hierarchy.
# Every layer raises these; FastAPI exception handlers convert them to HTTP.
# =============================================================================

from __future__ import annotations

from typing import Any


class PaperMindError(Exception):
    """Base exception for all PaperMind errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "PAPERMIND_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# Document Errors
# ---------------------------------------------------------------------------


class DocumentNotFoundError(PaperMindError):
    def __init__(self, doc_id: str) -> None:
        super().__init__(
            message=f"Document '{doc_id}' not found.",
            error_code="DOCUMENT_NOT_FOUND",
            details={"doc_id": doc_id},
        )


class UnsupportedFileTypeError(PaperMindError):
    def __init__(self, file_type: str) -> None:
        super().__init__(
            message=f"File type '{file_type}' is not supported.",
            error_code="UNSUPPORTED_FILE_TYPE",
            details={"file_type": file_type},
        )


class FileSizeLimitError(PaperMindError):
    def __init__(self, size_mb: float, limit_mb: int) -> None:
        super().__init__(
            message=f"File size {size_mb:.1f} MB exceeds the {limit_mb} MB limit.",
            error_code="FILE_SIZE_LIMIT_EXCEEDED",
            details={"size_mb": size_mb, "limit_mb": limit_mb},
        )


class DocumentProcessingError(PaperMindError):
    def __init__(self, doc_id: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to process document '{doc_id}': {reason}",
            error_code="DOCUMENT_PROCESSING_FAILED",
            details={"doc_id": doc_id, "reason": reason},
        )


# ---------------------------------------------------------------------------
# Pipeline Errors
# ---------------------------------------------------------------------------


class OCRError(PaperMindError):
    def __init__(self, page: int, reason: str) -> None:
        super().__init__(
            message=f"OCR failed on page {page}: {reason}",
            error_code="OCR_ERROR",
            details={"page": page, "reason": reason},
        )


class LayoutAnalysisError(PaperMindError):
    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"Layout analysis failed: {reason}",
            error_code="LAYOUT_ANALYSIS_ERROR",
            details={"reason": reason},
        )


class ExtractionError(PaperMindError):
    def __init__(self, element_type: str, reason: str) -> None:
        super().__init__(
            message=f"Failed to extract {element_type}: {reason}",
            error_code="EXTRACTION_ERROR",
            details={"element_type": element_type, "reason": reason},
        )


# ---------------------------------------------------------------------------
# LLM / Provider Errors
# ---------------------------------------------------------------------------


class LLMProviderError(PaperMindError):
    def __init__(self, provider: str, reason: str) -> None:
        super().__init__(
            message=f"LLM provider '{provider}' error: {reason}",
            error_code="LLM_PROVIDER_ERROR",
            details={"provider": provider, "reason": reason},
        )


class LLMRateLimitError(PaperMindError):
    def __init__(self, provider: str, retry_after: int | None = None) -> None:
        super().__init__(
            message=f"Rate limit exceeded for provider '{provider}'.",
            error_code="LLM_RATE_LIMIT",
            details={"provider": provider, "retry_after": retry_after},
        )


class LLMContextWindowError(PaperMindError):
    def __init__(self, provider: str, token_count: int, max_tokens: int) -> None:
        super().__init__(
            message=f"Input ({token_count} tokens) exceeds model context ({max_tokens} tokens).",
            error_code="LLM_CONTEXT_WINDOW_EXCEEDED",
            details={"provider": provider, "token_count": token_count, "max_tokens": max_tokens},
        )


# ---------------------------------------------------------------------------
# Retrieval Errors
# ---------------------------------------------------------------------------


class VectorStoreError(PaperMindError):
    def __init__(self, operation: str, reason: str) -> None:
        super().__init__(
            message=f"Vector store '{operation}' failed: {reason}",
            error_code="VECTOR_STORE_ERROR",
            details={"operation": operation, "reason": reason},
        )


class EmbeddingError(PaperMindError):
    def __init__(self, reason: str) -> None:
        super().__init__(
            message=f"Embedding generation failed: {reason}",
            error_code="EMBEDDING_ERROR",
            details={"reason": reason},
        )


class RetrievalError(PaperMindError):
    def __init__(self, query: str, reason: str) -> None:
        super().__init__(
            message=f"Retrieval failed for query '{query[:80]}...': {reason}",
            error_code="RETRIEVAL_ERROR",
            details={"query_preview": query[:80], "reason": reason},
        )


# ---------------------------------------------------------------------------
# Agent Errors
# ---------------------------------------------------------------------------


class AgentError(PaperMindError):
    def __init__(self, agent_name: str, reason: str) -> None:
        super().__init__(
            message=f"Agent '{agent_name}' failed: {reason}",
            error_code="AGENT_ERROR",
            details={"agent_name": agent_name, "reason": reason},
        )


class AgentTimeoutError(PaperMindError):
    def __init__(self, agent_name: str, timeout: int) -> None:
        super().__init__(
            message=f"Agent '{agent_name}' timed out after {timeout}s.",
            error_code="AGENT_TIMEOUT",
            details={"agent_name": agent_name, "timeout_seconds": timeout},
        )


# ---------------------------------------------------------------------------
# Knowledge Graph Errors
# ---------------------------------------------------------------------------


class GraphError(PaperMindError):
    def __init__(self, operation: str, reason: str) -> None:
        super().__init__(
            message=f"Graph '{operation}' failed: {reason}",
            error_code="GRAPH_ERROR",
            details={"operation": operation, "reason": reason},
        )


# ---------------------------------------------------------------------------
# Configuration Errors
# ---------------------------------------------------------------------------


class ConfigurationError(PaperMindError):
    def __init__(self, field: str, reason: str) -> None:
        super().__init__(
            message=f"Configuration error for '{field}': {reason}",
            error_code="CONFIGURATION_ERROR",
            details={"field": field, "reason": reason},
        )
