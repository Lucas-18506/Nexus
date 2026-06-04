"""Pydantic schemas for News and Event models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── News Schemas ──────────────────────────────────────────────

class NewsBase(BaseModel):
    """Base fields for News schemas."""

    title: str = Field(..., max_length=500)
    content: Optional[str] = None
    source: Optional[str] = Field(default=None, max_length=255)
    url: Optional[str] = Field(default=None, max_length=2048)
    published_at: Optional[datetime] = None
    category: Optional[str] = Field(default=None, max_length=100)
    impact_level: int = Field(default=0, ge=0, le=10)
    extracted_events: Optional[List[str]] = Field(default_factory=list)
    related_tickers: Optional[List[str]] = Field(default_factory=list)
    related_industries: Optional[List[str]] = Field(default_factory=list)
    sentiment: Optional[str] = Field(default=None, max_length=50)
    processed: bool = False


class NewsCreate(NewsBase):
    """Schema for creating a news article."""

    pass


class NewsResponse(NewsBase):
    """Schema for news API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    collected_at: datetime


class NewsListResponse(BaseModel):
    """Schema for listing news articles."""

    items: List[NewsResponse]
    total: int


# ── Event Schemas ─────────────────────────────────────────────

class EventBase(BaseModel):
    """Base fields for Event schemas."""

    title: str = Field(..., max_length=500)
    summary: Optional[str] = None
    event_type: Optional[str] = Field(default=None, max_length=100)
    event_date: Optional[datetime] = None
    source: Optional[str] = Field(default=None, max_length=255)
    impact_level: Optional[int] = Field(default=None, ge=0, le=10)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    related_industries: Optional[List[str]] = Field(default_factory=list)
    related_companies: Optional[List[str]] = Field(default_factory=list)
    related_macro: Optional[List[str]] = Field(default_factory=list)


class EventCreate(EventBase):
    """Schema for creating an event."""

    pass


class EventResponse(EventBase):
    """Schema for event API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class EventListResponse(BaseModel):
    """Schema for listing events."""

    items: List[EventResponse]
    total: int
