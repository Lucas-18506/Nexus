"""Pydantic schemas for Opportunity model."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class OpportunityBase(BaseModel):
    """Base fields for Opportunity schemas."""

    title: str = Field(..., max_length=500)
    theme: Optional[str] = Field(default=None, max_length=255)
    industry: Optional[str] = Field(default=None, max_length=255)
    catalyst: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    opportunity_score: int = Field(default=0, ge=0, le=100)
    risk_score: int = Field(default=50, ge=0, le=100)
    stage: str = Field(default="discovery", max_length=50)
    related_thesis_id: Optional[int] = None
    related_tickers: Optional[List[str]] = Field(default_factory=list)
    analysis_summary: Optional[str] = None


class OpportunityCreate(OpportunityBase):
    """Schema for creating an opportunity."""

    pass


class OpportunityUpdate(BaseModel):
    """Schema for updating an opportunity."""

    title: Optional[str] = Field(default=None, max_length=500)
    theme: Optional[str] = Field(default=None, max_length=255)
    industry: Optional[str] = Field(default=None, max_length=255)
    catalyst: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    opportunity_score: Optional[int] = Field(default=None, ge=0, le=100)
    risk_score: Optional[int] = Field(default=None, ge=0, le=100)
    stage: Optional[str] = Field(default=None, max_length=50)
    related_thesis_id: Optional[int] = None
    related_tickers: Optional[List[str]] = None
    analysis_summary: Optional[str] = None


class OpportunityResponse(OpportunityBase):
    """Schema for opportunity API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class OpportunityListResponse(BaseModel):
    """Schema for listing opportunities."""

    items: List[OpportunityResponse]
    total: int
