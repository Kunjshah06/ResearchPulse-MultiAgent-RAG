# =============================================================================
# PaperMind AI — Together / Azure / Ollama Provider Implementations
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


class TogetherProvider(BaseLLMProvider):
    """Together AI Provider."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.llm.together_api_key

    @property
    def provider_name(self) -> str:
        return "together"

    @property
    def default_model(self) -> str:
        return "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"

    @property
    def vision_model(self) -> str | None:
        return None

    async def complete(self, request: LLMRequest) -> LLMResponse:
        if not self._api_key:
            raise LLMProviderError(provider="together", reason="TOGETHER_API_KEY is not configured.")
        raise NotImplementedError("Together AI completion not initialized.")

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        raise NotImplementedError("Together AI stream not initialized.")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Together AI embedding not initialized.")


class AzureOpenAIProvider(BaseLLMProvider):
    """Azure OpenAI Service Provider."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.llm.azure_openai_api_key
        self._endpoint = settings.llm.azure_openai_endpoint
        self._deployment = settings.llm.azure_openai_deployment

    @property
    def provider_name(self) -> str:
        return "azure"

    @property
    def default_model(self) -> str:
        return self._deployment or "gpt-4o"

    @property
    def vision_model(self) -> str | None:
        return "gpt-4o"

    async def complete(self, request: LLMRequest) -> LLMResponse:
        if not self._api_key or not self._endpoint:
            raise LLMProviderError(provider="azure", reason="Azure OpenAI credentials are not configured.")
        raise NotImplementedError("Azure OpenAI completion not initialized.")

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        raise NotImplementedError("Azure OpenAI stream not initialized.")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Azure OpenAI embedding not initialized.")


class OllamaProvider(BaseLLMProvider):
    """Local Ollama Provider (OpenAI compatible endpoint)."""

    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = getattr(settings.llm, "ollama_base_url", "http://localhost:11434/v1")

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def default_model(self) -> str:
        return "llama3.1"

    @property
    def vision_model(self) -> str | None:
        return "llava"

    async def complete(self, request: LLMRequest) -> LLMResponse:
        t0 = time.perf_counter()
        model = request.model or self.default_model
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(base_url=self._base_url, api_key="ollama")
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
            client = AsyncOpenAI(base_url=self._base_url, api_key="ollama")
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
