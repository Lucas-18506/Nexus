"""L2 File Cache Manager — 文件级数据缓存（MVP 版本）

职责：
- 为 symbol+data_type 组合提供 JSON 文件缓存
- 自动 TTL 过期检查
- 支持手动失效和批量清理

缓存路径：
    ./cache/{data_type}/{symbol}_{YYYYMMDD}.json

文件格式：
    {
        "data": <任意 JSON 序列化数据>,
        "source": <数据来源描述>,
        "created_at": "2026-06-03T12:00:00+08:00",
        "expires_at": "2026-06-03T13:00:00+08:00"
    }

TTL 规则（默认）：
    - company_static: 7 天
    - financial_report: 1 天
    - macro_data: 4 小时
    - position_price: 1 小时
    - analysis_scan: 1 小时
    - default: 1 天

使用示例：
    cache = CacheManager(cache_dir="./cache")
    
    # 写入
    await cache.set("AAPL", "position_price", {"price": 150.0}, ttl=3600)
    
    # 读取（自动检查过期）
    data = await cache.get("AAPL", "position_price")
    if data:
        print(data["data"]["price"])
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── 默认 TTL 配置（秒）──
DEFAULT_TTL_MAP = {
    "company_static": 7 * 24 * 3600,      # 7 天
    "financial_report": 24 * 3600,         # 1 天
    "macro_data": 4 * 3600,                # 4 小时
    "position_price": 3600,                # 1 小时
    "analysis_scan": 3600,                 # 1 小时
    "default": 24 * 3600,                  # 1 天
}


class CacheManager:
    """L2 文件缓存管理器"""

    def __init__(self, cache_dir: str = "./cache"):
        self.cache_dir = Path(cache_dir)
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        """确保缓存目录存在"""
        for data_type in DEFAULT_TTL_MAP.keys():
            (self.cache_dir / data_type).mkdir(parents=True, exist_ok=True)
        logger.info("CacheManager initialized: %s", self.cache_dir.resolve())

    def _build_path(self, symbol: str, data_type: str) -> Path:
        """构建缓存文件路径

        格式：./cache/{data_type}/{symbol}_{YYYYMMDD}.json
        """
        today = datetime.now(timezone.utc).strftime("%Y%m%d")
        safe_symbol = symbol.replace("/", "_").replace("\\", "_")
        return self.cache_dir / data_type / f"{safe_symbol}_{today}.json"

    def _is_expired(self, expires_at: str) -> bool:
        """检查是否已过期"""
        try:
            expiry = datetime.fromisoformat(expires_at)
            return datetime.now(timezone.utc) > expiry
        except Exception:
            return True

    # ── 公共 API ──

    async def get(self, symbol: str, data_type: str) -> Optional[Dict[str, Any]]:
        """读取缓存数据

        如果缓存不存在或已过期，返回 None。

        Args:
            symbol: 标的代码（如 AAPL, 0700.HK）
            data_type: 数据类型（如 position_price, macro_data）

        Returns:
            缓存内容 dict 或 None
        """
        cache_path = self._build_path(symbol, data_type)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_entry = json.load(f)

            if self._is_expired(cache_entry.get("expires_at", "")):
                logger.debug("Cache expired: %s / %s", symbol, data_type)
                return None

            logger.debug("Cache hit: %s / %s", symbol, data_type)
            return cache_entry

        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Cache read error for %s/%s: %s", symbol, data_type, e)
            return None

    async def set(
        self,
        symbol: str,
        data_type: str,
        data: Any,
        ttl: Optional[int] = None,
        source: str = "internal",
    ) -> None:
        """写入缓存数据

        Args:
            symbol: 标的代码
            data_type: 数据类型
            data: 要缓存的数据（JSON 序列化）
            ttl: 有效期（秒），None 时使用 data_type 默认 TTL
            source: 数据来源描述
        """
        if ttl is None:
            ttl = DEFAULT_TTL_MAP.get(data_type, DEFAULT_TTL_MAP["default"])

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=ttl)

        cache_entry = {
            "data": data,
            "source": source,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        cache_path = self._build_path(symbol, data_type)
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cache_entry, f, ensure_ascii=False, indent=2)
            logger.debug("Cache set: %s / %s (ttl=%ds)", symbol, data_type, ttl)
        except OSError as e:
            logger.error("Cache write error for %s/%s: %s", symbol, data_type, e)

    async def invalidate(self, symbol: str, data_type: str) -> bool:
        """手动失效缓存

        Returns:
            是否成功删除缓存文件
        """
        cache_path = self._build_path(symbol, data_type)
        if cache_path.exists():
            try:
                cache_path.unlink()
                logger.info("Cache invalidated: %s / %s", symbol, data_type)
                return True
            except OSError as e:
                logger.error("Cache invalidate error for %s/%s: %s", symbol, data_type, e)
                return False
        return False

    async def invalidate_all(self, symbol: str) -> int:
        """失效某个 symbol 的所有数据类型缓存

        Returns:
            删除的文件数量
        """
        deleted = 0
        safe_symbol = symbol.replace("/", "_").replace("\\", "_")
        for data_type in DEFAULT_TTL_MAP.keys():
            dir_path = self.cache_dir / data_type
            if not dir_path.exists():
                continue
            for file in dir_path.iterdir():
                if file.name.startswith(f"{safe_symbol}_") and file.suffix == ".json":
                    try:
                        file.unlink()
                        deleted += 1
                    except OSError:
                        pass
        logger.info("Cache invalidated all for %s: %d files", symbol, deleted)
        return deleted

    async def cleanup(self, data_type: Optional[str] = None) -> int:
        """清理过期缓存文件

        Args:
            data_type: 如果指定，只清理该类型；否则清理全部

        Returns:
            删除的文件数量
        """
        deleted = 0
        data_types = [data_type] if data_type else DEFAULT_TTL_MAP.keys()

        for dt in data_types:
            dir_path = self.cache_dir / dt
            if not dir_path.exists():
                continue
            for file in dir_path.iterdir():
                if file.suffix != ".json":
                    continue
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        entry = json.load(f)
                    if self._is_expired(entry.get("expires_at", "")):
                        file.unlink()
                        deleted += 1
                except (json.JSONDecodeError, OSError):
                    # 损坏的文件也删除
                    try:
                        file.unlink()
                        deleted += 1
                    except OSError:
                        pass

        logger.info("Cache cleanup: %d expired files removed", deleted)
        return deleted

    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        stats = {}
        total_files = 0
        total_size = 0

        for data_type in DEFAULT_TTL_MAP.keys():
            dir_path = self.cache_dir / data_type
            if not dir_path.exists():
                stats[data_type] = {"files": 0, "size_kb": 0}
                continue

            files = list(dir_path.glob("*.json"))
            size = sum(f.stat().st_size for f in files)
            total_files += len(files)
            total_size += size
            stats[data_type] = {"files": len(files), "size_kb": round(size / 1024, 2)}

        stats["total"] = {"files": total_files, "size_kb": round(total_size / 1024, 2)}
        return stats
