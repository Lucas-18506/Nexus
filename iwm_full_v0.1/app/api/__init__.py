"""API路由模块 - 导出所有子路由"""
from app.api import data
from app.api import news
from app.api import kb
from app.api import thesis
from app.api import report
from app.api import agent
from app.api import portfolio
from app.api import analysis
from app.api import signals
from app.api import cache

__all__ = ["data", "news", "kb", "thesis", "report", "agent", "portfolio", "analysis", "signals", "cache"]
