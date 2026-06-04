# 多阶段构建：前端 + 后端打包到同一个容器

# ── Stage 1: 构建前端 ──
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend
COPY app/package.json app/package-lock.json* ./
RUN npm ci --prefer-offline --no-audit

COPY app/ .
RUN npm run build

# ── Stage 2: Python 后端 ──
FROM python:3.12-slim AS backend

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制 Python 依赖
COPY iwm_full_v0.1/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY iwm_full_v0.1/ ./

# 从前端构建阶段复制静态文件
COPY --from=frontend-builder /app/frontend/dist ./app/static

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
