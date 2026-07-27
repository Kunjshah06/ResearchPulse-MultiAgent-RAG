# =============================================================================
# PaperMind AI — Groq Provider Implementation
# =============================================================================

from __future__ import annotations

import time
from typing import AsyncIterator

from groq import AsyncGroq
from groq import RateLimitError as GroqRateLimitError

from papermind.core.config.settings import get_settings
from papermind.core.exceptions.errors import (
    LLMContextWindowError,
    LLMProviderError,
    LLMRateLimitError,
)
from papermind.core.logging.logger import get_logger
from papermind.services.llm.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMRequest,
    LLMResponse,
)

log = get_logger(__name__)


class GroqProvider(BaseLLMProvider):
    """
    Groq Cloud LLM provider.
    Uses the official groq Python SDK with async support.

    Supported models (as of 2025):
        - llama-3.3-70b-versatile
        - llama-3.1-8b-instant
        - mixtral-8x7b-32768
        - gemma2-9b-it
        - llama-3.2-90b-vision-preview  (multimodal)
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.llm.groq_api_key
        self._default_model = settings.llm.groq_default_model
        self._vision_model = settings.llm.groq_vision_model
        self._client: AsyncGroq | None = None

    def _get_client(self) -> AsyncGroq:
        if self._client is None:
            if not self._api_key:
                raise LLMProviderError(
                    provider="groq",
                    reason="GROQ_API_KEY is not configured. Please set your GROQ_API_KEY in .env.",
                )
            self._client = AsyncGroq(api_key=self._api_key)
        return self._client

    @property
    def provider_name(self) -> str:
        return "groq"

    @property
    def default_model(self) -> str:
        return self._default_model

    @property
    def vision_model(self) -> str | None:
        return self._vision_model

    def _build_messages(self, messages: list[LLMMessage]) -> list[dict]:
        return [
            {"role": m.role, "content": m.content, **({"name": m.name} if m.name else {})}
            for m in messages
        ]

    async def complete(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self._default_model
        t0 = time.perf_counter()

        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=model,
                messages=self._build_messages(request.messages),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stop=request.stop or None,
                stream=False,
            )
        except GroqRateLimitError as e:
            raise LLMRateLimitError(provider="groq") from e
        except Exception as e:
            msg = str(e)
            if "context_length" in msg or "too long" in msg.lower():
                raise LLMContextWindowError(
                    provider="groq",
                    token_count=request.max_tokens,
                    max_tokens=32768,
                ) from e
            raise LLMProviderError(provider="groq", reason=msg) from e

        latency_ms = (time.perf_counter() - t0) * 1000
        choice = response.choices[0]
        usage = response.usage

        log.debug(
            "Groq completion",
            model=model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            latency_ms=round(latency_ms, 1),
        )

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            provider="groq",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            latency_ms=latency_ms,
            finish_reason=choice.finish_reason or "stop",
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        model = request.model or self._default_model
        try:
            client = self._get_client()
            async with await client.chat.completions.create(
                model=model,
                messages=self._build_messages(request.messages),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            ) as stream_response:
                async for chunk in stream_response:
                    delta = chunk.choices[0].delta.content
                    if delta:
                        yield delta
        except GroqRateLimitError as e:
            raise LLMRateLimitError(provider="groq") from e
        except Exception as e:
            raise LLMProviderError(provider="groq", reason=str(e)) from e

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError(
            "Groq does not support embeddings. Use a dedicated embedding model."
        )
