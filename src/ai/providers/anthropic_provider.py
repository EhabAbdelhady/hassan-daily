"""Anthropic Claude provider implementation."""

import json
import re
from typing import Dict, Any, Optional, List
import anthropic

from ..base import BaseAIProvider, AIContentResponse
from ..prompts import build_prompts
from ...config import settings


class AnthropicProvider(BaseAIProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model
        self.client = anthropic.Anthropic(api_key=self.api_key) if self.api_key else None

    def generate_content(
        self,
        market_data: Dict[str, Any],
        headlines: Optional[List[str]] = None
    ) -> AIContentResponse:
        if not self.client:
            raise ValueError("ANTHROPIC_API_KEY is not configured.")

        system_prompt, user_prompt = build_prompts(market_data, headlines)

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        content_text = message.content[0].text
        # Extract JSON if enclosed in markdown blocks
        json_match = re.search(r"\{.*\}", content_text, re.DOTALL)
        if json_match:
            return AIContentResponse.model_validate_json(json_match.group(0))

        return AIContentResponse.model_validate_json(content_text)
