# =============================================================================
# PaperMind AI — Azure OpenAI Provider
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
