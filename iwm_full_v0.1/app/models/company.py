"""Company ORM model."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Company(Base):
    """Company analysis model."""

    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(50), nullable=False)
    market: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("industries.id", ondelete="SET NULL"),
        nullable=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    business_model: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    moat: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    risk_points: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    revenue_sources: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    cost_structure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    customer_structure: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    competitive_position: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("ticker", "market", name="uix_company_ticker_market"),
    )

    def __repr__(self) -> str:
        return f"<Company(id={self.id}, ticker='{self.ticker}', market='{self.market}')>"
