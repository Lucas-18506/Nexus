"""Report ORM model."""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Report(Base):
    """Generated report model."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_type: Mapped[str] = mapped_column(String(100), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    key_points: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    related_tickers: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    related_industries: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    confidence_overall: Mapped[float] = mapped_column(
        Numeric(3, 2), default=0.5, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return (
            f"<Report(id={self.id}, "
            f"report_type='{self.report_type}', "
            f"title='{self.title[:50]}...')>"
        )
