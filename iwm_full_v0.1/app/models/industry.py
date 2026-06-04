"""Industry ORM model."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def now_utc() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Industry(Base):
    """Industry analysis model."""

    __tablename__ = "industries"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lifecycle_stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    growth_rate: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    market_size: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    key_drivers: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    supply_chain: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bottleneck: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prosperity_indicators: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    risk_factors: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    opportunities: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list
    )
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Industry(id={self.id}, name='{self.name}')>"
