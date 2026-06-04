"""News and Event ORM models."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class News(Base):
    """News article model."""

    __tablename__ = "news"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    impact_level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extracted_events: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    related_tickers: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    related_industries: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    sentiment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<News(id={self.id}, title='{self.title[:50]}...')>"


class Event(Base):
    """Extracted event model."""

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    event_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    impact_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(nullable=True)
    related_industries: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    related_companies: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    related_macro: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, title='{self.title[:50]}...')>"
