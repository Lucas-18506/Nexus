"""Data service layer for querying collected data."""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession


class DataService:
    """Service for accessing collected financial data."""
    
    def __init__(self, db_session: AsyncSession) -> None:
        self._db = db_session
    
    async def get_macro_indicators(
        self,
        indicator_type: Optional[str] = None,
        country: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        from app.models.macro import MacroIndicator
        try:
            query = select(MacroIndicator).order_by(desc(MacroIndicator.collected_at))
            conditions = []
            if indicator_type:
                conditions.append(MacroIndicator.indicator_type == indicator_type)
            if country:
                conditions.append(MacroIndicator.country == country)
            if conditions:
                query = query.where(and_(*conditions))
            query = query.limit(limit)
            result = await self._db.execute(query)
            return [
                {
                    "id": row.id,
                    "indicator_name": row.indicator_name,
                    "indicator_type": row.indicator_type,
                    "country": row.country,
                    "current_value": float(row.current_value) if row.current_value is not None else None,
                    "previous_value": float(row.previous_value) if row.previous_value is not None else None,
                    "unit": row.unit,
                    "source": row.source,
                    "collected_at": row.collected_at.isoformat() if row.collected_at else None,
                }
                for row in result.scalars().all()
            ]
        except Exception as e:
            print(f"Error getting macro indicators: {e}")
            return []
    
    async def get_stock_data(
        self,
        ticker: str,
        market: str,
        period: str = "1y",
    ) -> Dict[str, Any]:
        from app.models.stock import StockPrice, StockFundamental, StockQuote
        try:
            quote_result = await self._db.execute(
                select(StockQuote)
                .where(StockQuote.ticker == ticker, StockQuote.market == market)
                .order_by(desc(StockQuote.updated_at))
                .limit(1)
            )
            quote_row = quote_result.scalar_one_or_none()
            
            fund_result = await self._db.execute(
                select(StockFundamental)
                .where(StockFundamental.ticker == ticker, StockFundamental.market == market)
                .order_by(desc(StockFundamental.updated_at))
                .limit(1)
            )
            fund_row = fund_result.scalar_one_or_none()
            
            period_days_map = {"1m": 30, "3m": 90, "6m": 180, "1y": 365, "2y": 730, "5y": 1825}
            days = period_days_map.get(period, 365)
            start_date = datetime.now() - timedelta(days=days)
            
            price_result = await self._db.execute(
                select(StockPrice)
                .where(
                    StockPrice.ticker == ticker,
                    StockPrice.market == market,
                    StockPrice.trade_date >= start_date.date(),
                )
                .order_by(StockPrice.trade_date)
            )
            prices = price_result.scalars().all()
            
            return {
                "ticker": ticker,
                "market": market,
                "period": period,
                "quote": {
                    "price": quote_row.price if quote_row else None,
                    "change": quote_row.change if quote_row else None,
                    "change_percent": quote_row.change_percent if quote_row else None,
                    "volume": quote_row.volume if quote_row else None,
                    "updated_at": quote_row.updated_at.isoformat() if quote_row else None,
                } if quote_row else None,
                "fundamentals": {
                    "pe_ttm": fund_row.pe_ttm if fund_row else None,
                    "pb": fund_row.pb if fund_row else None,
                    "ps_ttm": fund_row.ps_ttm if fund_row else None,
                    "market_cap": fund_row.market_cap if fund_row else None,
                    "profit_margin": fund_row.profit_margin if fund_row else None,
                    "roe": fund_row.roe if fund_row else None,
                } if fund_row else None,
                "prices": [
                    {
                        "date": p.trade_date.isoformat() if p.trade_date else None,
                        "open": p.open_price,
                        "high": p.high_price,
                        "low": p.low_price,
                        "close": p.close_price,
                        "volume": p.volume,
                    }
                    for p in prices
                ],
            }
        except Exception as e:
            print(f"Error getting stock data for {ticker}: {e}")
            return {"ticker": ticker, "market": market, "error": str(e)}
    
    async def get_market_summary(self) -> Dict[str, Any]:
        from app.models.macro import MacroIndicator
        from app.models.stock import StockQuote
        from app.models.news import News
        try:
            macro_result = await self._db.execute(
                select(MacroIndicator).order_by(desc(MacroIndicator.collected_at)).limit(10)
            )
            macro = [
                {
                    "name": m.indicator_name,
                    "value": float(m.current_value) if m.current_value is not None else None,
                    "unit": m.unit,
                    "change": round(float(m.current_value) - float(m.previous_value or m.current_value), 3)
                    if m.current_value and m.previous_value else None,
                }
                for m in macro_result.scalars().all()
            ]
            
            key_tickers = ["NVDA", "TSLA", "AAPL", "MSFT", "AMD"]
            stocks = []
            for ticker in key_tickers:
                quote_result = await self._db.execute(
                    select(StockQuote)
                    .where(StockQuote.ticker == ticker, StockQuote.market == "US")
                    .order_by(desc(StockQuote.updated_at))
                    .limit(1)
                )
                q = quote_result.scalar_one_or_none()
                if q:
                    stocks.append({
                        "ticker": q.ticker,
                        "price": q.price,
                        "change_percent": q.change_percent,
                    })
            
            news_result = await self._db.execute(
                select(func.count(News.id)).where(
                    News.collected_at >= datetime.now() - timedelta(hours=24)
                )
            )
            news_count_24h = news_result.scalar() or 0
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "macro": macro,
                "key_stocks": stocks,
                "news_count_24h": news_count_24h,
            }
        except Exception as e:
            print(f"Error getting market summary: {e}")
            return {"timestamp": datetime.utcnow().isoformat(), "error": str(e)}
    
    async def get_news(
        self,
        category: Optional[str] = None,
        limit: int = 20,
        processed: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        from app.models.news import News
        try:
            query = select(News).order_by(desc(News.collected_at))
            conditions = []
            if category:
                conditions.append(News.category == category)
            if processed is not None:
                conditions.append(News.processed == processed)
            if conditions:
                query = query.where(and_(*conditions))
            query = query.limit(limit)
            result = await self._db.execute(query)
            return [
                {
                    "id": row.id,
                    "title": row.title,
                    "content": row.content,
                    "source": row.source,
                    "url": row.url,
                    "published_at": row.published_at.isoformat() if row.published_at else None,
                    "category": row.category,
                    "related_tickers": row.related_tickers,
                    "related_industries": row.related_industries,
                    "sentiment": row.sentiment,
                    "impact_level": row.impact_level,
                    "processed": row.processed,
                }
                for row in result.scalars().all()
            ]
        except Exception as e:
            print(f"Error getting news: {e}")
            return []
    
    async def get_recent_events(
        self,
        days: int = 7,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        from app.models.news import Event
        try:
            start_date = datetime.now() - timedelta(days=days)
            result = await self._db.execute(
                select(Event)
                .where(Event.created_at >= start_date)
                .order_by(desc(Event.created_at))
                .limit(limit)
            )
            return [
                {
                    "id": row.id,
                    "title": row.title,
                    "summary": row.summary,
                    "event_type": row.event_type,
                    "impact_level": row.impact_level,
                    "related_industries": row.related_industries,
                    "related_companies": row.related_companies,
                    "event_date": row.event_date.isoformat() if row.event_date else None,
                }
                for row in result.scalars().all()
            ]
        except Exception as e:
            print(f"Error getting recent events: {e}")
            return []
