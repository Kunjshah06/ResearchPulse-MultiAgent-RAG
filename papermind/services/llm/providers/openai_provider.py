# =============================================================================
# PaperMind AI — OpenAI Provider Implementation
# =============================================================================

from __future__ import annotations

import time
from typing import AsyncIterator

from papermind.core.config.settings import get_settings
from papermind.core.exceptions.errors import LLMProviderError
from papermind.services.llm.base import (
    BaseLLMProvider,
    LLMMessage,
    LLMRequest,
    LLMResponse,
)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API Provider (gpt-4o, gpt-4o-mini)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.llm.openai_api_key
        self._default_model = settings.llm.openai_default_model
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise LLMProviderError(
                    provider="openai",
                    reason="OPENAI_API_KEY is not configured. Please set your OPENAI_API_KEY in .env.",
                )
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self._api_key)
        return self._client

    @property
    def provider_name(self) -> str:
        return "openai"

    @property
    def default_model(self) -> str:
        return self._default_model or "gpt-4o-mini"

    @property
    def vision_model(self) -> str | None:
        return "gpt-4o"

    def _build_messages(self, messages: list[LLMMessage]) -> list[dict]:
        return [
            {"role": m.role, "content": m.content, **({"name": m.name} if m.name else {})}
            for m in messages
        ]

    async def complete(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.default_model
        t0 = time.perf_counter()
        client = self._get_client()

        try:
            response = await client.chat.completions.create(
                model=model,
                messages=self._build_messages(request.messages),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stop=request.stop or None,
                stream=False,
            )
        except Exception as e:
            raise LLMProviderError(provider="openai", reason=str(e)) from e

        latency_ms = (time.perf_counter() - t0) * 1000
        choice = response.choices[0]
        usage = response.usage

        return LLMResponse(
            content=choice.message.content or "",
            model=response.model,
            provider="openai",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
            latency_ms=latency_ms,
            finish_reason=choice.finish_reason or "stop",
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        model = request.model or self.default_model
        client = self._get_client()
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=self._build_messages(request.messages),
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                stream=True,
            )
            async for chunk in response:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            raise LLMProviderError(provider="openai", reason=str(e)) from e

    async def embed(self, texts: list[str]) -> list[list[float]]:
        client = self._get_client()
        try:
            res = await client.embeddings.create(input=texts, model="text-embedding-3-small")
            return [data.embedding for data in res.data]
        except Exception as e:
            raise LLMProviderError(provider="openai", reason=str(e)) from e
