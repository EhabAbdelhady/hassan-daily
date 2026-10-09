"""Base schemas and interface for AI text providers."""

from abc import ABC, abstractmethod
from typing import List, Literal

from pydantic import BaseModel, Field

Indicator = Literal["gold", "usd", "bitcoin", "brent"]


class ContentItem(BaseModel):
    text: str = Field(description="One Arabic bullet point (one or two sentences)")
    based_on: List[Indicator] = Field(
        description="Which of the provided indicators this point is derived from (at least one)"
    )


class AIContentResponse(BaseModel):
    """What the model writes. Sources, prices in the caption, and the disclaimer are added by code."""

    opportunities: List[ContentItem] = Field(description="Exactly 3 opportunities for real estate / investment")
    risks: List[ContentItem] = Field(description="Exactly 3 risks and their impact on real estate")
    tip_investment: str = Field(description="One-line Arabic investment tip of the day")
    tip_real_estate: str = Field(description="One-line Arabic real estate tip of the day")
    caption_summary: str = Field(
        description="2-4 Arabic sentences summarizing today's movement for the social caption, plus one question to the audience"
    )


class BaseAIProvider(ABC):
    @abstractmethod
    def generate_content(self, system_prompt: str, user_prompt: str) -> AIContentResponse:
        """Sends the prompts and returns the parsed structured response."""
