"""FastAPI应用主入口"""
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import init_db
from app.api import data, news, kb, thesis, report, agent, portfolio, analysis, signals, cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    print("IWM starting up...")
    try:
        await init_db()
        print("Database initialized.")
    except Exception as e:
        print(f"Database init failed: {e}")
    yield
    # 关闭时清理
    print("IWM shutting down...")


app = FastAPI(
    title="IWM Investment Advisor",
    description="个人AI投资参谋系统",
    version="0.1.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(data.router)
app.include_router(news.router)
app.include_router(kb.router)
app.include_router(thesis.router)
app.include_router(report.router)
app.include_router(agent.router)
app.include_router(portfolio.router)
app.include_router(analysis.router)
app.include_router(signals.router)
app.include_router(cache.router)

# 静态文件服务（前端 build 产物）
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


@app.get("/health")
async def health_check() -> dict:
    """健康检查接口"""
    return {"status": "ok", "version": "0.1.0", "service": "iwm"}
