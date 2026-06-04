"""Data processors."""

from app.data_collection.processors.base import BaseProcessor
from app.data_collection.processors.news_processor import NewsProcessor

__all__ = [
    "BaseProcessor",
    "NewsProcessor",
]
