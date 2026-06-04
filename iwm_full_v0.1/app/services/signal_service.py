from typing import Optional, List
from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal, SignalAction, SignalStatus


class SignalService:
    """信号服务 - 最小化版本"""

    @staticmethod
    async def list_signals(
        db: AsyncSession,
        symbol: Optional[str] = None,
        market: Optional[str] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Signal]:
        """列出信号"""
        stmt = select(Signal).order_by(desc(Signal.created_at))
        conditions = []
        if symbol:
            conditions.append(Signal.symbol == symbol)
        if market:
            conditions.append(Signal.market == market)
        if action:
            conditions.append(Signal.action == action)
        if status:
            conditions.append(Signal.status == status)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.limit(limit).offset(offset)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_signal(
        db: AsyncSession,
        symbol: str,
        market: str,
        action: str,
        reason: Optional[str] = None,
        confidence: int = 50,
        source: Optional[str] = None,
    ) -> Signal:
        """创建新信号"""
        signal = Signal(
            symbol=symbol.upper().strip(),
            market=market.upper().strip(),
            action=action.lower().strip(),
            reason=reason,
            confidence=max(0, min(100, confidence)),
            source=source,
            status=SignalStatus.ACTIVE.value,
        )
        db.add(signal)
        await db.commit()
        await db.refresh(signal)
        return signal

    @staticmethod
    async def update_status(
        db: AsyncSession,
        signal_id: int,
        status: str,
    ) -> Optional[Signal]:
        """更新信号状态（采纳/忽略）"""
        signal = await db.get(Signal, signal_id)
        if not signal:
            return None
        from datetime import datetime, timezone
        signal.status = status
        if status == SignalStatus.EXECUTED.value:
            signal.executed_at = datetime.now(timezone.utc)
        elif status == SignalStatus.DISMISSED.value:
            signal.dismissed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(signal)
        return signal
