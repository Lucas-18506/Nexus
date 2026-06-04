"""Portfolio and Watchlist ORM models.

持仓管理模块数据模型：
- Position: 实际持仓记录（含成本、数量、盈亏计算）
- PositionTransaction: 持仓交易流水（买入/卖出/分红/拆股）
- WatchlistItem: 观察仓记录
"""

from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Date, Boolean,
    ForeignKey, Index, Numeric, Text, Enum, func, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class Position(Base):
    """持仓记录 - 一个标的的一条记录（支持同一标的多笔合并显示）"""

    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(50), nullable=False)
    market: Mapped[str] = mapped_column(String(10), nullable=False)  # US, HK, CN
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_cn: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 持仓核心数据
    quantity: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)
    avg_cost: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")

    # 实时价格（由外部行情服务更新）
    current_price: Mapped[Optional[float]] = mapped_column(Numeric(18, 8), nullable=True)
    current_price_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 分类与状态
    sector: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position_type: Mapped[str] = mapped_column(
        String(20), default="long", nullable=False
    )  # long / short / option_call / option_put
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False
    )  # active / closed / suspended

    # 关联分析数据（云端 Agent 产出）
    related_thesis_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("theses.id", ondelete="SET NULL"), nullable=True
    )
    analyst_rating: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # strong_buy / buy / hold / sell / strong_sell
    target_price: Mapped[Optional[float]] = mapped_column(Numeric(18, 8), nullable=True)
    stop_loss: Mapped[Optional[float]] = mapped_column(Numeric(18, 8), nullable=True)

    # 扩展字段
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True, default=list)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=dict
    )  # 如 { "broker": "富途", "account": "主账户" }

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 关系
    transactions: Mapped[List["PositionTransaction"]] = relationship(
        "PositionTransaction",
        back_populates="position",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("ticker", "market", "position_type", name="uix_position_ticker_market_type"),
        Index("idx_position_status", "status"),
        Index("idx_position_market", "market"),
        Index("idx_position_sector", "sector"),
    )

    # ── 计算属性（运行时计算，不入库） ──

    @property
    def market_value(self) -> Optional[float]:
        """持仓市值 = 数量 × 当前价"""
        if self.current_price is None:
            return None
        return float(self.quantity) * float(self.current_price)

    @property
    def cost_basis(self) -> float:
        """成本基数 = 数量 × 平均成本"""
        return float(self.quantity) * float(self.avg_cost)

    @property
    def unrealized_pnl(self) -> Optional[float]:
        """未实现盈亏 = 市值 - 成本"""
        mv = self.market_value
        if mv is None:
            return None
        return mv - self.cost_basis

    @property
    def unrealized_pnl_pct(self) -> Optional[float]:
        """未实现盈亏率"""
        cb = self.cost_basis
        if cb == 0:
            return None
        pnl = self.unrealized_pnl
        if pnl is None:
            return None
        return (pnl / cb) * 100

    @property
    def weight_in_portfolio(self, total_aum: float = 1.0) -> Optional[float]:
        """组合权重 = 市值 / 总资产"""
        mv = self.market_value
        if mv is None or total_aum == 0:
            return None
        return (mv / total_aum) * 100

    @property
    def upside_to_target(self) -> Optional[float]:
        """距目标价涨幅"""
        if self.target_price is None or self.current_price is None or self.current_price == 0:
            return None
        return ((self.target_price - self.current_price) / self.current_price) * 100

    @property
    def distance_to_stop(self) -> Optional[float]:
        """距止损跌幅"""
        if self.stop_loss is None or self.current_price is None or self.current_price == 0:
            return None
        return ((self.stop_loss - self.current_price) / self.current_price) * 100

    def to_dict(self, total_aum: float = 1.0) -> Dict[str, Any]:
        """序列化为字典（含计算属性）"""
        return {
            "id": self.id,
            "ticker": self.ticker,
            "market": self.market,
            "name": self.name,
            "name_cn": self.name_cn,
            "quantity": float(self.quantity),
            "avg_cost": float(self.avg_cost),
            "current_price": float(self.current_price) if self.current_price else None,
            "currency": self.currency,
            "market_value": self.market_value,
            "cost_basis": self.cost_basis,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
            "weight": self.weight_in_portfolio(total_aum),
            "sector": self.sector,
            "industry": self.industry,
            "position_type": self.position_type,
            "status": self.status,
            "analyst_rating": self.analyst_rating,
            "target_price": float(self.target_price) if self.target_price else None,
            "stop_loss": float(self.stop_loss) if self.stop_loss else None,
            "upside_to_target": self.upside_to_target,
            "distance_to_stop": self.distance_to_stop,
            "tags": self.tags or [],
            "notes": self.notes,
            "metadata": self.metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Position(id={self.id}, ticker='{self.ticker}', qty={self.quantity}, cost={self.avg_cost})>"


class PositionTransaction(Base):
    """持仓交易流水 - 记录每一笔买入/卖出/分红/拆股"""

    __tablename__ = "position_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    position_id: Mapped[int] = mapped_column(
        ForeignKey("positions.id", ondelete="CASCADE"), nullable=False
    )

    # 交易类型
    action: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # buy / sell / dividend / split / transfer / adjust
    action_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # 交易数量与价格
    quantity: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    fees: Mapped[float] = mapped_column(Numeric(18, 8), default=0)
    taxes: Mapped[float] = mapped_column(Numeric(18, 8), default=0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")

    # 交易后持仓快照（用于审计）
    post_quantity: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    post_avg_cost: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)

    # 备注
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )  # 数据来源：manual / broker_import / system_adjust

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # 关系
    position: Mapped["Position"] = relationship("Position", back_populates="transactions")

    __table_args__ = (
        Index("idx_tx_position_id", "position_id"),
        Index("idx_tx_action_date", "action_date"),
    )

    def __repr__(self) -> str:
        return f"<PositionTransaction(id={self.id}, position_id={self.position_id}, action='{self.action}', qty={self.quantity})>"


