"""Portfolio API routes - 持仓管理接口.

提供持仓和观察仓的 CRUD，以及组合汇总查询。
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


# ═══════════════════════════════════════════════════════
# Pydantic Schemas
# ═══════════════════════════════════════════════════════

class PositionCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=50, description="股票代码")
    market: str = Field(..., pattern=r"^(US|HK|CN)$", description="市场: US/HK/CN")
    name: str = Field(..., max_length=255, description="股票名称")
    name_cn: Optional[str] = Field(None, max_length=255, description="中文名")
    quantity: float = Field(default=0, ge=0, description="持仓数量")
    avg_cost: float = Field(default=0, ge=0, description="平均成本")
    currency: str = Field(default="USD", max_length=10)
    sector: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    position_type: str = Field(default="long", max_length=20)
    analyst_rating: Optional[str] = Field(None, max_length=20)
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    tags: Optional[list] = Field(default_factory=list)
    notes: Optional[str] = None
    metadata: Optional[dict] = Field(default_factory=dict)


class PositionUpdate(BaseModel):
    name: Optional[str] = None
    name_cn: Optional[str] = None
    quantity: Optional[float] = Field(None, ge=0)
    avg_cost: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    analyst_rating: Optional[str] = None
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    tags: Optional[list] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None


class TransactionCreate(BaseModel):
    action: str = Field(..., pattern=r"^(buy|sell|dividend|split|transfer|adjust)$")
    action_date: Optional[datetime] = None
    quantity: float = Field(..., gt=0)
    price: float = Field(..., ge=0)
    fees: float = Field(default=0, ge=0)
    taxes: float = Field(default=0, ge=0)
    currency: Optional[str] = "USD"
    notes: Optional[str] = None
    source: str = Field(default="manual", max_length=50)


class WatchlistCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=50)
    market: str = Field(..., pattern=r"^(US|HK|CN)$")
    name: str = Field(..., max_length=255)
    name_cn: Optional[str] = None
    reason: Optional[str] = None
    rating: Optional[str] = Field(None, pattern=r"^(strong_buy|buy|hold|watch|avoid)$")
    conviction: Optional[str] = Field(None, pattern=r"^(high|medium|low)$")
    target_entry_price: Optional[float] = None
    target_exit_price: Optional[float] = None
    planned_allocation_pct: Optional[float] = Field(None, ge=0, le=100)
    related_industry: Optional[str] = None
    alert_conditions: Optional[dict] = Field(default_factory=dict)
    tags: Optional[list] = Field(default_factory=list)
    notes: Optional[str] = None
    metadata: Optional[dict] = Field(default_factory=dict)


class WatchlistUpdate(BaseModel):
    name: Optional[str] = None
    name_cn: Optional[str] = None
    reason: Optional[str] = None
    rating: Optional[str] = None
    conviction: Optional[str] = None
    target_entry_price: Optional[float] = None
    target_exit_price: Optional[float] = None
    planned_allocation_pct: Optional[float] = None
    related_industry: Optional[str] = None
    alert_conditions: Optional[dict] = None
    tags: Optional[list] = None
    notes: Optional[str] = None
    metadata: Optional[dict] = None
    status: Optional[str] = None


class PriceUpdateRequest(BaseModel):
    quotes: list = Field(..., min_length=1)


# ═══════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════

async def get_service(db: AsyncSession = Depends(get_db)) -> PortfolioService:
    return PortfolioService(db)


# ═══════════════════════════════════════════════════════
# 持仓路由
# ═══════════════════════════════════════════════════════

@router.post("/positions", response_model=dict)
async def create_position(data: PositionCreate, service: PortfolioService = Depends(get_service)):
    """创建持仓记录"""
    pos = await service.create_position(data.model_dump())
    return {"success": True, "data": pos.to_dict(total_aum=1.0)}


@router.get("/positions")
async def list_positions(
    market: Optional[str] = Query(None, pattern=r"^(US|HK|CN)$"),
    sector: Optional[str] = None,
    status: Optional[str] = Query("active", pattern=r"^(active|closed|suspended)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    with_analysis: bool = Query(False, description="是否包含关联的云端分析数据"),
    service: PortfolioService = Depends(get_service),
):
    """获取持仓列表
    
    - with_analysis=true: 返回每个持仓关联的投资逻辑、公司分析、大V信号等
    """
    if with_analysis:
        items = await service.get_positions_with_analysis(market=market)
        total_aum = sum(
            item.get("market_value", 0) or 0 for item in items
        )
        # 重新计算 weight
        for item in items:
            mv = item.get("market_value")
            if mv and total_aum > 0:
                item["weight"] = round((mv / total_aum) * 100, 2)
        return {
            "success": True,
            "data": items,
            "total_aum": round(total_aum, 2),
            "count": len(items),
        }

    positions = await service.list_positions(
        market=market, status=status, sector=sector, limit=limit, offset=offset
    )
    total_aum = 0.0
    for pos in positions:
        mv = pos.market_value
        if mv:
            total_aum += mv

    return {
        "success": True,
        "data": [pos.to_dict(total_aum=total_aum) for pos in positions],
        "total_aum": round(total_aum, 2),
        "count": len(positions),
    }


@router.get("/positions/{position_id}")
async def get_position(position_id: int, service: PortfolioService = Depends(get_service)):
    """获取持仓详情（含交易流水）"""
    pos = await service.get_position(position_id)
    if not pos:
        raise HTTPException(status_code=404, detail="持仓不存在")
    return {"success": True, "data": pos.to_dict(total_aum=1.0)}


@router.patch("/positions/{position_id}")
async def update_position(
    position_id: int,
    data: PositionUpdate,
    service: PortfolioService = Depends(get_service),
):
    """更新持仓"""
    pos = await service.update_position(position_id, data.model_dump(exclude_unset=True))
    if not pos:
        raise HTTPException(status_code=404, detail="持仓不存在")
    return {"success": True, "data": pos.to_dict(total_aum=1.0)}


@router.post("/positions/{position_id}/close")
async def close_position(
    position_id: int,
    close_price: Optional[float] = None,
    service: PortfolioService = Depends(get_service),
):
    """清仓持仓"""
    pos = await service.close_position(position_id, close_price)
    if not pos:
        raise HTTPException(status_code=404, detail="持仓不存在")
    return {"success": True, "data": pos.to_dict(total_aum=1.0)}


@router.delete("/positions/{position_id}")
async def delete_position(position_id: int, service: PortfolioService = Depends(get_service)):
    """删除持仓"""
    ok = await service.delete_position(position_id)
    if not ok:
        raise HTTPException(status_code=404, detail="持仓不存在")
    return {"success": True, "message": "已删除"}


# ═══════════════════════════════════════════════════════
# 交易流水路由
# ═══════════════════════════════════════════════════════

@router.post("/positions/{position_id}/transactions")
async def add_transaction(
    position_id: int,
    data: TransactionCreate,
    service: PortfolioService = Depends(get_service),
):
    """添加交易流水（自动更新持仓）"""
    tx = await service.add_transaction(position_id, data.model_dump())
    return {
        "success": True,
        "data": {
            "id": tx.id,
            "action": tx.action,
            "quantity": float(tx.quantity),
            "price": float(tx.price),
            "post_quantity": float(tx.post_quantity),
            "post_avg_cost": float(tx.post_avg_cost),
            "created_at": tx.created_at.isoformat(),
        }
    }


@router.get("/transactions")
async def list_transactions(
    position_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=500),
    service: PortfolioService = Depends(get_service),
):
    """获取交易流水"""
    txs = await service.list_transactions(position_id=position_id, limit=limit)
    return {
        "success": True,
        "data": [
            {
                "id": tx.id,
                "position_id": tx.position_id,
                "action": tx.action,
                "action_date": tx.action_date.isoformat() if tx.action_date else None,
                "quantity": float(tx.quantity),
                "price": float(tx.price),
                "fees": float(tx.fees),
                "taxes": float(tx.taxes),
                "currency": tx.currency,
                "post_quantity": float(tx.post_quantity),
                "post_avg_cost": float(tx.post_avg_cost),
                "notes": tx.notes,
                "source": tx.source,
                "created_at": tx.created_at.isoformat(),
            }
            for tx in txs
        ],
    }


# ═══════════════════════════════════════════════════════
# 观察仓路由
# ═══════════════════════════════════════════════════════

@router.post("/watchlist", response_model=dict)
async def create_watchlist_item(
    data: WatchlistCreate, service: PortfolioService = Depends(get_service)
):
    """添加观察仓"""
    item = await service.create_watchlist_item(data.model_dump())
    return {"success": True, "data": item.to_dict()}


@router.get("/watchlist")
async def list_watchlist(
    market: Optional[str] = Query(None, pattern=r"^(US|HK|CN)$"),
    rating: Optional[str] = None,
    status: Optional[str] = Query(None, pattern=r"^(watching|researching|ready|entered|dropped)$"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    service: PortfolioService = Depends(get_service),
):
    """获取观察仓列表"""
    items = await service.list_watchlist(
        market=market, status=status, rating=rating, limit=limit, offset=offset
    )
    return {
        "success": True,
        "data": [item.to_dict() for item in items],
        "count": len(items),
    }


@router.get("/watchlist/{item_id}")
async def get_watchlist_item(item_id: int, service: PortfolioService = Depends(get_service)):
    """获取观察仓详情"""
    item = await service.get_watchlist_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="观察仓不存在")
    return {"success": True, "data": item.to_dict()}


@router.patch("/watchlist/{item_id}")
async def update_watchlist_item(
    item_id: int,
    data: WatchlistUpdate,
    service: PortfolioService = Depends(get_service),
):
    """更新观察仓"""
    item = await service.update_watchlist_item(item_id, data.model_dump(exclude_unset=True))
    if not item:
        raise HTTPException(status_code=404, detail="观察仓不存在")
    return {"success": True, "data": item.to_dict()}


@router.delete("/watchlist/{item_id}")
async def delete_watchlist_item(item_id: int, service: PortfolioService = Depends(get_service)):
    """删除观察仓"""
    ok = await service.delete_watchlist_item(item_id)
    if not ok:
        raise HTTPException(status_code=404, detail="观察仓不存在")
    return {"success": True, "message": "已删除"}


# ═══════════════════════════════════════════════════════
# 组合汇总路由
# ═══════════════════════════════════════════════════════

@router.get("/summary")
async def get_portfolio_summary(service: PortfolioService = Depends(get_service)):
    """获取组合实时汇总"""
    summary = await service.get_portfolio_summary()
    return {"success": True, "data": summary}


@router.post("/summary/snapshot")
async def save_snapshot(service: PortfolioService = Depends(get_service)):
    """手动保存组合快照"""
    snapshot = await service.save_snapshot()
    return {"success": True, "data": {"id": snapshot.id, "snapshot_date": snapshot.snapshot_date.isoformat()}}


@router.get("/health-score")
async def get_health_score(service: PortfolioService = Depends(get_service)):
    """获取组合健康评分（100分制）
    
    评分维度：
    - AI集中度（25%）
    - 港股占比（20%）
    - 高亏损标的数量（20%）
    - 防御性资产比例（15%）
    - 现金预留（10%）
    - 集中度风险（10%）
    """
    result = await service.calculate_health_score()
    return {"success": True, "data": result}


@router.get("/risk-metrics")
async def get_risk_metrics(service: PortfolioService = Depends(get_service)):
    """获取组合风险指标
    
    返回：
    - sharpe_ratio: 夏普比率（>1.5 优秀，0.5-1.5 一般，<0.5 差）
    - max_drawdown: 最大回撤百分比（<10% 优秀，10-20% 一般，>20% 高）
    - volatility: 年化波动率百分比
    - annual_return: 年化收益率百分比
    - risk_free_rate: 无风险利率（3%）
    """
    result = await service.calculate_risk_metrics()
    return {"success": True, "data": result}


@router.get("/correlation")
async def get_correlation_matrix(service: PortfolioService = Depends(get_service)):
    """获取持仓标的之间的近似相关性矩阵
    
    基于行业/市场/标签相似度计算"近似相关性"：
    - 同市场：+0.3
    - 同行业：+0.4
    - 每共享一个标签：+0.2
    
    返回：
    - matrix: 所有标的对的相关性列表
    - top_pairs: Top5 高相关性标的对
    - high_correlation_pairs: 相关性 >0.7 的标的对（风险提示）
    """
    result = await service.calculate_correlation_matrix()
    return {"success": True, "data": result}


# ═══════════════════════════════════════════════════════
# 价格更新路由（内部/定时任务用）
# ═══════════════════════════════════════════════════════

@router.post("/prices/update")
async def update_prices(
    data: PriceUpdateRequest,
    service: PortfolioService = Depends(get_service),
):
    """批量更新持仓和观察仓的当前价格
    
    由行情采集器定时调用，或手动触发。
    """
    result = await service.update_prices(data.quotes)
    return {"success": True, "data": result}


# ═══════════════════════════════════════════════════════
# 云端分析数据对接
# ═══════════════════════════════════════════════════════

@router.post("/positions/{position_id}/link-thesis")
async def link_position_to_thesis(
    position_id: int,
    thesis_id: int,
    service: PortfolioService = Depends(get_service),
):
    """将持仓关联到投资逻辑（Thesis）"""
    pos = await service.link_position_to_thesis(position_id, thesis_id)
    if not pos:
        raise HTTPException(status_code=404, detail="持仓不存在")
    return {"success": True, "data": {"position_id": pos.id, "thesis_id": pos.related_thesis_id}}


@router.post("/watchlist/{item_id}/link-thesis")
async def link_watchlist_to_thesis(
    item_id: int,
    thesis_id: int,
    service: PortfolioService = Depends(get_service),
):
    """将观察仓关联到投资逻辑（Thesis）"""
    item = await service.link_watchlist_to_thesis(item_id, thesis_id)
    if not item:
        raise HTTPException(status_code=404, detail="观察仓不存在")
    return {"success": True, "data": {"watchlist_item_id": item.id, "thesis_id": item.related_thesis_id}}
