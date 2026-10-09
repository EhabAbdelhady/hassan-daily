"""AI Provider Factory to easily switch between Gemini, OpenAI, and Anthropic."""

from typing import Optional
from .base import BaseAIProvider
from .providers.gemini_provider import GeminiProvider
from .providers.openai_provider import OpenAIProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.fallback_provider import FallbackAnalyticalProvider
from ..config import settings


def get_ai_provider(provider_name: Optional[str] = None) -> BaseAIProvider:
    """Instantiates and returns the configured AI provider."""
    name = (provider_name or settings.AI_PROVIDER).lower().strip()

    if name == "gemini":
        if settings.GEMINI_API_KEY:
            return GeminiProvider(api_key=settings.GEMINI_API_KEY)
        print("[AI Factory] Notice: GEMINI_API_KEY not set in .env. Using analytical grounded generator.")
        return FallbackAnalyticalProvider()

    elif name == "openai":
        if settings.OPENAI_API_KEY:
            return OpenAIProvider(api_key=settings.OPENAI_API_KEY)
        print("[AI Factory] Notice: OPENAI_API_KEY not set in .env. Using analytical grounded generator.")
        return FallbackAnalyticalProvider()

    elif name == "anthropic":
        if settings.ANTHROPIC_API_KEY:
            return AnthropicProvider(api_key=settings.ANTHROPIC_API_KEY)
        print("[AI Factory] Notice: ANTHROPIC_API_KEY not set in .env. Using analytical grounded generator.")
        return FallbackAnalyticalProvider()

    else:
        print(f"[AI Factory] Unknown provider '{name}'. Defaulting to analytical generator.")
        return FallbackAnalyticalProvider()
