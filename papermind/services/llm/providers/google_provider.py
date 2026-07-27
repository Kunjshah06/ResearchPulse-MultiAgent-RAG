# =============================================================================
# PaperMind AI — Google Gemini Provider Implementation
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


class GoogleProvider(BaseLLMProvider):
    """Google Gemini LLM Provider."""

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.llm.google_api_key

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def default_model(self) -> str:
        return "gemini-1.5-pro"

    @property
    def vision_model(self) -> str | None:
        return "gemini-1.5-pro"

    async def complete(self, request: LLMRequest) -> LLMResponse:
        if not self._api_key:
            raise LLMProviderError(
                provider="google",
                reason="GOOGLE_API_KEY is not configured. Please set your GOOGLE_API_KEY in .env.",
            )
        model_name = request.model or self.default_model
        t0 = time.perf_counter()

        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            model = genai.GenerativeModel(model_name)
            
            prompt = "\n".join([f"{m.role}: {m.content}" for m in request.messages])
            response = await model.generate_content_async(prompt)
            
            latency_ms = (time.perf_counter() - t0) * 1000
            return LLMResponse(
                content=response.text or "",
                model=model_name,
                provider="google",
                latency_ms=latency_ms,
            )
        except Exception as e:
            raise LLMProviderError(provider="google", reason=str(e)) from e

    async def stream(self, request: LLMRequest) -> AsyncIterator[str]:
        if not self._api_key:
            raise LLMProviderError(
                provider="google",
                reason="GOOGLE_API_KEY is not configured. Please set your GOOGLE_API_KEY in .env.",
            )
        model_name = request.model or self.default_model
        try:
            import google.generativeai as genai
            genai.configure(api_key=self._api_key)
            model = genai.GenerativeModel(model_name)
            prompt = "\n".join([f"{m.role}: {m.content}" for m in request.messages])
            response = await model.generate_content_async(prompt, stream=True)
            async for chunk in response:
                yield chunk.text
        except Exception as e:
            raise LLMProviderError(provider="google", reason=str(e)) from e

    async def embed(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError("Google embedding not configured.")
