"""Cache Management API — 缓存管理路由

提供：
- GET /api/cache/stats — 查看缓存统计
- POST /api/cache/cleanup — 清理过期缓存
- DELETE /api/cache/{symbol}/{data_type} — 失效指定缓存
- DELETE /api/cache/{symbol} — 失效指定 symbol 所有缓存
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.services.cache_manager import CacheManager

router = APIRouter(prefix="/cache", tags=["cache"])


def get_cache_manager():
    return CacheManager()


@router.get("/stats")
async def get_cache_stats(cache: CacheManager = Depends(get_cache_manager)):
    """获取缓存统计信息"""
    stats = await cache.get_stats()
    return {"success": True, "data": stats}


@router.post("/cleanup")
async def cleanup_cache(
    data_type: str = None,
    cache: CacheManager = Depends(get_cache_manager)
):
    """清理过期缓存文件

    Args:
        data_type: 如果指定，只清理该类型；否则清理全部
    """
    deleted = await cache.cleanup(data_type=data_type)
    return {"success": True, "data": {"deleted": deleted}}


@router.delete("/invalidate/{symbol}/{data_type}")
async def invalidate_cache(
    symbol: str,
    data_type: str,
    cache: CacheManager = Depends(get_cache_manager)
):
    """手动失效指定缓存"""
    result = await cache.invalidate(symbol, data_type)
    return {"success": True, "data": {"deleted": result}}


@router.delete("/invalidate/{symbol}")
async def invalidate_all_cache(
    symbol: str,
    cache: CacheManager = Depends(get_cache_manager)
):
    """失效指定 symbol 的所有缓存"""
    deleted = await cache.invalidate_all(symbol)
    return {"success": True, "data": {"deleted": deleted}}
