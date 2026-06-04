"""Analysis Report API routes.

提供分析结论的 CRUD、文件扫描、持仓关联查询。
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


# ═══════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════

class AnalysisCreate(BaseModel):
    analysis_type: str = Field(..., pattern=r"^(macro|industry|company)$")
    title: str = Field(..., min_length=1, max_length=500)
    target_ticker: Optional[str] = Field(None, max_length=50)
    target_market: Optional[str] = Field(None, pattern=r"^(US|HK|CN)$")
    target_industry: Optional[str] = Field(None, max_length=255)
    report_date: Optional[str] = None  # ISO format
    verdict: Optional[str] = Field(None, pattern=r"^(bullish|neutral|bearish|watch)$")
    score: Optional[float] = Field(None, ge=0, le=100)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    summary: str = Field(default="")
    key_points: Optional[list] = Field(default_factory=list)
    risk_points: Optional[list] = Field(default_factory=list)
    opportunities: Optional[list] = Field(default_factory=list)
    content: str = Field(default="")
    linked_position_id: Optional[int] = None
    linked_thesis_id: Optional[int] = None


class AnalysisUpdate(BaseModel):
    title: Optional[str] = None
    verdict: Optional[str] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    confidence: Optional[float] = Field(None, ge=0, le=1)
    summary: Optional[str] = None
    key_points: Optional[list] = None
    risk_points: Optional[list] = None
    opportunities: Optional[list] = None
    content: Optional[str] = None
    linked_position_id: Optional[int] = None
    linked_thesis_id: Optional[int] = None


class ScanRequest(BaseModel):
    reports_dir: str = Field(..., description="分析文件目录路径")


# ═══════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════

async def get_service(db: AsyncSession = Depends(get_db)) -> AnalysisService:
    return AnalysisService(db)


# ═══════════════════════════════════════════════════════
# CRUD Routes
# ═══════════════════════════════════════════════════════

@router.post("", response_model=dict)
async def create_analysis(data: AnalysisCreate, service: AnalysisService = Depends(get_service)):
    """创建分析报告"""
    payload = data.model_dump()
    if payload.get("report_date"):
        try:
            payload["report_date"] = datetime.fromisoformat(payload["report_date"].replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的 report_date 格式")
    result = await service.create(payload)
    return {"success": True, "data": result}


@router.get("")
async def list_analysis(
    analysis_type: Optional[str] = Query(None, pattern=r"^(macro|industry|company)$"),
    ticker: Optional[str] = None,
    industry: Optional[str] = None,
    verdict: Optional[str] = Query(None, pattern=r"^(bullish|neutral|bearish|watch)$"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: AnalysisService = Depends(get_service),
):
    """获取分析报告列表"""
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的 start_date")
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(status_code=400, detail="无效的 end_date")

    result = await service.list_reports(
        analysis_type=analysis_type, ticker=ticker, industry=industry,
        verdict=verdict, start_date=start_dt, end_date=end_dt,
        limit=limit, offset=offset,
    )
    return {"success": True, "data": result}


@router.get("/{report_id}")
async def get_analysis(report_id: int, service: AnalysisService = Depends(get_service)):
    """获取分析报告详情（含完整内容）"""
    result = await service.get(report_id)
    if not result:
        raise HTTPException(status_code=404, detail="分析报告不存在")
    return {"success": True, "data": result}


@router.patch("/{report_id}")
async def update_analysis(report_id: int, data: AnalysisUpdate, service: AnalysisService = Depends(get_service)):
    """更新分析报告"""
    result = await service.update(report_id, data.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="分析报告不存在")
    return {"success": True, "data": result}


@router.delete("/{report_id}")
async def delete_analysis(report_id: int, service: AnalysisService = Depends(get_service)):
    """删除分析报告"""
    ok = await service.delete(report_id)
    if not ok:
        raise HTTPException(status_code=404, detail="分析报告不存在")
    return {"success": True, "message": "已删除"}


# ═══════════════════════════════════════════════════════
# Ticker / Industry lookups
# ═══════════════════════════════════════════════════════

@router.get("/by-symbol/{symbol}")
async def get_analysis_by_symbol(
    symbol: str,
    market: Optional[str] = Query(None, pattern=r"^(US|HK|CN)$"),
    limit: int = Query(20, ge=1, le=100),
    service: AnalysisService = Depends(get_service),
):
    """获取某个 symbol（ticker）关联的所有分析报告"""
    items = await service.get_by_ticker(symbol, market=market, limit=limit)
    return {"success": True, "data": items}


@router.get("/by-symbol/{symbol}/latest")
async def get_latest_analysis_by_symbol(
    symbol: str,
    market: Optional[str] = Query(None, pattern=r"^(US|HK|CN)$"),
    service: AnalysisService = Depends(get_service),
):
    """获取某个 symbol（ticker）的最新分析报告"""
    result = await service.get_latest_by_ticker(symbol, market=market)
    if not result:
        raise HTTPException(status_code=404, detail="未找到该标的的分析报告")
    return {"success": True, "data": result}


@router.get("/by-industry/{industry}")
async def get_analysis_by_industry(
    industry: str,
    limit: int = Query(20, ge=1, le=100),
    service: AnalysisService = Depends(get_service),
):
    """获取某行业的分析报告"""
    items = await service.get_by_industry(industry, limit=limit)
    return {"success": True, "data": items}


# ═══════════════════════════════════════════════════════
# Portfolio summary
# ═══════════════════════════════════════════════════════

@router.post("/portfolio-summary")
async def get_portfolio_analysis_summary(
    tickers: list[str],
    service: AnalysisService = Depends(get_service),
):
    """批量获取持仓标的的分析汇总"""
    result = await service.get_portfolio_summary(tickers)
    return {"success": True, "data": result}


# ═══════════════════════════════════════════════════════
# Analysis Tag Routes
# ═══════════════════════════════════════════════════════

class TagCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    color: Optional[str] = Field(None, max_length=50)

class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=50)

@router.post("/tags")
async def create_tag(data: TagCreate, service: AnalysisService = Depends(get_service)):
    """创建分析标签"""
    result = await service.create_tag(data.model_dump())
    return {"success": True, "data": result}

@router.get("/tags")
async def list_tags(service: AnalysisService = Depends(get_service)):
    """获取所有分析标签"""
    items = await service.list_tags()
    return {"success": True, "data": items}

@router.get("/tags/{tag_id}")
async def get_tag(tag_id: int, service: AnalysisService = Depends(get_service)):
    """获取标签详情"""
    result = await service.get_tag(tag_id)
    if not result:
        raise HTTPException(status_code=404, detail="标签不存在")
    return {"success": True, "data": result}

@router.patch("/tags/{tag_id}")
async def update_tag(tag_id: int, data: TagUpdate, service: AnalysisService = Depends(get_service)):
    """更新标签"""
    result = await service.update_tag(tag_id, data.model_dump(exclude_unset=True))
    if not result:
        raise HTTPException(status_code=404, detail="标签不存在")
    return {"success": True, "data": result}

@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: int, service: AnalysisService = Depends(get_service)):
    """删除标签"""
    ok = await service.delete_tag(tag_id)
    if not ok:
        raise HTTPException(status_code=404, detail="标签不存在")
    return {"success": True, "message": "已删除"}

@router.post("/sync")
async def sync_analysis_reports(
    request: ScanRequest,
    service: AnalysisService = Depends(get_service),
):
    """同步分析文件目录，自动扫描导入/更新数据库.

    支持的文件名格式:
    - 公司分析_{ticker}_{name}_{YYYYMMDD}.md
    - 公司分析_{name}_{YYYYMMDD}.md
    - 行业分析_{industry}_{YYYYMMDD}.md
    - 宏观分析_{YYYYMMDD}.md

    这是关键接口，后续会定时调用以同步大V监测产出的新报告。
    """
    result = await service.scan_reports_directory(request.reports_dir)
    return {"success": True, "data": result}
