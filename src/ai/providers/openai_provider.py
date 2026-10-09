"""OpenAI provider implementation."""

import json
from typing import Dict, Any, Optional, List
from openai import OpenAI

from ..base import BaseAIProvider, AIContentResponse
from ..prompts import build_prompts
from ...config import settings


class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def generate_content(
        self,
        market_data: Dict[str, Any],
        headlines: Optional[List[str]] = None
    ) -> AIContentResponse:
        if not self.client:
            raise ValueError("OPENAI_API_KEY is not configured.")

        system_prompt, user_prompt = build_prompts(market_data, headlines)

        response = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format=AIContentResponse,
            temperature=0.3
        )

        return response.choices[0].message.parsed
