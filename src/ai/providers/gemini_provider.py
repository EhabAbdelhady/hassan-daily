"""Gemini AI provider implementation."""

import json
from typing import Dict, Any, Optional, List
from google import genai
from google.genai import types

from ..base import BaseAIProvider, AIContentResponse
from ..prompts import build_prompts
from ...config import settings


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def generate_content(
        self,
        market_data: Dict[str, Any],
        headlines: Optional[List[str]] = None
    ) -> AIContentResponse:
        if not self.client:
            raise ValueError("GEMINI_API_KEY is not configured.")

        system_prompt, user_prompt = build_prompts(market_data, headlines)

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=AIContentResponse,
            temperature=0.3,
        )

        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=config
        )

        return AIContentResponse.model_validate_json(response.text)
