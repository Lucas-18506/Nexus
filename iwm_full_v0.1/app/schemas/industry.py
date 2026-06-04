"""Pydantic schemas for Industry model."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class IndustryBase(BaseModel):
    """Base fields for Industry schemas."""

    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    lifecycle_stage: Optional[str] = Field(default=None, max_length=100)
    growth_rate: Optional[str] = Field(default=None, max_length=100)
    market_size: Optional[str] = Field(default=None, max_length=255)
    key_drivers: Optional[List[str]] = Field(default_factory=list)
    supply_chain: Optional[str] = None
    bottleneck: Optional[str] = None
    prosperity_indicators: Optional[List[str]] = Field(default_factory=list)
    risk_factors: Optional[List[str]] = Field(default_factory=list)
    opportunities: Optional[List[str]] = Field(default_factory=list)


class IndustryCreate(IndustryBase):
    """Schema for creating a new industry."""

    pass


class IndustryUpdate(BaseModel):
    """Schema for updating an existing industry."""

    name: Optional[str] = Field(default=None, max_length=255)
    description: Optional[str] = None
    lifecycle_stage: Optional[str] = Field(default=None, max_length=100)
    growth_rate: Optional[str] = Field(default=None, max_length=100)
    market_size: Optional[str] = Field(default=None, max_length=255)
    key_drivers: Optional[List[str]] = None
    supply_chain: Optional[str] = None
    bottleneck: Optional[str] = None
    prosperity_indicators: Optional[List[str]] = None
    risk_factors: Optional[List[str]] = None
    opportunities: Optional[List[str]] = None


class IndustryResponse(IndustryBase):
    """Schema for industry API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class IndustryListResponse(BaseModel):
    """Schema for listing industries."""

    items: List[IndustryResponse]
    total: int
