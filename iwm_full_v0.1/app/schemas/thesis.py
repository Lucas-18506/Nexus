"""Pydantic schemas for Thesis and ThesisEvidence models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ── Thesis Evidence Schemas ───────────────────────────────────

class ThesisEvidenceBase(BaseModel):
    """Base fields for ThesisEvidence schemas."""

    evidence_type: Optional[str] = Field(default=None, max_length=100)
    content: str
    source: Optional[str] = Field(default=None, max_length=500)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ThesisEvidenceCreate(ThesisEvidenceBase):
    """Schema for creating thesis evidence."""

    thesis_id: int


class ThesisEvidenceResponse(ThesisEvidenceBase):
    """Schema for thesis evidence API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    thesis_id: int
    created_at: datetime


# ── Thesis Schemas ────────────────────────────────────────────

class ThesisBase(BaseModel):
    """Base fields for Thesis schemas."""

    title: str = Field(..., max_length=500)
    description: str
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    status: str = Field(default="draft", max_length=50)
    owner: str = Field(default="system", max_length=100)
    source_type: Optional[str] = Field(default=None, max_length=100)
    related_industry: Optional[str] = Field(default=None, max_length=255)
    related_tickers: Optional[List[str]] = Field(default_factory=list)


class ThesisCreate(ThesisBase):
    """Schema for creating a thesis."""

    pass


class ThesisUpdate(BaseModel):
    """Schema for updating a thesis."""

    title: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = None
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    status: Optional[str] = Field(default=None, max_length=50)
    owner: Optional[str] = Field(default=None, max_length=100)
    source_type: Optional[str] = Field(default=None, max_length=100)
    related_industry: Optional[str] = Field(default=None, max_length=255)
    related_tickers: Optional[List[str]] = None


class ThesisResponse(ThesisBase):
    """Schema for thesis API response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    evidences: List[ThesisEvidenceResponse] = Field(default_factory=list)


class ThesisListResponse(BaseModel):
    """Schema for listing theses."""

    items: List[ThesisResponse]
    total: int
