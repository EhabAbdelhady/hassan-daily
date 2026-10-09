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
        # The rules go at the top of the prompt rather than in system_instruction:
        # on the free tier, newer models answer 503 "high demand" to requests using that field.
        contents = f"{system_prompt}\n\n---\n\n{user_prompt}"
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=AIContentResponse.model_json_schema(),
        )
        attempts = [(self.model, 0)] + [(self.model, w) for w in RETRY_WAITS]
        if self.model != BACKUP_MODEL:
            attempts.append((BACKUP_MODEL, 0))

        quota_used_up = False
        for i, (model, wait) in enumerate(attempts):
            if quota_used_up and model == self.model:
                continue  # retrying the same model can't help until the daily quota resets
            if wait:
                print(f"[Gemini] Busy, retrying in {wait}s...")
                time.sleep(wait)
            try:
                response = self.client.models.generate_content(model=model, contents=contents, config=config)
                if model != self.model:
                    print(f"[Gemini] Used backup model {model}")
                return AIContentResponse.model_validate_json(response.text)
            except errors.APIError as e:
                busy = e.code in (429, 500, 503)
                if not busy or i == len(attempts) - 1:
                    raise
                quota_used_up = quota_used_up or e.code == 429
                print(f"[Gemini] {model} unavailable ({e.code})")
