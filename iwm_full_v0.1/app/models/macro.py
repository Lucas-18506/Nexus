"""Macro indicator ORM model."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class MacroIndicator(Base):
    """Macro economic indicator model."""

    __tablename__ = "macro_indicators"

    id: Mapped[int] = mapped_column(primary_key=True)
    indicator_name: Mapped[str] = mapped_column(String(255), nullable=False)
    indicator_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    current_value: Mapped[Optional[float]] = mapped_column(
        Numeric(20, 6), nullable=True
    )
    previous_value: Mapped[Optional[float]] = mapped_column(
        Numeric(20, 6), nullable=True
    )
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "indicator_name",
            "collected_at",
            name="uix_macro_indicator_name_collected_at",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<MacroIndicator(id={self.id}, "
            f"indicator_name='{self.indicator_name}', "
            f"current_value={self.current_value})>"
        )
