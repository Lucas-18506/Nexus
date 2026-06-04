"""新闻API路由 - 新闻查询、事件提取、采集触发"""
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("")
async def get_news(
    category: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    processed: Optional[bool] = None
) -> dict:
    """获取新闻列表"""
    return {"news": [], "total": 0}


@router.get("/{news_id}/events")
async def get_news_events(news_id: int) -> dict:
    """获取新闻关联的事件提取结果"""
    return {"news_id": news_id, "events": []}


@router.post("/collect")
async def trigger_news_collection() -> dict:
    """触发新闻采集任务"""
    return {"status": "accepted", "message": "News collection triggered"}
