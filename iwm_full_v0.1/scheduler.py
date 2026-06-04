#!/usr/bin/env python3
"""独立定时任务调度器入口

用法:
    python scheduler.py

按 Ctrl+C 停止调度器。
"""
import asyncio


async def main() -> None:
    """主调度循环"""
    print("Scheduler started. Press Ctrl+C to stop.")
    try:
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("Shutting down scheduler...")


if __name__ == "__main__":
    asyncio.run(main())
