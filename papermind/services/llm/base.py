# =============================================================================
# PaperMind AI — LLM Provider Abstraction Layer
# =============================================================================
# This module defines the abstract interface for all LLM providers.
# The rest of the system ONLY depends on this interface — never on Groq or
# OpenAI directly. Swapping providers = changing one config value.
# =============================================================================

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


@dataclass
class LLMMessage:
    """A single message in a conversation."""

    role: str           # "system" | "user" | "assistant"
    content: str
    name: str | None = None


@dataclass
class LLMRequest:
    """A request to an LLM provider."""

    messages: list[LLMMessage]
    model: str | None = None                # None → use provider default
    temperature: float = 0.1               # low temp for factual RAG
    max_tokens: int = 2048
    top_p: float = 1.0
    stream: bool = False
    stop: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """A response from an LLM provider."""

    content: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    finish_reason: str = "stop"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMUsage:
    """Token usage tracking."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class BaseLLMProvider(ABC):
    """
    Abstract base class for all LLM providers.

    Implementations:
        - GroqProvider         (groq SDK)
        - OpenAIProvider       (openai SDK)
        - AnthropicProvider    (anthropic SDK)
        - GoogleProvider       (google-generativeai)
        - TogetherProvider     (together SDK)
        - AzureOpenAIProvider  (openai SDK with azure endpoint)
        - OllamaProvider       (openai-compatible local endpoint)

    All implementations must be stateless (no mutable class-level state).
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Unique provider identifier, e.g. 'groq', 'openai'."""

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model name for this provider."""

    @property
    @abstractmethod
    def vision_model(self) -> str | None:
        """Vision-capable model, or None if provider lacks multimodal support."""

    @abstractmethod
    async def complete(self, request: LLMRequest) -> LLMResponse:
        """
        Send a chat completion request and return the full response.

        Args:
            request: The LLMRequest containing messages and parameters.

        Returns:
            LLMResponse with the generated content and usage stats.

        Raises:
            LLMProviderError: On any provider-side error.
            LLMRateLimitError: When rate limits are exceeded.
            LLMContextWindowError: When input exceeds model context.
        """

    @abstractmethod
    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        """
        Stream a chat completion response token by token.

        Args:
            request: The LLMRequest with stream=True.

        Yields:
            String chunks as they arrive from the provider.
        """

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings (only for providers that support it).

        Args:
            texts: A list of strings to embed.

        Returns:
            A list of float vectors, one per input text.

        Note:
            Not all providers support embedding. Raise NotImplementedError if unsupported.
        """

    async def health_check(self) -> bool:
        """Check provider connectivity. Returns True if healthy."""
        try:
            test_request = LLMRequest(
                messages=[LLMMessage(role="user", content="Say 'ok'")],
                max_tokens=5,
            )
            response = await self.complete(test_request)
            return bool(response.content)
        except Exception:
            return False

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count.
        Override in subclasses for provider-accurate counting.
        Default: rough approximation (1 token ≈ 4 chars).
        """
        return len(text) // 4
