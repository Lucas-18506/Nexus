"""Report service for generating various types of reports."""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession


class ReportService:
    """Service for generating and retrieving reports."""
    
    def __init__(self, db_session: AsyncSession) -> None:
        self._db = db_session
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        from app.models.macro import MacroIndicator
        from app.models.stock import StockQuote
        from app.models.news import News, Event
        from app.models.report import Report
        try:
            macro_result = await self._db.execute(
                select(MacroIndicator).order_by(desc(MacroIndicator.collected_at)).limit(6)
            )
            macro_indicators = [
                {
                    "name": m.indicator_name,
                    "value": float(m.current_value) if m.current_value is not None else None,
                    "unit": m.unit,
                    "change": round(float(m.current_value) - float(m.previous_value or m.current_value), 2)
                    if m.current_value and m.previous_value else None,
                }
                for m in macro_result.scalars().all()
            ]
            
            key_tickers = ["NVDA", "TSLA", "AAPL", "MSFT", "AMD", "COIN"]
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
                        "change": q.change,
                        "change_percent": q.change_percent,
                    })
            
            news_result = await self._db.execute(
                select(News).order_by(desc(News.impact_level)).limit(10)
            )
            top_news = [
                {
                    "title": n.title,
                    "source": n.source,
                    "sentiment": n.sentiment,
                    "impact_level": n.impact_level,
                    "related_tickers": n.related_tickers,
                }
                for n in news_result.scalars().all()
            ]
            
            events_result = await self._db.execute(
                select(Event).where(Event.created_at >= datetime.now() - timedelta(days=1))
                .order_by(desc(Event.impact_level)).limit(5)
            )
            recent_events = [
                {"title": e.title, "type": e.event_type, "impact_level": e.impact_level}
                for e in events_result.scalars().all()
            ]
            
            sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
            for n in top_news:
                s = n.get("sentiment", "neutral")
                if s in sentiment_counts:
                    sentiment_counts[s] += 1
            
            total = sum(sentiment_counts.values()) or 1
            market_mood = "neutral"
            if sentiment_counts["positive"] / total > 0.5:
                market_mood = "bullish"
            elif sentiment_counts["negative"] / total > 0.5:
                market_mood = "bearish"
            
            content_lines = [
                f"# Daily Market Report - {datetime.now().strftime('%Y-%m-%d')}",
                f"", f"## Market Mood: {market_mood.upper()}", f"", f"## Macro Indicators",
            ]
            for m in macro_indicators:
                content_lines.append(f"- {m['name']}: {m['value']} {m['unit']} (change: {m['change']})")
            content_lines.extend(["", "## Key Stocks"])
            for s in stocks:
                content_lines.append(f"- {s['ticker']}: {s['price']} ({s['change_percent']}%)")
            content_lines.extend(["", "## Top News"])
            for n in top_news[:5]:
                content_lines.append(f"- [{n['sentiment']}] {n['title']}")
            content = "\n".join(content_lines)
            
            key_points = [
                f"Market mood: {market_mood}",
                f"Macro indicators tracked: {len(macro_indicators)}",
                f"Key stocks monitored: {len(stocks)}",
                f"Top news items: {len(top_news)}",
                f"Recent events: {len(recent_events)}",
            ]
            
            report_data = {
                "report_type": "daily",
                "title": f"Daily Market Report - {datetime.now().strftime('%Y-%m-%d')}",
                "content": content,
                "summary": f"Daily market summary. Mood: {market_mood}. {len(stocks)} stocks, {len(top_news)} news items.",
                "key_points": key_points,
                "confidence_overall": 0.7,
                "generated_at": datetime.utcnow().isoformat(),
                "market_mood": market_mood,
                "sentiment_distribution": sentiment_counts,
                "macro_indicators": macro_indicators,
                "key_stocks": stocks,
                "top_news": top_news,
                "recent_events": recent_events,
            }
            
            await self._store_report(report_data)
            return report_data
        except Exception as e:
            print(f"Error generating daily report: {e}")
            return {"report_type": "daily", "title": f"Daily Market Report - {datetime.now().strftime('%Y-%m-%d')}",
                    "content": f"Error: {e}", "error": str(e), "generated_at": datetime.utcnow().isoformat()}
    
    async def generate_opportunity_report(self) -> Dict[str, Any]:
        from app.models.stock import StockQuote
        from app.models.news import News, Event
        from app.models.report import Report
        try:
            news_result = await self._db.execute(
                select(News).where(News.sentiment == "positive")
                .order_by(desc(News.impact_level)).limit(20)
            )
            positive_news = news_result.scalars().all()
            
            ticker_sentiment: Dict[str, Dict[str, Any]] = {}
            for news in positive_news:
                for ticker in (news.related_tickers or []):
                    if ticker not in ticker_sentiment:
                        ticker_sentiment[ticker] = {"ticker": ticker, "positive_count": 0, "total_impact": 0, "news": []}
                    ticker_sentiment[ticker]["positive_count"] += 1
                    ticker_sentiment[ticker]["total_impact"] += (news.impact_level or 0)
                    if len(ticker_sentiment[ticker]["news"]) < 3:
                        ticker_sentiment[ticker]["news"].append(news.title)
            
            sorted_tickers = sorted(ticker_sentiment.values(), key=lambda x: x["total_impact"], reverse=True)[:10]
            opportunities = []
            for item in sorted_tickers:
                quote_result = await self._db.execute(
                    select(StockQuote).where(StockQuote.ticker == item["ticker"])
                    .order_by(desc(StockQuote.updated_at)).limit(1)
                )
                quote = quote_result.scalar_one_or_none()
                opportunities.append({
                    "ticker": item["ticker"],
                    "positive_signals": item["positive_count"],
                    "impact_score": item["total_impact"],
                    "latest_price": quote.price if quote else None,
                    "price_change_pct": quote.change_percent if quote else None,
                    "supporting_news": item["news"],
                    "opportunity_type": "sentiment_momentum",
                })
            
            events_result = await self._db.execute(
                select(Event).where(Event.created_at >= datetime.now() - timedelta(days=7))
                .order_by(desc(Event.impact_level)).limit(10)
            )
            emerging_themes = [
                {"theme": e.title, "type": e.event_type, "impact_level": e.impact_level, "tickers": e.related_companies}
                for e in events_result.scalars().all()
            ]
            
            content_lines = [
                f"# Investment Opportunity Report - {datetime.now().strftime('%Y-%m-%d')}",
                f"", f"## Summary", f"Found {len(opportunities)} opportunities based on positive sentiment analysis.",
                f"", f"## Top Opportunities",
            ]
            for opp in opportunities[:5]:
                content_lines.append(f"- **{opp['ticker']}**: {opp['positive_signals']} positive signals, impact score {opp['impact_score']}")
            content_lines.extend(["", "## Emerging Themes"])
            for theme in emerging_themes[:5]:
                content_lines.append(f"- {theme['theme']} (type: {theme['type']})")
            content = "\n".join(content_lines)
            
            report_data = {
                "report_type": "opportunity",
                "title": f"Investment Opportunity Report - {datetime.now().strftime('%Y-%m-%d')}",
                "content": content,
                "summary": f"Found {len(opportunities)} opportunities based on positive sentiment analysis",
                "key_points": [f"{len(opportunities)} sentiment-driven opportunities identified"] + [f"Theme: {t['theme']}" for t in emerging_themes[:3]],
                "confidence_overall": 0.6,
                "generated_at": datetime.utcnow().isoformat(),
                "opportunities": opportunities,
                "emerging_themes": emerging_themes,
            }
            await self._store_report(report_data)
            return report_data
        except Exception as e:
            print(f"Error generating opportunity report: {e}")
            return {"report_type": "opportunity", "title": f"Investment Opportunity Report - {datetime.now().strftime('%Y-%m-%d')}",
                    "content": f"Error: {e}", "error": str(e), "generated_at": datetime.utcnow().isoformat()}
    
    async def generate_industry_report(self, industry_id: int) -> Dict[str, Any]:
        from app.models.industry import Industry
        from app.models.company import Company
        from app.models.news import News
        from app.models.thesis import Thesis
        from app.models.report import Report
        try:
            industry_result = await self._db.execute(
                select(Industry).where(Industry.id == industry_id)
            )
            industry = industry_result.scalar_one_or_none()
            if not industry:
                return {"report_type": "industry", "error": f"Industry {industry_id} not found"}
            
            company_result = await self._db.execute(
                select(Company).where(Company.industry_id == industry_id).order_by(Company.name)
            )
            companies = [{"id": c.id, "ticker": c.ticker, "market": c.market, "name": c.name}
                         for c in company_result.scalars().all()]
            
            news_result = await self._db.execute(
                select(News).where(News.related_industries.contains([industry.name]))
                .order_by(desc(News.collected_at)).limit(10)
            )
            related_news = [{"title": n.title, "sentiment": n.sentiment, "impact_level": n.impact_level}
                            for n in news_result.scalars().all()]
            
            thesis_result = await self._db.execute(
                select(Thesis).where(Thesis.related_industry == industry.name)
                .order_by(desc(Thesis.confidence)).limit(5)
            )
            theses = [{"id": t.id, "title": t.title, "confidence": float(t.confidence) if t.confidence is not None else None, "status": t.status}
                      for t in thesis_result.scalars().all()]
            
            content_lines = [
                f"# Industry Report: {industry.name}",
                f"", f"## Overview", f"{industry.description or 'No description available.'}",
                f"", f"- Lifecycle Stage: {industry.lifecycle_stage or 'N/A'}",
                f"- Key Drivers: {', '.join(industry.key_drivers or [])}",
                f"", f"## Companies ({len(companies)})",
            ]
            for c in companies:
                content_lines.append(f"- {c['name']} ({c['ticker']}.{c['market']})")
            content_lines.extend(["", "## Related News"])
            for n in related_news[:5]:
                content_lines.append(f"- [{n['sentiment']}] {n['title']}")
            content_lines.extend(["", "## Active Theses"])
            for t in theses:
                content_lines.append(f"- {t['title']} (confidence: {t['confidence']}, status: {t['status']})")
            content = "\n".join(content_lines)
            
            report_data = {
                "report_type": "industry",
                "title": f"Industry Report: {industry.name}",
                "content": content,
                "summary": f"Industry analysis for {industry.name}. {len(companies)} companies, {len(related_news)} news items, {len(theses)} active theses.",
                "key_points": (industry.key_drivers or []) + (industry.opportunities or [])[:3],
                "confidence_overall": 0.75,
                "generated_at": datetime.utcnow().isoformat(),
                "industry": {
                    "id": industry.id, "name": industry.name, "description": industry.description,
                    "lifecycle_stage": industry.lifecycle_stage, "key_drivers": industry.key_drivers,
                    "supply_chain": industry.supply_chain, "bottleneck": industry.bottleneck,
                    "risk_factors": industry.risk_factors, "opportunities": industry.opportunities,
                },
                "companies": companies, "related_news": related_news, "active_theses": theses,
            }
            await self._store_report(report_data)
            return report_data
        except Exception as e:
            print(f"Error generating industry report: {e}")
            return {"report_type": "industry", "industry_id": industry_id,
                    "content": f"Error: {e}", "error": str(e), "generated_at": datetime.utcnow().isoformat()}
    
    async def get_report_history(self, report_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        from app.models.report import Report
        try:
            query = select(Report).order_by(desc(Report.created_at))
            if report_type:
                query = query.where(Report.report_type == report_type)
            query = query.limit(limit)
            result = await self._db.execute(query)
            return [{"id": row.id, "report_type": row.report_type, "title": row.title,
                     "created_at": row.created_at.isoformat() if row.created_at else None}
                    for row in result.scalars().all()]
        except Exception as e:
            print(f"Error getting report history: {e}")
            return []
    
    async def get_report(self, report_id: int) -> Optional[Dict[str, Any]]:
        from app.models.report import Report
        try:
            result = await self._db.execute(select(Report).where(Report.id == report_id))
            row = result.scalar_one_or_none()
            if row:
                return {
                    "id": row.id, "report_type": row.report_type, "title": row.title,
                    "content": row.content, "summary": row.summary,
                    "key_points": row.key_points,
                    "confidence_overall": float(row.confidence_overall) if row.confidence_overall is not None else None,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                }
        except Exception as e:
            print(f"Error getting report {report_id}: {e}")
        return None
    
    async def _store_report(self, data: Dict[str, Any]) -> None:
        from app.models.report import Report
        try:
            report = Report(
                report_type=data["report_type"],
                title=data["title"],
                content=data.get("content", ""),
                summary=data.get("summary"),
                key_points=data.get("key_points"),
                confidence_overall=data.get("confidence_overall", 0.5),
            )
            self._db.add(report)
            await self._db.commit()
        except Exception as e:
            await self._db.rollback()
            print(f"Error storing report: {e}")