class WatchlistItem(Base):
    """观察仓记录 - 关注但未买入的标的"""

    __tablename__ = "watchlist_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(50), nullable=False)
    market: Mapped[str] = mapped_column(String(10), nullable=False)  # US, HK, CN
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    name_cn: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # 关注原因与评级
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # strong_buy / buy / hold / watch / avoid
    conviction: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # high / medium / low

    # 目标与计划
    target_entry_price: Mapped[Optional[float]] = mapped_column(Numeric(18, 8), nullable=True)
    target_exit_price: Mapped[Optional[float]] = mapped_column(Numeric(18, 8), nullable=True)
    planned_allocation_pct: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), nullable=True
    )  # 计划配置比例

    # 关联分析
    related_thesis_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("theses.id", ondelete="SET NULL"), nullable=True
    )
    related_industry: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # 触发条件
    alert_conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=dict
    )  # 如 { "price_below": 100, "volume_spike": true }

    # 当前价格（行情服务更新）
    current_price: Mapped[Optional[float]] = mapped_column(Numeric(18, 8), nullable=True)
    current_price_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # 距目标入场价
    distance_to_entry: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)

    # 状态
    status: Mapped[str] = mapped_column(
        String(20), default="watching", nullable=False
    )  # watching / researching / ready / entered / dropped

    # 扩展
    tags: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True, default=list)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True, default=dict
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(),
        onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("ticker", "market", name="uix_watchlist_ticker_market"),
        Index("idx_watchlist_status", "status"),
        Index("idx_watchlist_rating", "rating"),
        Index("idx_watchlist_market", "market"),
    )

    @property
    def upside_to_target(self) -> Optional[float]:
        """距目标入场价涨幅（负值为还没跌到目标）"""
        if self.target_entry_price is None or self.current_price is None or self.current_price == 0:
            return None
        return ((self.target_entry_price - self.current_price) / self.current_price) * 100

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "ticker": self.ticker,
            "market": self.market,
            "name": self.name,
            "name_cn": self.name_cn,
            "current_price": float(self.current_price) if self.current_price else None,
            "target_entry_price": float(self.target_entry_price) if self.target_entry_price else None,
            "target_exit_price": float(self.target_exit_price) if self.target_exit_price else None,
            "planned_allocation_pct": float(self.planned_allocation_pct) if self.planned_allocation_pct else None,
            "upside_to_target": self.upside_to_target,
            "distance_to_entry": float(self.distance_to_entry) if self.distance_to_entry else None,
            "rating": self.rating,
            "conviction": self.conviction,
            "reason": self.reason,
            "status": self.status,
            "related_industry": self.related_industry,
            "alert_conditions": self.alert_conditions or {},
            "tags": self.tags or [],
            "notes": self.notes,
            "metadata": self.metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<WatchlistItem(id={self.id}, ticker='{self.ticker}', status='{self.status}')>"


class PortfolioSummary(Base):
    """组合汇总快照 - 定时计算并保存（用于历史对比）"""

    __tablename__ = "portfolio_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    # 组合层面统计
    total_aum: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    total_cost_basis: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    total_unrealized_pnl: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    total_unrealized_pnl_pct: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)

    # 按市场分布
    us_market_value: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    hk_market_value: Mapped[float] = mapped_column(Numeric(18, 4), default=0)
    cn_market_value: Mapped[float] = mapped_column(Numeric(18, 4), default=0)

    # 按行业分布
    sector_breakdown: Mapped[Optional[Dict[str, float]]] = mapped_column(
        JSONB, nullable=True, default=dict
    )

    # 绩效指标
    ytd_return: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)

    # 持仓数量
    active_positions_count: Mapped[int] = mapped_column(Integer, default=0)
    watchlist_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("idx_summary_snapshot_date", "snapshot_date"),
    )

    def __repr__(self) -> str:
        return f"<PortfolioSummary(id={self.id}, date={self.snapshot_date}, aum={self.total_aum})>"
