"""Data collection module.

This module provides data collectors and processors for gathering
financial data from various sources.
"""

from app.data_collection.collectors import (
    BaseCollector,
    MacroCollector,
    StockCollector,
    NewsCollector,
)
from app.data_collection.processors import (
    BaseProcessor,
    NewsProcessor,
)
from app.data_collection.scheduler_tasks import (
    create_scheduler,
    task_macro_daily,
    task_stock_eod,
    task_news_regular,
    task_daily_report,
    TASKS,
)

__all__ = [
    # Collectors
    "BaseCollector",
    "MacroCollector",
    "StockCollector",
    "NewsCollector",
    # Processors
    "BaseProcessor",
    "NewsProcessor",
    # Scheduler
    "create_scheduler",
    "task_macro_daily",
    "task_stock_eod",
    "task_news_regular",
    "task_daily_report",
    "TASKS",
]
