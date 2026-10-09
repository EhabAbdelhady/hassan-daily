"""Anthropic Claude provider implementation."""

from typing import Optional

import anthropic

from ..base import BaseAIProvider, AIContentResponse

DEFAULT_MODEL = "claude-opus-5-5"


class AnthropicProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.model = model or DEFAULT_MODEL
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate_content(self, system_prompt: str, user_prompt: str) -> AIContentResponse:
        response = self.client.beta.messages.parse(
            model=self.model,
            max_tokens=16000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
            output_format=AIContentResponse,
            # If a request is ever declined by a safety classifier, retry it on Anthropic's recommended fallback model
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
        if response.stop_reason == "refusal":
            raise RuntimeError(f"Claude declined the request: {response.stop_details}")
        if response.parsed_output is None:
            raise RuntimeError(f"Claude returned no structured output (stop_reason={response.stop_reason})")
        return response.parsed_output
