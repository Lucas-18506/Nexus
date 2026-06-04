#!/bin/bash
# 启动脚本 - 用于 Render 等平台

cd iwm_full_v0.1

# 初始化数据库
python3 -c "
import asyncio
from app.core.database import init_db
asyncio.run(init_db())
"

# 启动应用
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
