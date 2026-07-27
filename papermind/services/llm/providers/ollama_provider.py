# =============================================================================
# PaperMind AI — Ollama Provider
# =============================================================================

from __future__ import annotations

import time
from typing import AsyncIterator

from papermind.core.config.settings import get_settings
from papermind.core.exceptions.errors import LLMProviderError
from papermind.services.llm.base import (
    BaseLLMProvider,
    LLMRequest,
    LLMResponse,
)


class OllamaProvider(BaseLLMProvider):
    """Local Ollama Provider (OpenAI compatible endpoint)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.llm.ollama_base_url
        self._default_model = settings.llm.ollama_default_model

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def default_model(self) -> str:
        return self._default_model

    @property
    def vision_model(self) -> str | None:
        return "llava"

    async def complete(self, request: LLMRequest) -> LLMResponse:
        t0 = time.perf_counter()
        model = request.model or self.default_model
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(base_url=self._base_url, api_key="ollama", timeout=120.0)
            messages = [{"role": m.role, "content": m.content} for m in request.messages]
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            latency_ms = (time.perf_counter() - t0) * 1000
            choice = response.choices[0]
            return LLMResponse(
                content=choice.message.content or "",
                model=model,
                provider="ollama",
                latency_ms=latency_ms,
            )
        except Exception as e:
            raise LLMProviderError(provider="ollama", reason=str(e)) from e

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        model = request.model or self.default_model
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(base_url=self._base_url, api_key="ollama", timeout=120.0)
            messages = [{"role": m.role, "content": m.content} for m in request.messages]
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            )
            async for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            raise LLMProviderError(provider="ollama", reason=str(e)) from e

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Ollama embedding not initialized.")
