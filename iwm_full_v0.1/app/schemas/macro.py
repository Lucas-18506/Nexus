"""Pydantic schemas for MacroIndicator model."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MacroIndicatorBase(BaseModel):
    """Base fields for MacroIndicator schemas."""

    indicator_name: str = Field(..., max_length=255)
    indicator_type: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    current_value: Optional[float] = None
    previous_value: Optional[float] = None
    unit: Optional[str] = Field(default=None, max_length=50)
    frequency: Optional[str] = Field(default=None, max_length=50)
    source: Optional[str] = Field(default=None, max_length=255)


class MacroIndicatorCreate(MacroIndicatorBase):
    """Schema for creating a macro indicator."""

    pass


class MacroIndicatorResponse(MacroIndicatorBase):
    """Schema for macro indicator API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    collected_at: datetime


class MacroIndicatorListResponse(BaseModel):
    """Schema for listing macro indicators."""

    items: List[MacroIndicatorResponse]
    total: int
