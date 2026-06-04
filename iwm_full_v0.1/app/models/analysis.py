"""Analysis Report ORM model.

存储大V监测产出的分析结论（宏观/行业/公司）。
支持从 markdown 文件扫描导入，也支持 API 直接创建。
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


class AnalysisReport(Base):
    """分析报告模型 - 宏观/行业/公司三层分析结论."""

    __tablename__ = "analysis_reports"

    id: Mapped[int] = mapped_column(primary_key=True)

    # 分析类型
    analysis_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True,
        comment="macro / industry / company",
    )

    # 标题
    title: Mapped[str] = mapped_column(String(500), nullable=False)

    # 目标标的
    target_ticker: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True,
        comment="公司分析: 股票代码",
    )
    target_market: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True,
        comment="US/HK/CN",
    )
    target_industry: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, index=True,
        comment="行业分析: 行业名称",
    )

    # 报告日期
    report_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True,
    )

    # 源文件路径
    source_file: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True,
        comment="扫描导入时的源文件路径",
    )

    # 分析结论
    verdict: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="bullish / neutral / bearish / watch",
    )
    score: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), nullable=True,
        comment="综合打分 0-100",
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        Numeric(3, 2), nullable=True,
        comment="置信度 0-1",
    )

    # 结构化内容
    summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    key_points: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list,
        comment="关键要点列表",
    )
    risk_points: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list,
        comment="风险点列表",
    )
    opportunities: Mapped[Optional[List[str]]] = mapped_column(
        JSONB, nullable=True, default=list,
        comment="机会点列表",
    )

    # 完整内容（markdown）
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # 关联
    linked_position_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("positions.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )
    linked_thesis_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("theses.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    # 时间戳
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

    # 索引
    __table_args__ = (
        Index("idx_analysis_type_date", "analysis_type", "report_date"),
        Index("idx_analysis_ticker_date", "target_ticker", "report_date"),
        Index("idx_analysis_industry_date", "target_industry", "report_date"),
    )

    def to_dict(self, include_content: bool = False) -> dict:
        result = {
            "id": self.id,
            "analysis_type": self.analysis_type,
            "title": self.title,
            "target_ticker": self.target_ticker,
            "target_market": self.target_market,
            "target_industry": self.target_industry,
            "report_date": self.report_date.isoformat() if self.report_date else None,
            "verdict": self.verdict,
            "score": float(self.score) if self.score is not None else None,
            "confidence": float(self.confidence) if self.confidence is not None else None,
            "summary": self.summary,
            "key_points": self.key_points or [],
            "risk_points": self.risk_points or [],
            "opportunities": self.opportunities or [],
            "linked_position_id": self.linked_position_id,
            "linked_thesis_id": self.linked_thesis_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            result["content"] = self.content
            result["source_file"] = self.source_file
        return result


class AnalysisTag(Base):
    """分析标签模型 — 为报告打标签（AI基建层、电力、消费等）"""

    __tablename__ = "analysis_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True,
        comment="标签名称",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True,
        comment="标签描述",
    )
    color: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="标签颜色代码",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
