# =============================================================================
# PaperMind AI — LLM Factory & Provider Unit Tests
# =============================================================================

from __future__ import annotations

import pytest

from papermind.core.exceptions.errors import ConfigurationError
from papermind.services.llm.base import BaseLLMProvider
from papermind.services.llm.factory import create_llm_provider, get_default_llm_provider


def test_create_groq_provider_succeeds_without_api_key():
    provider = create_llm_provider("groq")
    assert isinstance(provider, BaseLLMProvider)
    assert provider.provider_name == "groq"


def test_create_openai_provider_succeeds():
    provider = create_llm_provider("openai")
    assert isinstance(provider, BaseLLMProvider)
    assert provider.provider_name == "openai"


def test_invalid_provider_raises_error():
    with pytest.raises(ConfigurationError):
        create_llm_provider("invalid_provider_name")


def test_get_default_llm_provider():
    provider = get_default_llm_provider()
    assert isinstance(provider, BaseLLMProvider)
