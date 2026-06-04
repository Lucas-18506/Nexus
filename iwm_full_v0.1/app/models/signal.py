from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Integer, Float, DateTime, Enum as SQLEnum, Text, Boolean, select, desc, and_
from sqlalchemy.orm import Mapped, mapped_column
import enum

from app.models.base import Base


class SignalAction(str, enum.Enum):
    """交易信号操作类型"""
    OPEN = "open"           # 建仓
    ADD = "add"             # 加仓
    REDUCE = "reduce"       # 减仓
    CLOSE = "close"         # 清仓
    HOLD = "hold"           # 持仓


class SignalStatus(str, enum.Enum):
    """信号状态"""
    ACTIVE = "active"       # 待处理
    DISMISSED = "dismissed" # 已忽略
    EXECUTED = "executed"   # 已执行


class Signal(Base):
    """交易信号模型 - 最小化版本"""
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    market: Mapped[str] = mapped_column(String(8), nullable=False, default="US")
    action: Mapped[str] = mapped_column(String(16), nullable=False)  # SignalAction
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    confidence: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    source: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="active")  # SignalStatus
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Signal {self.symbol} {self.action} {self.confidence}%>"
