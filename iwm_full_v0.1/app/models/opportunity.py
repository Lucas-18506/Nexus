"""Opportunity ORM model."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Opportunity(Base):
    """Investment opportunity model."""

    __tablename__ = "opportunities"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    theme: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    catalyst: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(
        Numeric(3, 2), default=0.5, nullable=False
    )
    opportunity_score: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False
    )
    risk_score: Mapped[int] = mapped_column(
        Integer, default=50, nullable=False
    )
    stage: Mapped[str] = mapped_column(
        String(50), default="discovery", nullable=False
    )
    related_thesis_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("theses.id", ondelete="SET NULL"),
        nullable=True,
    )
    related_tickers: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    analysis_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Opportunity(id={self.id}, "
            f"title='{self.title[:50]}...', "
            f"stage='{self.stage}')>"
        )
