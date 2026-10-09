"""OpenAI provider implementation."""

from typing import Optional

from openai import OpenAI

from ..base import BaseAIProvider, AIContentResponse

DEFAULT_MODEL = "gpt-4o"


class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.model = model or DEFAULT_MODEL
        self.client = OpenAI(api_key=api_key)

    def generate_content(self, system_prompt: str, user_prompt: str) -> AIContentResponse:
        response = self.client.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format=AIContentResponse,
        )
        parsed = response.choices[0].message.parsed
        if parsed is None:
            raise RuntimeError(f"OpenAI returned no structured output: {response.choices[0].message.refusal}")
        return parsed
