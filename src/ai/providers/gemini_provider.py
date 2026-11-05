"""Gemini AI provider implementation."""

import time
from typing import List, Optional, Tuple

from google import genai
from google.genai import errors, types

from ..base import BaseAIProvider, AIContentResponse

DEFAULT_MODEL = "gemini-3.8-flash"
# The free tier often answers 503 "high demand" for the larger models while the lite models still
# work (seen on 2026-11-05), so walk down this list. A quota error (429) skips to the next model.
FALLBACK_MODELS = ["gemini-3.7-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
LITE_MODELS = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite"]
PASS_WAIT = 90  # seconds between full passes when every model is busy
PASSES = 3      # worst case about 3 minutes of waiting before the run gives up (the next start retries)


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str, model: Optional[str] = None):
        self.model = model or DEFAULT_MODEL
        self.client = genai.Client(api_key=api_key)

    def _attempts(self) -> List[Tuple[int, str]]:
        """(pass number, model) in order: pass 1 tries every model, later passes only the main and lite ones."""
        first = [self.model] + [m for m in FALLBACK_MODELS if m != self.model]
        later = [self.model] + [m for m in LITE_MODELS if m != self.model]
        return [(1, m) for m in first] + [(n, m) for n in range(2, PASSES + 1) for m in later]

    def generate_content(self, system_prompt: str, user_prompt: str) -> AIContentResponse:
        # The rules go at the top of the prompt rather than in system_instruction:
        # on the free tier, newer models answer 503 "high demand" to requests using that field.
        contents = f"{system_prompt}\n\n---\n\n{user_prompt}"
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=AIContentResponse.model_json_schema(),
        )

        quota_used_up = set()
        last_error: Optional[errors.APIError] = None
        current_pass = 1
        for n, model in self._attempts():
            if model in quota_used_up:
                continue  # its daily quota won't reset during this run
            if n != current_pass:
                current_pass = n
                print(f"[Gemini] Every model is busy, waiting {PASS_WAIT}s before trying again (pass {n}/{PASSES})...")
                time.sleep(PASS_WAIT)
            try:
                response = self.client.models.generate_content(model=model, contents=contents, config=config)
                if model != self.model:
                    print(f"[Gemini] Used backup model {model}")
                return AIContentResponse.model_validate_json(response.text)
            except errors.APIError as e:
                if e.code not in (429, 500, 503):
                    raise
                if e.code == 429:
                    quota_used_up.add(model)
                last_error = e
                print(f"[Gemini] {model} unavailable ({e.code})")
        raise last_error
