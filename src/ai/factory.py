"""AI Provider Factory to switch between Gemini, OpenAI, and Anthropic."""

from typing import Optional

from .base import BaseAIProvider
from ..config import settings


def get_ai_provider(provider_name: Optional[str] = None) -> BaseAIProvider:
    """Returns the configured AI provider. Raises if its API key is missing (no canned fallback text)."""
    name = (provider_name or settings.AI_PROVIDER).lower().strip()
    model = settings.AI_MODEL or None

    if name == "anthropic":
        from .providers.anthropic_provider import AnthropicProvider
        key, provider_cls = settings.ANTHROPIC_API_KEY, AnthropicProvider
    elif name == "openai":
        from .providers.openai_provider import OpenAIProvider
        key, provider_cls = settings.OPENAI_API_KEY, OpenAIProvider
    elif name == "gemini":
        from .providers.gemini_provider import GeminiProvider
        key, provider_cls = settings.GEMINI_API_KEY, GeminiProvider
    else:
        raise ValueError(f"Unknown AI_PROVIDER '{name}'. Use anthropic, openai, or gemini.")

    if not key:
        raise ValueError(f"AI_PROVIDER is '{name}' but its API key is not set.")
    return provider_cls(api_key=key, model=model)
