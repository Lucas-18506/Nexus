"""Pydantic schemas for API request/response models."""

from app.schemas.company import (
    CompanyCreate,
    CompanyListResponse,
    CompanyResponse,
    CompanyUpdate,
)
from app.schemas.industry import (
    IndustryCreate,
    IndustryListResponse,
    IndustryResponse,
    IndustryUpdate,
)
from app.schemas.macro import (
    MacroIndicatorCreate,
    MacroIndicatorListResponse,
    MacroIndicatorResponse,
)
from app.schemas.news import (
    EventCreate,
    EventListResponse,
    EventResponse,
    NewsCreate,
    NewsListResponse,
    NewsResponse,
)
from app.schemas.opportunity import (
    OpportunityCreate,
    OpportunityListResponse,
    OpportunityResponse,
    OpportunityUpdate,
)
from app.schemas.report import (
    ReportCreate,
    ReportListResponse,
    ReportResponse,
)
from app.schemas.thesis import (
    ThesisCreate,
    ThesisEvidenceCreate,
    ThesisEvidenceResponse,
    ThesisListResponse,
    ThesisResponse,
    ThesisUpdate,
)

__all__ = [
    # Industry
    "IndustryCreate",
    "IndustryUpdate",
    "IndustryResponse",
    "IndustryListResponse",
    # Company
    "CompanyCreate",
    "CompanyUpdate",
    "CompanyResponse",
    "CompanyListResponse",
    # News & Event
    "NewsCreate",
    "NewsResponse",
    "NewsListResponse",
    "EventCreate",
    "EventResponse",
    "EventListResponse",
    # Macro
    "MacroIndicatorCreate",
    "MacroIndicatorResponse",
    "MacroIndicatorListResponse",
    # Thesis
    "ThesisCreate",
    "ThesisUpdate",
    "ThesisResponse",
    "ThesisListResponse",
    "ThesisEvidenceCreate",
    "ThesisEvidenceResponse",
    # Opportunity
    "OpportunityCreate",
    "OpportunityUpdate",
    "OpportunityResponse",
    "OpportunityListResponse",
    # Report
    "ReportCreate",
    "ReportResponse",
    "ReportListResponse",
]
