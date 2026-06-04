"""数据API路由 - 宏观指标、股票数据、市场摘要"""
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/data", tags=["data"])


@router.get("/macro")
async def get_macro_indicators(
    indicator_type: Optional[str] = None,
    country: Optional[str] = None,
    limit: int = Query(default=50, le=200)
) -> dict:
    """获取宏观指标数据"""
    return {"indicators": [], "total": 0}


@router.get("/stock/{ticker}")
async def get_stock_data(
    ticker: str,
    market: str = Query(..., description="US/HK/CN"),
    period: str = Query(default="1y", description="1m/3m/6m/1y/2y/5y")
) -> dict:
    """获取股票历史数据"""
    return {"ticker": ticker, "market": market, "data": []}


@router.get("/market/summary")
async def get_market_summary() -> dict:
    """获取市场摘要概览"""
    return {
        "a_share": {"index": "沪深300", "change": "+0.5%", "note": "震荡"},
        "hk": {"index": "恒生指数", "change": "+1.2%", "note": "反弹"},
        "us": {"index": "标普500", "change": "-0.3%", "note": "调整"},
        "risk_level": "中等"
    }
