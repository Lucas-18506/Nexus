"""APScheduler task definitions for data collection."""

import asyncio
from typing import Dict, Any, Callable, Coroutine

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
    AP_SCHEDULER_AVAILABLE = True
except ImportError:
    AP_SCHEDULER_AVAILABLE = False
    AsyncIOScheduler = None
    CronTrigger = None
    IntervalTrigger = None

from app.data_collection.collectors.macro_collector import MacroCollector
from app.data_collection.collectors.stock_collector import StockCollector
from app.data_collection.collectors.news_collector import NewsCollector


# Default tickers for scheduled collection
DEFAULT_STOCK_TICKERS = [
    ("NVDA", "US"), ("TSLA", "US"), ("AAPL", "US"),
    ("MSFT", "US"), ("AMD", "US"), ("COIN", "US"),
    ("0700.HK", "HK"), ("9988.HK", "HK"), ("1211.HK", "HK"),
]

DEFAULT_MACRO_INDICATORS = [
    "US_10Y_Yield", "US_2Y_Yield", "DXY",
    "USD_CNY", "CPI_US", "PMI_China",
]


async def task_macro_daily() -> None:
    """Daily macro data collection task (runs at 8:00)."""
    print("[Scheduler] Starting daily macro data collection...")
    try:
        collector = MacroCollector()
        results = await collector.collect_batch(DEFAULT_MACRO_INDICATORS)
        print(f"[Scheduler] Collected {len(results)} macro indicators")
        for r in results:
            print(f"  - {r['indicator_name']}: {r['current_value']} {r['unit']}")
    except Exception as e:
        print(f"[Scheduler] Macro daily task failed: {e}")


async def task_stock_eod() -> None:
    """End-of-day stock data collection task (runs at 16:30)."""
    print("[Scheduler] Starting EOD stock data collection...")
    try:
        collector = StockCollector()
        results = []
        for ticker, market in DEFAULT_STOCK_TICKERS:
            try:
                quote = await collector.get_stock_quote(ticker, market)
                results.append(quote)
                print(f"  - {ticker} ({market}): {quote['price']} "
                      f"({quote['change_percent']}%)")
            except Exception as te:
                print(f"  - Error collecting {ticker}: {te}")
        print(f"[Scheduler] Collected {len(results)} stock quotes")
    except Exception as e:
        print(f"[Scheduler] Stock EOD task failed: {e}")


async def task_news_regular() -> None:
    """Regular news collection task (runs every 4 hours)."""
    print("[Scheduler] Starting regular news collection...")
    try:
        collector = NewsCollector()
        
        # Collect macro news
        macro_news = await collector.collect_macro_news()
        print(f"[Scheduler] Collected {len(macro_news)} macro news items")
        
        # Collect industry news for key sectors
        industries = ["AI", "半导体", "新能源汽车", "消费电子"]
        for industry in industries:
            try:
                news = await collector.collect_industry_news(industry)
                print(f"  - {industry}: {len(news)} items")
            except Exception as ie:
                print(f"  - Error collecting {industry} news: {ie}")
        
        # Collect ticker-specific news
        for ticker, market in DEFAULT_STOCK_TICKERS[:3]:
            try:
                news = await collector.collect_by_ticker(ticker, market)
                print(f"  - {ticker}: {len(news)} items")
            except Exception as te:
                print(f"  - Error collecting {ticker} news: {te}")
                
    except Exception as e:
        print(f"[Scheduler] News regular task failed: {e}")


async def task_daily_report() -> None:
    """Daily report generation trigger (runs at 9:00)."""
    print("[Scheduler] Triggering daily report generation...")
    try:
        # Collect all necessary data for the daily report
        macro_collector = MacroCollector()
        stock_collector = StockCollector()
        news_collector = NewsCollector()
        
        # Gather macro data
        macro_data = await macro_collector.collect_batch(DEFAULT_MACRO_INDICATORS)
        
        # Gather stock quotes
        stock_quotes = []
        for ticker, market in DEFAULT_STOCK_TICKERS:
            try:
                quote = await stock_collector.get_stock_quote(ticker, market)
                stock_quotes.append(quote)
            except Exception:
                pass
        
        # Gather news
        news = await news_collector.collect_macro_news()
        
        print(f"[Scheduler] Daily report data ready: "
              f"{len(macro_data)} macro, {len(stock_quotes)} stocks, {len(news)} news")
        
    except Exception as e:
        print(f"[Scheduler] Daily report task failed: {e}")


# Task definitions configuration
TASKS: Dict[str, Dict[str, Any]] = {
    "macro_daily": {
        "id": "macro_daily",
        "name": "Daily Macro Data Collection",
        "func": task_macro_daily,
        "trigger": "cron",
        "hour": 8,
        "minute": 0,
    },
    "stock_eod": {
        "id": "stock_eod",
        "name": "End-of-Day Stock Collection",
        "func": task_stock_eod,
        "trigger": "cron",
        "hour": 16,
        "minute": 30,
    },
    "news_regular": {
        "id": "news_regular",
        "name": "Regular News Collection",
        "func": task_news_regular,
        "trigger": "interval",
        "hours": 4,
    },
    "daily_report": {
        "id": "daily_report",
        "name": "Daily Report Generation",
        "func": task_daily_report,
        "trigger": "cron",
        "hour": 9,
        "minute": 0,
    },
}


def create_scheduler() -> "AsyncIOScheduler":
    """Factory function to create and configure the AsyncIOScheduler.
    
    Returns:
        Configured AsyncIOScheduler instance with all tasks registered.
    """
    if not AP_SCHEDULER_AVAILABLE:
        raise ImportError(
            "APScheduler is not installed. "
            "Install it with: pip install apscheduler"
        )
    
    scheduler = AsyncIOScheduler()
    
    for task_name, task_config in TASKS.items():
        trigger_type = task_config["trigger"]
        func = task_config["func"]
        
        if trigger_type == "cron":
            trigger = CronTrigger(
                hour=task_config["hour"],
                minute=task_config["minute"],
            )
        elif trigger_type == "interval":
            trigger = IntervalTrigger(hours=task_config["hours"])
        else:
            continue
        
        scheduler.add_job(
            func=func,
            trigger=trigger,
            id=task_config["id"],
            name=task_config["name"],
            replace_existing=True,
        )
        print(f"[Scheduler] Registered task: {task_config['name']} "
              f"({trigger_type})")
    
    return scheduler
