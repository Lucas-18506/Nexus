"""Portfolio service layer - 持仓管理业务逻辑.

职责：
- 持仓 CRUD + 盈亏计算
- 观察仓 CRUD + 评级管理
- 组合汇总快照
- 持仓与云端分析数据关联
"""

import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.portfolio import Position, PositionTransaction, WatchlistItem, PortfolioSummary
from app.models.stock import StockQuote
from app.services.cache_manager import CacheManager

logger = logging.getLogger(__name__)


class PortfolioService:
    """持仓管理服务"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.cache = CacheManager()

    # ═══════════════════════════════════════════════════════
    # 持仓 CRUD
    # ═══════════════════════════════════════════════════════

    async def create_position(self, data: Dict[str, Any]) -> Position:
        """创建持仓记录"""
        pos = Position(
            ticker=data["ticker"],
            market=data["market"],
            name=data["name"],
            name_cn=data.get("name_cn"),
            quantity=data.get("quantity", 0),
            avg_cost=data.get("avg_cost", 0),
            currency=data.get("currency", "USD"),
            sector=data.get("sector"),
            industry=data.get("industry"),
            position_type=data.get("position_type", "long"),
            status="active",
            analyst_rating=data.get("analyst_rating"),
            target_price=data.get("target_price"),
            stop_loss=data.get("stop_loss"),
            tags=data.get("tags", []),
            notes=data.get("notes"),
            metadata=data.get("metadata", {}),
        )
        self.db.add(pos)
        await self.db.commit()
        await self.db.refresh(pos)
        logger.info("创建持仓: %s %s", pos.ticker, pos.market)
        return pos

    async def get_position(self, position_id: int) -> Optional[Position]:
        """按 ID 获取持仓详情（含交易流水）"""
        result = await self.db.execute(
            select(Position)
            .where(Position.id == position_id)
            .options(selectinload(Position.transactions))
        )
        return result.scalar_one_or_none()

    async def get_position_by_ticker(self, ticker: str, market: str) -> Optional[Position]:
        """按 ticker+market 获取持仓"""
        result = await self.db.execute(
            select(Position)
            .where(and_(Position.ticker == ticker, Position.market == market))
            .options(selectinload(Position.transactions))
        )
        return result.scalar_one_or_none()

    async def list_positions(
        self,
        market: Optional[str] = None,
        status: Optional[str] = "active",
        sector: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Position]:
        """获取持仓列表"""
        query = select(Position)
        if status:
            query = query.where(Position.status == status)
        if market:
            query = query.where(Position.market == market)
        if sector:
            query = query.where(Position.sector == sector)
        query = query.order_by(Position.updated_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_position(self, position_id: int, data: Dict[str, Any]) -> Optional[Position]:
        """更新持仓（成本/评级/目标价等）"""
        pos = await self.get_position(position_id)
        if not pos:
            return None

        allowed_fields = {
            "name", "name_cn", "quantity", "avg_cost", "currency",
            "sector", "industry", "analyst_rating", "target_price",
            "stop_loss", "tags", "notes", "metadata",
        }
        for k, v in data.items():
            if k in allowed_fields and hasattr(pos, k):
                setattr(pos, k, v)

        pos.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(pos)
        return pos

    async def close_position(self, position_id: int, close_price: Optional[float] = None) -> Optional[Position]:
        """清仓持仓"""
        pos = await self.get_position(position_id)
        if not pos:
            return None

        pos.status = "closed"
        pos.closed_at = datetime.now(timezone.utc)
        if close_price:
            pos.current_price = close_price
        pos.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(pos)
        logger.info("持仓已清仓: %s %s", pos.ticker, pos.market)
        return pos

    async def delete_position(self, position_id: int) -> bool:
        """删除持仓（连带删除交易流水）"""
        pos = await self.get_position(position_id)
        if not pos:
            return False
        await self.db.delete(pos)
        await self.db.commit()
        logger.info("删除持仓: id=%d", position_id)
        return True

    # ═══════════════════════════════════════════════════════
    # 持仓交易流水
    # ═══════════════════════════════════════════════════════

    async def add_transaction(self, position_id: int, data: Dict[str, Any]) -> PositionTransaction:
        """添加交易流水并更新持仓"""
        pos = await self.get_position(position_id)
        if not pos:
            raise ValueError(f"持仓不存在: {position_id}")

        action = data["action"]  # buy / sell / dividend / etc.
        qty = float(data["quantity"])
        price = float(data["price"])
        fees = float(data.get("fees", 0))
        taxes = float(data.get("taxes", 0))

        # 计算交易后持仓
        if action in ("buy", "dividend", "transfer_in"):
            new_qty = float(pos.quantity) + qty
            # 加权平均成本
            old_cost = float(pos.quantity) * float(pos.avg_cost)
            new_cost = old_cost + (qty * price) + fees + taxes
            new_avg_cost = new_cost / new_qty if new_qty != 0 else 0
        elif action in ("sell", "transfer_out"):
            new_qty = float(pos.quantity) - qty
            # 卖出不影响平均成本（FIFO 简化）
            new_avg_cost = float(pos.avg_cost)
        else:
            new_qty = float(pos.quantity)
            new_avg_cost = float(pos.avg_cost)

        tx = PositionTransaction(
            position_id=position_id,
            action=action,
            action_date=data.get("action_date", datetime.now(timezone.utc)),
            quantity=qty,
            price=price,
            fees=fees,
            taxes=taxes,
            currency=data.get("currency", pos.currency),
            post_quantity=new_qty,
            post_avg_cost=new_avg_cost,
            notes=data.get("notes"),
            source=data.get("source", "manual"),
        )
        self.db.add(tx)

        # 更新持仓
        pos.quantity = new_qty
        pos.avg_cost = new_avg_cost
        if new_qty == 0:
            pos.status = "closed"
            pos.closed_at = datetime.now(timezone.utc)
        pos.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(tx)
        logger.info("添加交易流水: %s %s %s %.2f", pos.ticker, action, qty, price)
        return tx

    async def list_transactions(
        self, position_id: Optional[int] = None, limit: int = 50
    ) -> List[PositionTransaction]:
        """获取交易流水列表"""
        query = select(PositionTransaction).order_by(PositionTransaction.action_date.desc())
        if position_id:
            query = query.where(PositionTransaction.position_id == position_id)
        query = query.limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ═══════════════════════════════════════════════════════
    # 观察仓 CRUD
    # ═══════════════════════════════════════════════════════

    async def create_watchlist_item(self, data: Dict[str, Any]) -> WatchlistItem:
        """添加观察仓"""
        item = WatchlistItem(
            ticker=data["ticker"],
            market=data["market"],
            name=data["name"],
            name_cn=data.get("name_cn"),
            reason=data.get("reason"),
            rating=data.get("rating"),
            conviction=data.get("conviction"),
            target_entry_price=data.get("target_entry_price"),
            target_exit_price=data.get("target_exit_price"),
            planned_allocation_pct=data.get("planned_allocation_pct"),
            related_industry=data.get("related_industry"),
            alert_conditions=data.get("alert_conditions", {}),
            tags=data.get("tags", []),
            notes=data.get("notes"),
            metadata=data.get("metadata", {}),
        )
        self.db.add(item)
        await self.db.commit()
        await self.db.refresh(item)
        logger.info("添加观察仓: %s %s", item.ticker, item.market)
        return item

    async def get_watchlist_item(self, item_id: int) -> Optional[WatchlistItem]:
        """获取观察仓详情"""
        result = await self.db.execute(
            select(WatchlistItem).where(WatchlistItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def list_watchlist(
        self,
        market: Optional[str] = None,
        status: Optional[str] = None,
        rating: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[WatchlistItem]:
        """获取观察仓列表"""
        query = select(WatchlistItem)
        if market:
            query = query.where(WatchlistItem.market == market)
        if status:
            query = query.where(WatchlistItem.status == status)
        if rating:
            query = query.where(WatchlistItem.rating == rating)
        query = query.order_by(WatchlistItem.updated_at.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_watchlist_item(self, item_id: int, data: Dict[str, Any]) -> Optional[WatchlistItem]:
        """更新观察仓"""
        item = await self.get_watchlist_item(item_id)
        if not item:
            return None

        allowed_fields = {
            "name", "name_cn", "reason", "rating", "conviction",
            "target_entry_price", "target_exit_price", "planned_allocation_pct",
            "related_industry", "alert_conditions", "tags", "notes",
            "metadata", "status",
        }
        for k, v in data.items():
            if k in allowed_fields and hasattr(item, k):
                setattr(item, k, v)

        item.updated_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def delete_watchlist_item(self, item_id: int) -> bool:
        """删除观察仓"""
        item = await self.get_watchlist_item(item_id)
        if not item:
            return False
        await self.db.delete(item)
        await self.db.commit()
        logger.info("删除观察仓: id=%d", item_id)
        return True

    # ═══════════════════════════════════════════════════════
    # 价格更新（由行情采集器调用）
    # ═══════════════════════════════════════════════════════

    async def update_prices(self, quotes: List[Dict[str, Any]]) -> Dict[str, int]:
        """批量更新持仓和观察仓的当前价格
        
        quotes: [{"ticker": "AAPL", "market": "US", "price": 175.5}]
        """
        updated_positions = 0
        updated_watchlist = 0
        now = datetime.now(timezone.utc)

        for q in quotes:
            ticker = q["ticker"]
            market = q["market"]
            price = q.get("price")
            if price is None:
                continue

            # 缓存价格（L2 文件缓存）
            try:
                await self.cache.set(
                    f"{ticker}.{market}",
                    "position_price",
                    {"price": price, "market": market, "ticker": ticker, "updated_at": now.isoformat()},
                    ttl=3600,
                    source="market_data",
                )
            except Exception as e:
                logger.warning("Price cache write error for %s.%s: %s", ticker, market, e)

            # 更新持仓
            pos_result = await self.db.execute(
                select(Position).where(
                    and_(Position.ticker == ticker, Position.market == market)
                )
            )
            pos = pos_result.scalar_one_or_none()
            if pos:
                pos.current_price = price
                pos.current_price_updated_at = now
                updated_positions += 1

            # 更新观察仓
            wl_result = await self.db.execute(
                select(WatchlistItem).where(
                    and_(WatchlistItem.ticker == ticker, WatchlistItem.market == market)
                )
            )
            wl = wl_result.scalar_one_or_none()
            if wl:
                wl.current_price = price
                wl.current_price_updated_at = now
                # 重新计算距目标入场价
                if wl.target_entry_price and price != 0:
                    wl.distance_to_entry = ((wl.target_entry_price - price) / price) * 100
                updated_watchlist += 1

        await self.db.commit()
        logger.info("价格更新完成: 持仓 %d 条, 观察仓 %d 条", updated_positions, updated_watchlist)
        return {"positions": updated_positions, "watchlist": updated_watchlist}

    async def get_cached_price(self, ticker: str, market: str) -> Optional[float]:
        """从缓存获取价格（如缓存过期则返回 None）"""
        cache_entry = await self.cache.get(f"{ticker}.{market}", "position_price")
        if cache_entry:
            return cache_entry["data"].get("price")
        return None

    # ═══════════════════════════════════════════════════════
    # 组合汇总
    # ═══════════════════════════════════════════════════════

    async def get_portfolio_summary(self) -> Dict[str, Any]:
        """获取当前组合汇总（实时计算）"""
        positions = await self.list_positions(status="active", limit=1000)

        total_aum = 0.0
        total_cost = 0.0
        total_pnl = 0.0
        us_value = 0.0
        hk_value = 0.0
        cn_value = 0.0
        sector_breakdown: Dict[str, float] = {}

        active_count = 0
        for pos in positions:
            active_count += 1
            mv = pos.market_value
            cb = pos.cost_basis
            pnl = pos.unrealized_pnl
            if mv is not None:
                total_aum += mv
                if pnl is not None:
                    total_pnl += pnl
            if cb is not None:
                total_cost += cb

            # 按市场分布
            if mv is not None:
                if pos.market == "US":
                    us_value += mv
                elif pos.market == "HK":
                    hk_value += mv
                elif pos.market == "CN":
                    cn_value += mv

            # 按行业分布
            if pos.sector and mv is not None:
                sector_breakdown[pos.sector] = sector_breakdown.get(pos.sector, 0) + mv

        # 计算比例
        if total_aum > 0:
            for k in sector_breakdown:
                sector_breakdown[k] = round((sector_breakdown[k] / total_aum) * 100, 2)

        total_pnl_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

        watchlist = await self.list_watchlist(status="watching", limit=1000)

        summary = {
            "total_aum": round(total_aum, 2),
            "total_cost_basis": round(total_cost, 2),
            "total_unrealized_pnl": round(total_pnl, 2),
            "total_unrealized_pnl_pct": round(total_pnl_pct, 2),
            "active_positions_count": active_count,
            "watchlist_count": len(watchlist),
            "market_breakdown": {
                "us": round(us_value, 2),
                "hk": round(hk_value, 2),
                "cn": round(cn_value, 2),
            },
            "sector_breakdown": sector_breakdown,
            "currency": "USD",  # 简化，实际需要做汇率换算
        }

        return summary

    async def save_snapshot(self) -> PortfolioSummary:
        """保存组合快照（定时任务调用）"""
        summary = await self.get_portfolio_summary()
        now = datetime.now(timezone.utc)

        snapshot = PortfolioSummary(
            snapshot_date=now,
            total_aum=summary["total_aum"],
            total_cost_basis=summary["total_cost_basis"],
            total_unrealized_pnl=summary["total_unrealized_pnl"],
            total_unrealized_pnl_pct=summary["total_unrealized_pnl_pct"],
            us_market_value=summary["market_breakdown"]["us"],
            hk_market_value=summary["market_breakdown"]["hk"],
            cn_market_value=summary["market_breakdown"]["cn"],
            sector_breakdown=summary["sector_breakdown"],
            active_positions_count=summary["active_positions_count"],
            watchlist_count=summary["watchlist_count"],
        )
        self.db.add(snapshot)
        await self.db.commit()
        await self.db.refresh(snapshot)
        logger.info("保存组合快照: date=%s, aum=%.2f", now.isoformat(), summary["total_aum"])
        return snapshot

    # ═══════════════════════════════════════════════════════
    # 云端分析数据对接
    # ═══════════════════════════════════════════════════════

    async def link_position_to_thesis(self, position_id: int, thesis_id: int) -> Optional[Position]:
        """将持仓关联到投资逻辑"""
        pos = await self.get_position(position_id)
        if not pos:
            return None
        pos.related_thesis_id = thesis_id
        await self.db.commit()
        return pos

    async def link_watchlist_to_thesis(self, item_id: int, thesis_id: int) -> Optional[WatchlistItem]:
        """将观察仓关联到投资逻辑"""
        item = await self.get_watchlist_item(item_id)
        if not item:
            return None
        item.related_thesis_id = thesis_id
        await self.db.commit()
        return item

    async def get_positions_with_analysis(self, market: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取持仓 + 关联的云端分析数据
        
        返回每个持仓的:
        - 基本信息 + 盈亏
        - 关联的 Thesis (投资逻辑)
        - 关联的 Company 分析摘要
        - 关联的 InfluencerSignal (大V信号，如果有)
        """
        positions = await self.list_positions(market=market, limit=1000)
        total_aum = 0.0
        for pos in positions:
            mv = pos.market_value
            if mv:
                total_aum += mv

        results = []
        for pos in positions:
            item = pos.to_dict(total_aum=total_aum)
            # 关联云端数据（此处为框架，实际需联表查询）
            item["linked_analysis"] = {
                "thesis_id": pos.related_thesis_id,
                "company_analysis_url": f"/api/company/{pos.ticker}" if pos.market != "US" else None,
                "industry_analysis_url": f"/api/industry/{pos.industry}" if pos.industry else None,
                "latest_news_count": 0,  # 待实现
                "influencer_signals": [],  # 待大V模块接入
            }
            results.append(item)
        return results

    # ═══════════════════════════════════════════════════════
    # 组合健康评分
    # ═══════════════════════════════════════════════════════

    # AI 相关标的识别关键字（ticker / sector / industry）
    AI_KEYWORDS = {"nvidia", "amd", "sivers", "sivef", "商汤", "优必选", "minimax", "0100", "ai", "semiconductor", "chip", "software", "technology", "robot"}
    # 防御性资产识别关键字
    DEFENSIVE_KEYWORDS = {"visa", "mastercard", "consumer", "healthcare", "pharma", "medical", "bank", "finance", "insurance", "utility", "reit"}

    async def calculate_health_score(self) -> Dict[str, Any]:
        """计算组合健康评分（100分制）

        评分维度：
        - AI集中度（25%）：AI相关标的权重，过高扣分
        - 港股占比（20%）：港股标的权重，过高扣分
        - 高亏损标的数量（20%）：亏损>20%的标的数量
        - 防御性资产比例（15%）：防御性标的占比，过低扣分
        - 现金预留（10%）：现金预留比例（暂取0）
        - 其他风险（10%）：单一标的集中度
        """
        positions = await self.list_positions(status="active", limit=1000)
        total_aum = 0.0
        for pos in positions:
            mv = pos.market_value
            if mv:
                total_aum += mv

        if total_aum <= 0:
            return {
                "score": 0,
                "grade": "N/A",
                "color": "gray",
                "breakdown": {},
                "suggestions": ["暂无持仓数据，无法计算健康评分"],
            }

        ai_weight = 0.0
        hk_weight = 0.0
        defensive_weight = 0.0
        high_loss_count = 0
        max_single_weight = 0.0
        cash_pct = 0.0  # 暂取0，后续可接入现金持仓

        for pos in positions:
            mv = pos.market_value or 0.0
            weight = (mv / total_aum) * 100 if total_aum > 0 else 0.0

            # 单一标的集中度
            if weight > max_single_weight:
                max_single_weight = weight

            # 港股占比
            if pos.market == "HK":
                hk_weight += weight

            # AI 集中度（通过 ticker、sector、industry 匹配）
            text = f"{pos.ticker} {pos.name} {pos.name_cn or ''} {pos.sector or ''} {pos.industry or ''}".lower()
            if any(kw in text for kw in self.AI_KEYWORDS):
                ai_weight += weight

            # 防御性资产
            if any(kw in text for kw in self.DEFENSIVE_KEYWORDS):
                defensive_weight += weight

            # 高亏损标的（亏损>20%）
            pnl_pct = pos.unrealized_pnl_pct or 0.0
            if pnl_pct < -20:
                high_loss_count += 1

        # ── 分项评分 ──
        def score_ai_concentration(w: float) -> int:
            if w <= 40:   return 25
            if w <= 55:   return 20
            if w <= 70:   return 12
            if w <= 85:   return 5
            return 0

        def score_hk_concentration(w: float) -> int:
            if w <= 40:   return 20
            if w <= 55:   return 15
            if w <= 70:   return 8
            if w <= 85:   return 3
            return 0

        def score_high_loss(n: int) -> int:
            if n == 0:   return 20
            if n == 1:   return 15
            if n == 2:   return 10
            if n == 3:   return 5
            return 0

        def score_defensive(w: float) -> int:
            if w >= 30:   return 15
            if w >= 20:   return 12
            if w >= 10:   return 8
            if w >= 5:    return 4
            return 0

        def score_cash(w: float) -> int:
            if w >= 20:   return 10
            if w >= 10:   return 8
            if w >= 5:    return 4
            return 0

        def score_concentration(w: float) -> int:
            if w <= 20:   return 10
            if w <= 30:   return 7
            if w <= 40:   return 4
            return 0

        scores = {
            "ai_concentration": {
                "label": "AI集中度",
                "weight": 25,
                "raw_value": round(ai_weight, 2),
                "raw_unit": "%",
                "score": score_ai_concentration(ai_weight),
                "max": 25,
                "suggestion": "AI标的占比过高，建议降低单一赛道集中度" if ai_weight > 55 else None,
            },
            "hk_concentration": {
                "label": "港股占比",
                "weight": 20,
                "raw_value": round(hk_weight, 2),
                "raw_unit": "%",
                "score": score_hk_concentration(hk_weight),
                "max": 20,
                "suggestion": "港股占比过高，建议增加美股或其他市场配置" if hk_weight > 55 else None,
            },
            "high_loss_count": {
                "label": "高亏损标的",
                "weight": 20,
                "raw_value": high_loss_count,
                "raw_unit": "只",
                "score": score_high_loss(high_loss_count),
                "max": 20,
                "suggestion": f"有{high_loss_count}只标的亏损超20%，建议检视止损策略" if high_loss_count > 0 else None,
            },
            "defensive_ratio": {
                "label": "防御性资产",
                "weight": 15,
                "raw_value": round(defensive_weight, 2),
                "raw_unit": "%",
                "score": score_defensive(defensive_weight),
                "max": 15,
                "suggestion": "防御性资产比例偏低，建议配置消费/医药等防御板块" if defensive_weight < 15 else None,
            },
            "cash_reserve": {
                "label": "现金预留",
                "weight": 10,
                "raw_value": round(cash_pct, 2),
                "raw_unit": "%",
                "score": score_cash(cash_pct),
                "max": 10,
                "suggestion": "现金预留不足，建议保持10%以上现金以应对波动" if cash_pct < 10 else None,
            },
            "concentration_risk": {
                "label": "集中度风险",
                "weight": 10,
                "raw_value": round(max_single_weight, 2),
                "raw_unit": "%",
                "score": score_concentration(max_single_weight),
                "max": 10,
                "suggestion": f"最大单一标的占比{max_single_weight:.1f}%，建议分散持仓" if max_single_weight > 30 else None,
            },
        }

        total_score = sum(v["score"] for v in scores.values())

        if total_score >= 80:
            grade, color = "健康", "green"
        elif total_score >= 60:
            grade, color = "关注", "yellow"
        else:
            grade, color = "风险", "red"

        suggestions = [v["suggestion"] for v in scores.values() if v["suggestion"]]
        if not suggestions:
            suggestions.append("组合健康度良好，继续保持")

        return {
            "score": total_score,
            "grade": grade,
            "color": color,
            "breakdown": scores,
            "suggestions": suggestions,
            "total_aum": round(total_aum, 2),
            "position_count": len(positions),
        }

    # ── 风险指标（夏普比率、最大回撤、波动率）──
    async def calculate_risk_metrics(self) -> Dict[str, Any]:
        """计算组合风险指标：夏普比率、最大回撤、波动率

        数据说明：
        - 无历史收益率数据，用持仓成本→当前价的年化收益率作为单期回报
        - 无风险利率假设 3%（中国 10 年期国债近似）
        - 最大回撤：用各持仓从成本到当前价的跌幅中的最大值
        """
        positions = await self.list_positions(status="active", limit=1000)
        if not positions:
            return {
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "volatility": 0.0,
                "annual_return": 0.0,
                "risk_free_rate": 3.0,
                "position_count": 0,
                "note": "暂无持仓数据",
            }

        # 假设无风险利率 3%
        RISK_FREE_RATE = 0.03

        # 计算各持仓的年化收益率（从成本到当前价）
        # 假设平均持仓周期 180 天（约半年）
        HOLDING_DAYS = 180

        returns = []
        weights = []
        total_aum = 0.0

        for pos in positions:
            mv = pos.market_value or 0
            if mv <= 0 or pos.avg_cost <= 0:
                continue
            total_aum += mv

            # 单期收益率 (当前价 - 成本) / 成本
            holding_return = (pos.current_price or pos.avg_cost) / pos.avg_cost - 1
            # 年化收益率
            annual_return = (1 + holding_return) ** (365 / HOLDING_DAYS) - 1
            returns.append(annual_return)
            weights.append(mv)

        if not returns or total_aum <= 0:
            return {
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "volatility": 0.0,
                "annual_return": 0.0,
                "risk_free_rate": RISK_FREE_RATE * 100,
                "position_count": len(positions),
                "note": "持仓数据不足，无法计算风险指标",
            }

        # 权重归一化
        weights = [w / total_aum for w in weights]

        # 加权平均年化收益率
        portfolio_return = sum(r * w for r, w in zip(returns, weights))

        # 波动率（加权年化收益率的标准差）
        # 单资产时 volatility = |return - Rf|（简化），多资产时计算加权标准差
        if len(returns) == 1:
            # 单只标的：用 |收益率 - 无风险利率| 作为波动率代理
            volatility = abs(returns[0] - RISK_FREE_RATE)
        else:
            # 多资产加权标准差
            mean_ret = portfolio_return
            variance = sum(w * (r - mean_ret) ** 2 for r, w in zip(returns, weights))
            volatility = variance ** 0.5

        # 夏普比率 = (组合年化收益率 - 无风险利率) / 波动率
        if volatility > 0:
            sharpe_ratio = (portfolio_return - RISK_FREE_RATE) / volatility
        else:
            sharpe_ratio = 0.0

        # 最大回撤：各持仓从成本到当前价的跌幅中的最大值
        drawdowns = []
        for pos in positions:
            if pos.avg_cost > 0 and pos.current_price is not None:
                dd = (pos.current_price - pos.avg_cost) / pos.avg_cost
                if dd < 0:
                    drawdowns.append(abs(dd))
        max_drawdown = max(drawdowns) if drawdowns else 0.0

        return {
            "sharpe_ratio": round(sharpe_ratio, 2),
            "max_drawdown": round(max_drawdown * 100, 2),  # 百分比
            "volatility": round(volatility * 100, 2),  # 百分比
            "annual_return": round(portfolio_return * 100, 2),  # 百分比
            "risk_free_rate": round(RISK_FREE_RATE * 100, 2),  # 百分比
            "position_count": len(positions),
            "holding_days": HOLDING_DAYS,
            "note": None,
        }

    # ── 相关性矩阵（近似相关性，基于行业/市场/标签）──
    async def calculate_correlation_matrix(self) -> Dict[str, Any]:
        """计算持仓标的之间的近似相关性矩阵

        由于无历史价格数据，使用行业/市场/标签相似度计算"近似相关性"：
        - 同市场：+0.3
        - 同行业：+0.4
        - 每共享一个标签：+0.2
        - 叠加后归一化到 [-1, 1]

        返回：
        - matrix: 每对标的的相关性系数列表
        - top_pairs: Top5 高相关性标的对（用于前端展示）
        - high_correlation_pairs: 相关性 >0.7 的标的对（风险提示）
        """
        positions = await self.list_positions(status="active", limit=1000)
        if not positions or len(positions) < 2:
            return {
                "matrix": [],
                "top_pairs": [],
                "high_correlation_pairs": [],
                "position_count": len(positions),
                "note": "持仓数量不足，无法计算相关性矩阵",
            }

        # 计算每对标的的相关性
        pairs = []
        n = len(positions)
        for i in range(n):
            for j in range(i + 1, n):
                pos_a = positions[i]
                pos_b = positions[j]

                correlation = 0.0

                # 同市场 +0.3
                if pos_a.market == pos_b.market:
                    correlation += 0.3

                # 同行业 +0.4
                if pos_a.sector and pos_b.sector and pos_a.sector == pos_b.sector:
                    correlation += 0.4

                # 共享标签：每共享一个 +0.2
                tags_a = set(pos_a.tags or [])
                tags_b = set(pos_b.tags or [])
                shared_tags = tags_a & tags_b
                correlation += len(shared_tags) * 0.2

                # 归一化到 [-1, 1]（理论上最大值约 1.3，简单 clamp）
                correlation = min(correlation, 1.0)

                pairs.append({
                    "ticker_a": pos_a.ticker,
                    "name_a": pos_a.name_cn or pos_a.name,
                    "ticker_b": pos_b.ticker,
                    "name_b": pos_b.name_cn or pos_b.name,
                    "market": pos_a.market if pos_a.market == pos_b.market else "mixed",
                    "shared_tags": list(shared_tags),
                    "shared_sector": pos_a.sector if pos_a.sector == pos_b.sector else None,
                    "correlation": round(correlation, 2),
                })

        # 按相关性降序排序
        pairs.sort(key=lambda x: x["correlation"], reverse=True)

        # Top5 高相关性
        top_pairs = pairs[:5]

        # 高相关性（>0.7）的风险提示
        high_correlation_pairs = [p for p in pairs if p["correlation"] > 0.7]

        return {
            "matrix": pairs,
            "top_pairs": top_pairs,
            "high_correlation_pairs": high_correlation_pairs,
            "position_count": n,
            "note": None,
        }
