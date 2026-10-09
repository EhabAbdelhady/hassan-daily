"""Gemini AI provider implementation."""

import time
from typing import Optional

from google import genai
from google.genai import errors, types

from ..base import BaseAIProvider, AIContentResponse

DEFAULT_MODEL = "gemini-3.8-flash"
# Free tier sometimes answers 503 "high demand"; the lighter model is usually still available
BACKUP_MODEL = "gemini-3.5-flash-lite"
RETRY_WAITS = (30, 90)  # seconds to wait before each retry on the main model


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
        attempts = [(self.model, 0)] + [(self.model, w) for w in RETRY_WAITS]
        if self.model != BACKUP_MODEL:
            attempts.append((BACKUP_MODEL, 0))

        for i, (model, wait) in enumerate(attempts):
            if wait:
                print(f"[Gemini] Busy, retrying in {wait}s...")
                time.sleep(wait)
            try:
                response = self.client.models.generate_content(model=model, contents=user_prompt, config=config)
                if model != self.model:
                    print(f"[Gemini] Used backup model {model}")
                return AIContentResponse.model_validate_json(response.text)
            except errors.APIError as e:
                busy = e.code in (429, 500, 503)
                if not busy or i == len(attempts) - 1:
                    raise
                print(f"[Gemini] {model} unavailable ({e.code})")
