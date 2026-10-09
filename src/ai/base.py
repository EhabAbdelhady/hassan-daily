"""Base schemas and interface for AI text providers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class ContentItem(BaseModel):
    text: str = Field(description="Arabic bullet point text")
    source: str = Field(description="Arabic attribution source tag e.g. (المصدر: Reuters | أكتوبر 2026)")


class AIContentResponse(BaseModel):
    opportunities: List[ContentItem] = Field(description="3 key real estate and investment opportunities")
    risks: List[ContentItem] = Field(description="3 key market risks and real estate impact")
    tip_investment: str = Field(description="Concise Arabic investment tip of the day")
    tip_real_estate: str = Field(description="Concise Arabic real estate tip of the day")
    social_caption: str = Field(description="Engaging Arabic social media caption for Facebook & Instagram")
    disclaimer: str = Field(
        default="تنويه: المحتوى للأغراض المعرفية والتثقيفية فقط، ولا يُعد بأي شكل نصيحة استثمارية أو مالية.",
        description="Mandatory regulatory disclaimer"
    )


class BaseAIProvider(ABC):
    @abstractmethod
    def generate_content(
        self,
        market_data: Dict[str, Any],
        headlines: Optional[List[str]] = None
    ) -> AIContentResponse:
        """Generates structured market commentary, tips, and captions in Arabic."""
        pass
