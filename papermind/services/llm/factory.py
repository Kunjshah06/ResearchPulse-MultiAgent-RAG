# =============================================================================
# PaperMind AI — LLM Provider Factory
# =============================================================================
# Returns the correct provider based on the LLM_PROVIDER env setting.
# This is the ONLY place in the codebase where provider names are mapped
# to concrete classes. Everywhere else uses BaseLLMProvider.
# =============================================================================

from __future__ import annotations

from functools import lru_cache

from papermind.core.config.settings import get_settings
from papermind.core.exceptions.errors import ConfigurationError
from papermind.services.llm.base import BaseLLMProvider


def create_llm_provider(provider: str | None = None) -> BaseLLMProvider:
    """
    Factory function. Returns an instance of the requested provider.

    Args:
        provider: Override the env setting. Pass None to use LLM_PROVIDER env var.

    Returns:
        An instance of BaseLLMProvider.

    Raises:
        ConfigurationError: If provider name is unknown or API key is missing.
    """
    settings = get_settings()
    provider_name = (provider or settings.llm.provider).lower()

    if provider_name == "groq":
        from papermind.services.llm.providers.groq_provider import GroqProvider
        return GroqProvider()

    elif provider_name == "openai":
        from papermind.services.llm.providers.openai_provider import OpenAIProvider
        return OpenAIProvider()

    elif provider_name == "anthropic":
        from papermind.services.llm.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider()

    elif provider_name == "google":
        from papermind.services.llm.providers.google_provider import GoogleProvider
        return GoogleProvider()

    elif provider_name == "together":
        from papermind.services.llm.providers.together_provider import TogetherProvider
        return TogetherProvider()

    elif provider_name == "azure":
        from papermind.services.llm.providers.azure_provider import AzureOpenAIProvider
        return AzureOpenAIProvider()

    elif provider_name == "ollama":
        from papermind.services.llm.providers.ollama_provider import OllamaProvider
        return OllamaProvider()

    else:
        raise ConfigurationError(
            field="LLM_PROVIDER",
            reason=f"Unknown provider '{provider_name}'. "
                   f"Valid options: groq, openai, anthropic, google, together, azure, ollama",
        )


@lru_cache(maxsize=1)
def get_default_llm_provider() -> BaseLLMProvider:
    """
    Returns a cached singleton of the default provider.
    Use for FastAPI dependency injection.
    """
    return create_llm_provider()
