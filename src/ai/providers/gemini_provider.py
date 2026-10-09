"""Gemini AI provider implementation."""

from typing import Optional

from google import genai
from google.genai import types

from ..base import BaseAIProvider, AIContentResponse

DEFAULT_MODEL = "gemini-3.8-flash"


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.model = model or DEFAULT_MODEL
        self.client = genai.Client(api_key=api_key)

    def generate_content(self, system_prompt: str, user_prompt: str) -> AIContentResponse:
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=AIContentResponse,
        )
        response = self.client.models.generate_content(model=self.model, contents=user_prompt, config=config)
        return AIContentResponse.model_validate_json(response.text)
