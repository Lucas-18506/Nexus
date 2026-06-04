"""Pydantic schemas for Company model."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CompanyBase(BaseModel):
    """Base fields for Company schemas."""

    ticker: str = Field(..., max_length=50)
    market: str = Field(..., max_length=50)
    name: str = Field(..., max_length=255)
    industry_id: Optional[int] = None
    description: Optional[str] = None
    business_model: Optional[str] = None
    moat: Optional[str] = None
    risk_points: Optional[List[str]] = Field(default_factory=list)
    revenue_sources: Optional[List[str]] = Field(default_factory=list)
    cost_structure: Optional[str] = None
    customer_structure: Optional[str] = None
    competitive_position: Optional[str] = None


class CompanyCreate(CompanyBase):
    """Schema for creating a new company."""

    pass


class CompanyUpdate(BaseModel):
    """Schema for updating an existing company."""

    ticker: Optional[str] = Field(default=None, max_length=50)
    market: Optional[str] = Field(default=None, max_length=50)
    name: Optional[str] = Field(default=None, max_length=255)
    industry_id: Optional[int] = None
    description: Optional[str] = None
    business_model: Optional[str] = None
    moat: Optional[str] = None
    risk_points: Optional[List[str]] = None
    revenue_sources: Optional[List[str]] = None
    cost_structure: Optional[str] = None
    customer_structure: Optional[str] = None
    competitive_position: Optional[str] = None


class CompanyResponse(CompanyBase):
    """Schema for company API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class CompanyListResponse(BaseModel):
    """Schema for listing companies."""

    items: List[CompanyResponse]
    total: int
