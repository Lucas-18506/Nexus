"""Data collectors."""

from app.data_collection.collectors.base import BaseCollector
from app.data_collection.collectors.macro_collector import MacroCollector
from app.data_collection.collectors.stock_collector import StockCollector
from app.data_collection.collectors.news_collector import NewsCollector

__all__ = [
    "BaseCollector",
    "MacroCollector",
    "StockCollector",
    "NewsCollector",
]
