from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.signal_service import SignalService
from app.models.signal import Signal, SignalAction, SignalStatus

router = APIRouter(prefix="/signals", tags=["signals"])


class SignalCreate(BaseModel):
    """创建信号请求体"""
    symbol: str = Field(..., min_length=1, max_length=32)
    market: str = Field(default="US", max_length=8)
    action: str = Field(..., max_length=16)
    reason: Optional[str] = Field(None, max_length=2000)
    confidence: int = Field(default=50, ge=0, le=100)
    source: Optional[str] = Field(None, max_length=128)


class SignalUpdateStatus(BaseModel):
    status: str = Field(..., max_length=16)


class SignalResponse(BaseModel):
    id: int
    symbol: str
    market: str
    action: str
    reason: Optional[str]
    confidence: int
    source: Optional[str]
    status: str
    created_at: Optional[str]

    class Config:
        from_attributes = True


@router.get("", response_model=List[SignalResponse])
async def list_signals(
    symbol: Optional[str] = Query(None, max_length=32),
    market: Optional[str] = Query(None, max_length=8),
    action: Optional[str] = Query(None, max_length=16),
    status: Optional[str] = Query(None, max_length=16),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """列出所有交易信号"""
    signals = await SignalService.list_signals(
        db=db,
        symbol=symbol,
        market=market,
        action=action,
        status=status,
        limit=limit,
        offset=offset,
    )
    return [
        SignalResponse(
            id=s.id,
            symbol=s.symbol,
            market=s.market,
            action=s.action,
            reason=s.reason,
            confidence=s.confidence,
            source=s.source,
            status=s.status,
            created_at=s.created_at.isoformat() if s.created_at else None,
        )
        for s in signals
    ]


@router.post("", response_model=SignalResponse, status_code=201)
async def create_signal(
    payload: SignalCreate,
    db: AsyncSession = Depends(get_db),
):
    """创建新信号（供大V监测推送Timing分析时使用）"""
    signal = await SignalService.create_signal(
        db=db,
        symbol=payload.symbol,
        market=payload.market,
        action=payload.action,
        reason=payload.reason,
        confidence=payload.confidence,
        source=payload.source,
    )
    return SignalResponse(
        id=signal.id,
        symbol=signal.symbol,
        market=signal.market,
        action=signal.action,
        reason=signal.reason,
        confidence=signal.confidence,
        source=signal.source,
        status=signal.status,
        created_at=signal.created_at.isoformat() if signal.created_at else None,
    )


@router.patch("/{signal_id}/status", response_model=SignalResponse)
async def update_signal_status(
    signal_id: int,
    payload: SignalUpdateStatus,
    db: AsyncSession = Depends(get_db),
):
    """更新信号状态（采纳/忽略）"""
    signal = await SignalService.update_status(db, signal_id, payload.status)
    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")
    return SignalResponse(
        id=signal.id,
        symbol=signal.symbol,
        market=signal.market,
        action=signal.action,
        reason=signal.reason,
        confidence=signal.confidence,
        source=signal.source,
        status=signal.status,
        created_at=signal.created_at.isoformat() if signal.created_at else None,
    )
