"""Application configuration using Pydantic Settings."""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    数据库支持两种模式：
    - 开发环境：SQLite（无需安装 PostgreSQL）
    - 生产环境（Render/Railway）：PostgreSQL via DATABASE_URL
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── 数据库配置 ──
    # 优先使用 DATABASE_URL（Render/Railway 等云平台自动注入）
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    
    # 开发模式开关：设置 USE_SQLITE=true 使用 SQLite
    use_sqlite: bool = Field(default=False, alias="USE_SQLITE")
    sqlite_path: str = Field(default="./iwm.db", alias="SQLITE_PATH")
    
    # 如果不用 DATABASE_URL，用分量配置（本地 PostgreSQL）
    postgres_user: str = Field(default="postgres")
    postgres_password: str = Field(default="postgres")
    postgres_host: str = Field(default="localhost")
    postgres_port: int = Field(default=5432)
    postgres_db: str = Field(default="iwm")

    # ── Qdrant ──
    qdrant_host: str = Field(default="localhost")
    qdrant_port: int = Field(default=6333)
    qdrant_api_key: Optional[str] = Field(default=None)

    # ── OpenAI ──
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o")
    openai_embedding_model: str = Field(default="text-embedding-3-small")

    # ── API Server ──
    api_port: int = Field(default=8000)
    api_host: str = Field(default="0.0.0.0")

    # ── Logging ──
    log_level: str = Field(default="INFO")
    
    # ── 分析报告目录 ──
    analysis_reports_dir: str = Field(default="./analysis_reports")
    
    # ── 缓存目录 ──
    cache_dir: str = Field(default="./cache", alias="CACHE_DIR")

    @property
    def is_postgres(self) -> bool:
        """是否使用 PostgreSQL"""
        if self.database_url:
            return "postgresql" in self.database_url
        return not self.use_sqlite

    @property
    def db_url(self) -> str:
        """数据库连接 URL（自动判断 PostgreSQL/SQLite）
        
        优先级：
        1. DATABASE_URL 环境变量（Render/Railway 自动注入）
        2. USE_SQLITE=true → SQLite
        3. 默认 → 本地 PostgreSQL
        """
        # 1. 外部注入的 URL（Render/Railway）
        if self.database_url:
            url = self.database_url
            # 异步引擎需要 +asyncpg 或 +aiosqlite
            if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("sqlite://") and not url.startswith("sqlite+aiosqlite://"):
                url = url.replace("sqlite://", "sqlite+aiosqlite://", 1)
            return url
        
        # 2. SQLite 开发模式
        if self.use_sqlite:
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        
        # 3. 本地 PostgreSQL
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def db_sync_url(self) -> str:
        """同步数据库连接 URL（用于 Alembic 等同步工具）"""
        if self.database_url:
            url = self.database_url
            # 移除异步驱动前缀
            if url.startswith("postgresql+asyncpg://"):
                url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
            elif url.startswith("sqlite+aiosqlite://"):
                url = url.replace("sqlite+aiosqlite://", "sqlite://", 1)
            return url
        
        if self.use_sqlite:
            return f"sqlite:///{self.sqlite_path}"
        
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
