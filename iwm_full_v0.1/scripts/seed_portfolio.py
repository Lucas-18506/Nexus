"""Seed data script - 初始化用户持仓和观察仓.

基于用户持仓清单（2026-06-03）生成初始数据。
运行方式：
    cd iwm_full_v0.1
    python3 -m scripts.seed_portfolio

注意：需要先创建好数据库表（运行 alembic 迁移）
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

# 将 app 加入路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# 使用同步引擎做初始数据写入（或者使用 async）
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://iwm:iwm_password@localhost:5432/iwm")


async def seed():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    # 持仓数据（预定义标签：AI基建层、AI应用层、物理AI、电力、消费、医药、科技、港股、美股、高波动、核心仓位、观察仓）
    positions = [
        # 港股持仓
        {"ticker": "9988.HK", "market": "HK", "name": "Alibaba Group", "name_cn": "阿里巴巴", "sector": "科技", "industry": "电商/云计算", "quantity": 500, "avg_cost": 108.5, "currency": "HKD", "tags": ["科技", "AI应用层", "核心仓位", "港股"], "analyst_rating": "buy", "notes": "港股持仓，科技+电商双驱动"},
        {"ticker": "9880.HK", "market": "HK", "name": "UBTECH Robotics", "name_cn": "优必选", "sector": "科技", "industry": "机器人/AI", "quantity": 2000, "avg_cost": 52.3, "currency": "HKD", "tags": ["物理AI", "科技", "港股", "高波动"], "analyst_rating": "buy", "notes": "物理AI概念，机器人龙头"},
        {"ticker": "6060.HK", "market": "HK", "name": "ZhongAn Online", "name_cn": "众安在线", "sector": "金融", "industry": "保险/金融科技", "quantity": 1500, "avg_cost": 18.2, "currency": "HKD", "tags": ["消费", "医药", "港股"], "analyst_rating": "hold", "notes": "保险科技，互联网医疗联动"},
        {"ticker": "3896.HK", "market": "HK", "name": "Kingsoft Cloud", "name_cn": "金山云", "sector": "科技", "industry": "云计算/AI基建", "quantity": 3000, "avg_cost": 3.85, "currency": "HKD", "tags": ["AI基建层", "科技", "港股", "高波动"], "analyst_rating": "buy", "notes": "AI基建层，云计算"},
        {"ticker": "1816.HK", "market": "HK", "name": "CGN Power", "name_cn": "中广核", "sector": "电力", "industry": "核电", "quantity": 8000, "avg_cost": 2.65, "currency": "HKD", "tags": ["电力", "港股", "核心仓位"], "analyst_rating": "buy", "notes": "电力板块，核电资产"},
        {"ticker": "1810.HK", "market": "HK", "name": "Xiaomi Corp", "name_cn": "小米", "sector": "科技", "industry": "消费电子", "quantity": 3000, "avg_cost": 25.8, "currency": "HKD", "tags": ["消费", "科技", "港股", "核心仓位"], "analyst_rating": "buy", "notes": "消费+科技双驱动"},
        {"ticker": "1211.HK", "market": "HK", "name": "BYD Co Ltd", "name_cn": "比亚迪", "sector": "消费", "industry": "新能源汽车", "quantity": 400, "avg_cost": 298.0, "currency": "HKD", "tags": ["消费", "科技", "物理AI", "港股", "核心仓位"], "analyst_rating": "buy", "notes": "科技+消费，新能源车龙头"},
        {"ticker": "0991.HK", "market": "HK", "name": "Datang Power", "name_cn": "大唐发电", "sector": "电力", "industry": "火电/新能源", "quantity": 10000, "avg_cost": 1.85, "currency": "HKD", "tags": ["电力", "港股"], "analyst_rating": "hold", "notes": "电力板块"},
        {"ticker": "0241.HK", "market": "HK", "name": "Alibaba Health", "name_cn": "阿里健康", "sector": "医药", "industry": "互联网医疗", "quantity": 2500, "avg_cost": 6.2, "currency": "HKD", "tags": ["医药", "消费", "港股"], "analyst_rating": "buy", "notes": "医药+消费，互联网医疗"},
        {"ticker": "0020.HK", "market": "HK", "name": "SenseTime", "name_cn": "商汤", "sector": "科技", "industry": "AI/计算机视觉", "quantity": 5000, "avg_cost": 1.55, "currency": "HKD", "tags": ["AI基建层", "科技", "港股", "高波动"], "analyst_rating": "hold", "notes": "AI基建层，计算机视觉"},
        {"ticker": "0100.HK", "market": "HK", "name": "MiniMax Group Inc", "name_cn": "MiniMax", "sector": "科技", "industry": "AI大模型/应用", "quantity": 100, "avg_cost": 158.0, "currency": "HKD", "tags": ["AI应用层", "科技", "港股", "高波动"], "analyst_rating": "buy", "notes": "港股IPO持仓，AI大模型独角兽，上市日期2026-01-09，代码0100.HK"},

        # 美股持仓
        {"ticker": "V", "market": "US", "name": "Visa Inc", "name_cn": "Visa", "sector": "金融", "industry": "支付/金融科技", "quantity": 30, "avg_cost": 265.0, "currency": "USD", "tags": ["消费", "美股", "核心仓位"], "analyst_rating": "buy", "notes": "消费赛道，全球支付龙头"},
        {"ticker": "MSFT", "market": "US", "name": "Microsoft Corp", "name_cn": "微软", "sector": "科技", "industry": "云计算/AI", "quantity": 25, "avg_cost": 410.5, "currency": "USD", "tags": ["科技", "AI基建层", "AI应用层", "美股", "核心仓位"], "analyst_rating": "strong_buy", "notes": "科技+AI基建+AI应用，微软生态"},
    ]

    # 观察仓数据
    watchlist = [
        {"ticker": "6869.HK", "market": "HK", "name": "YOFC", "name_cn": "长飞光纤", "reason": "通信光纤，科技赛道", "rating": "watch", "conviction": "medium", "related_industry": "通信/光纤", "tags": ["观察仓", "科技", "港股"]},
        {"ticker": "HSAI", "market": "US", "name": "Hesai Technology", "name_cn": "禾赛", "reason": "激光雷达，物理AI赛道，美股持有", "rating": "watch", "conviction": "high", "related_industry": "激光雷达/自动驾驶", "tags": ["观察仓", "物理AI", "美股"]},
        {"ticker": "300476.SZ", "market": "CN", "name": "Shengyi Technology", "name_cn": "胜宏科技", "reason": "PCB电子，科技赛道，A股标的", "rating": "watch", "conviction": "medium", "related_industry": "PCB/电子", "tags": ["观察仓", "科技"]},
        {"ticker": "300750.SZ", "market": "CN", "name": "CATL", "name_cn": "宁德时代", "reason": "新能源电池，科技+电力双属性", "rating": "watch", "conviction": "high", "related_industry": "新能源/电池", "tags": ["观察仓", "科技", "电力"]},
        {"ticker": "0992.HK", "market": "HK", "name": "Lenovo Group", "name_cn": "联想", "reason": "PC+服务器，科技+AI基建层", "rating": "watch", "conviction": "medium", "related_industry": "PC/服务器", "tags": ["观察仓", "科技", "AI基建层", "港股"]},
        {"ticker": "SIVEF", "market": "US", "name": "Sivers Semiconductors AB", "name_cn": "Sivers半导体", "reason": "瑞典半导体公司，5G毫米波+光子学双业务", "rating": "watch", "conviction": "medium", "related_industry": "半导体/5G/光通信", "tags": ["观察仓", "科技", "半导体", "美股"]},
        {"ticker": "MRVL", "market": "US", "name": "Marvell Technology", "name_cn": "Marvell", "reason": "半导体，AI基建层核心标的", "rating": "watch", "conviction": "high", "related_industry": "半导体", "tags": ["观察仓", "科技", "AI基建层", "美股"]},
        {"ticker": "COHR", "market": "US", "name": "Coherent Corp", "name_cn": "Coherent", "reason": "激光/光子学，科技赛道", "rating": "watch", "conviction": "medium", "related_industry": "激光/光子学", "tags": ["观察仓", "科技", "美股"]},
        {"ticker": "LITE", "market": "US", "name": "Lumentum Holdings", "name_cn": "Lumentum", "reason": "光通信，科技赛道", "rating": "watch", "conviction": "medium", "related_industry": "光通信", "tags": ["观察仓", "科技", "美股"]},
        {"ticker": "GLW", "market": "US", "name": "Corning Inc", "name_cn": "康宁", "reason": "特种玻璃/材料，科技/材料赛道", "rating": "watch", "conviction": "medium", "related_industry": "玻璃/材料", "tags": ["观察仓", "科技", "美股"]},
        {"ticker": "OKLO", "market": "US", "name": "Oklo Inc", "name_cn": "Oklo", "reason": "小型堆核能，电力赛道", "rating": "watch", "conviction": "high", "related_industry": "核能/小型堆", "tags": ["观察仓", "电力", "美股"]},
        {"ticker": "SMCI", "market": "US", "name": "Super Micro Computer", "name_cn": "超微电脑", "reason": "服务器，AI基建层", "rating": "watch", "conviction": "high", "related_industry": "服务器", "tags": ["观察仓", "AI基建层", "美股"]},
        {"ticker": "AVGO", "market": "US", "name": "Broadcom Inc", "name_cn": "博通", "reason": "半导体，AI基建层核心", "rating": "watch", "conviction": "high", "related_industry": "半导体", "tags": ["观察仓", "科技", "AI基建层", "美股"]},
        {"ticker": "ETN", "market": "US", "name": "Eaton Corp", "name_cn": "伊顿", "reason": "电气设备，电力赛道", "rating": "watch", "conviction": "medium", "related_industry": "电气", "tags": ["观察仓", "电力", "美股"]},
        {"ticker": "NOK", "market": "US", "name": "Nokia Corp", "name_cn": "诺基亚", "reason": "通信设备，科技赛道", "rating": "watch", "conviction": "medium", "related_industry": "通信", "tags": ["观察仓", "科技", "美股"]},
        {"ticker": "AAOI", "market": "US", "name": "Applied Optoelectronics", "name_cn": "Applied Optoelectronics", "reason": "光通信，科技赛道", "rating": "watch", "conviction": "medium", "related_industry": "光通信", "tags": ["观察仓", "科技", "美股"]},
        {"ticker": "AMD", "market": "US", "name": "AMD Inc", "name_cn": "AMD", "reason": "半导体，AI基建层，CPU+GPU", "rating": "watch", "conviction": "high", "related_industry": "半导体", "tags": ["观察仓", "科技", "AI基建层", "美股"]},
        {"ticker": "TSLA", "market": "US", "name": "Tesla Inc", "name_cn": "特斯拉", "reason": "新能源车+AI+物理AI，多概念叠加", "rating": "watch", "conviction": "high", "related_industry": "新能源汽车/AI", "tags": ["观察仓", "物理AI", "科技", "美股"]},
        {"ticker": "ARM", "market": "US", "name": "ARM Holdings", "name_cn": "ARM", "reason": "半导体IP，AI基建层", "rating": "watch", "conviction": "high", "related_industry": "半导体/IP", "tags": ["观察仓", "科技", "AI基建层", "美股"]},
        {"ticker": "DELL", "market": "US", "name": "Dell Technologies", "name_cn": "戴尔", "reason": "服务器+PC，AI基建层", "rating": "watch", "conviction": "medium", "related_industry": "服务器/PC", "tags": ["观察仓", "AI基建层", "美股"]},
        {"ticker": "HPQ", "market": "US", "name": "HP Inc", "name_cn": "惠普", "reason": "PC/打印，科技赛道", "rating": "watch", "conviction": "low", "related_industry": "PC/打印", "tags": ["观察仓", "科技", "美股"]},
    ]

    async with async_session() as session:
        from app.models.portfolio import Position, WatchlistItem

        # 清除旧数据（可选）
        await session.execute(text("DELETE FROM watchlist_items"))
        await session.execute(text("DELETE FROM positions"))
        await session.execute(text("DELETE FROM portfolio_summaries"))
        await session.commit()

        # 插入持仓
        for p in positions:
            pos = Position(**p)
            session.add(pos)
        await session.commit()
        print(f"已创建 {len(positions)} 条持仓记录")

        # 插入观察仓
        for w in watchlist:
            item = WatchlistItem(**w)
            session.add(item)
        await session.commit()
        print(f"已创建 {len(watchlist)} 条观察仓记录")

        print("Seed 完成！")


if __name__ == "__main__":
    asyncio.run(seed())
