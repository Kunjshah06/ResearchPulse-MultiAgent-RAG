# =============================================================================
# PaperMind AI — Anthropic Provider Implementation
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


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API Provider (claude-3-5-sonnet, claude-3-haiku)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.llm.anthropic_api_key
        self._client = None

    def _get_client(self):
        if self._client is None:
            if not self._api_key:
                raise LLMProviderError(
                    provider="anthropic",
                    reason="ANTHROPIC_API_KEY is not configured. Please set your ANTHROPIC_API_KEY in .env.",
                )
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self._api_key)
        return self._client

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"

    @property
    def vision_model(self) -> str | None:
        return "claude-3-5-sonnet-20241022"

    async def complete(self, request: LLMRequest) -> LLMResponse:
        model = request.model or self.default_model
        t0 = time.perf_counter()
        client = self._get_client()

        system_prompt = ""
        user_msgs = []
        for m in request.messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                user_msgs.append({"role": m.role, "content": m.content})

        try:
            kwargs = {
                "model": model,
                "messages": user_msgs,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            response = await client.messages.create(**kwargs)
        except Exception as e:
            raise LLMProviderError(provider="anthropic", reason=str(e)) from e

        latency_ms = (time.perf_counter() - t0) * 1000
        content = "".join([block.text for block in response.content if hasattr(block, "text")])

        return LLMResponse(
            content=content,
            model=response.model,
            provider="anthropic",
            prompt_tokens=response.usage.input_tokens if response.usage else 0,
            completion_tokens=response.usage.output_tokens if response.usage else 0,
            total_tokens=(response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
            latency_ms=latency_ms,
        )

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        model = request.model or self.default_model
        client = self._get_client()

        system_prompt = ""
        user_msgs = []
        for m in request.messages:
            if m.role == "system":
                system_prompt = m.content
            else:
                user_msgs.append({"role": m.role, "content": m.content})

        try:
            kwargs = {
                "model": model,
                "messages": user_msgs,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            }
            if system_prompt:
                kwargs["system"] = system_prompt

            async with client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            raise LLMProviderError(provider="anthropic", reason=str(e)) from e

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Anthropic does not support embeddings.")
