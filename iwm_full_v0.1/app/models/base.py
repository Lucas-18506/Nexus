"""SQLAlchemy declarative base for all models.

统一从 app.core.database 导入 Base，避免循环导入。
"""

from app.core.database import Base

__all__ = ["Base"]
