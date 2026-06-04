#!/usr/bin/env python3
"""IWM Investment Advisor - 多模式入口

支持模式:
    api       - 启动FastAPI服务
    scheduler - 启动定时任务调度器
    daily     - 执行日报生成任务
    once      - 执行单次采集任务

用法:
    python run.py api                  # 启动API服务
    python run.py scheduler            # 启动调度器
    python run.py daily                # 生成日报
    python run.py once --task macro    # 单次采集宏观数据
    python run.py once --task stock    # 单次采集股票数据
    python run.py once --task news     # 单次采集新闻
"""
import asyncio
import argparse
import os
from datetime import datetime


async def run_api() -> None:
    """运行FastAPI服务"""
    import uvicorn
    from app.main import app
    uvicorn.run(app, host="0.0.0.0", port=8000)


async def run_scheduler() -> None:
    """运行定时任务调度器"""
    print("启动定时任务调度器...")
    while True:
        await asyncio.sleep(60)


async def run_daily_report() -> None:
    """生成日报"""
    print("生成日报...")
    # 模拟日报生成
    report = (
        "# IWM 日报\n\n"
        "## 市场概况\n"
        "今日市场震荡整理。\n\n"
        "## Agent委员会观点\n"
        "中性偏多。\n"
    )
    print(report)
    # 保存到文件
    filename = f"data/reports/daily_{datetime.now().strftime('%Y%m%d')}.md"
    os.makedirs("data/reports", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"报告已保存: {filename}")


async def run_once(task: str) -> None:
    """执行单次任务"""
    print(f"执行单次任务: {task}")
    if task == "macro":
        print("采集宏观数据...")
    elif task == "stock":
        print("采集股票数据...")
    elif task == "news":
        print("采集新闻...")
    else:
        print(f"未知任务: {task}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IWM Investment Advisor")
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["api", "scheduler", "daily", "once"],
        default="api",
        help="运行模式 (默认: api)"
    )
    parser.add_argument(
        "--task",
        choices=["macro", "stock", "news"],
        help="单次任务类型 (仅用于 once 模式)"
    )
    args = parser.parse_args()

    if args.mode == "api":
        asyncio.run(run_api())
    elif args.mode == "scheduler":
        asyncio.run(run_scheduler())
    elif args.mode == "daily":
        asyncio.run(run_daily_report())
    elif args.mode == "once":
        asyncio.run(run_once(args.task))
