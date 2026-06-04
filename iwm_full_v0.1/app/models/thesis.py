"""Thesis and ThesisEvidence ORM models."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
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


class Thesis(Base):
    """Investment thesis model."""

    __tablename__ = "theses"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(
        Numeric(3, 2), default=0.5, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(50), default="draft", nullable=False
    )
    owner: Mapped[str] = mapped_column(
        String(100), default="system", nullable=False
    )
    source_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    related_industry: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    related_tickers: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
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
        return f"<Thesis(id={self.id}, title='{self.title[:50]}...', status='{self.status}')>"


class ThesisEvidence(Base):
    """Evidence supporting a thesis."""

    __tablename__ = "thesis_evidences"

    id: Mapped[int] = mapped_column(primary_key=True)
    thesis_id: Mapped[int] = mapped_column(
        ForeignKey("theses.id", ondelete="CASCADE"),
        nullable=False,
    )
    evidence_type: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    confidence: Mapped[float] = mapped_column(
        Numeric(3, 2), default=0.5, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<ThesisEvidence(id={self.id}, thesis_id={self.thesis_id}, evidence_type='{self.evidence_type}')>"
