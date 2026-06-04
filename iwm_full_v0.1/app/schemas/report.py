"""Pydantic schemas for Report model."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ReportBase(BaseModel):
    """Base fields for Report schemas."""

    report_type: str = Field(..., max_length=100)
    title: str = Field(..., max_length=500)
    content: str
    summary: Optional[str] = None
    key_points: Optional[List[str]] = Field(default_factory=list)
    related_tickers: Optional[List[str]] = Field(default_factory=list)
    related_industries: Optional[List[str]] = Field(default_factory=list)
    confidence_overall: float = Field(default=0.5, ge=0.0, le=1.0)


class ReportCreate(ReportBase):
    """Schema for creating a report."""

    pass


class ReportResponse(ReportBase):
    """Schema for report API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ReportListResponse(BaseModel):
    """Schema for listing reports."""

    items: List[ReportResponse]
    total: int
