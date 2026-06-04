"""Analysis Report service layer."""

import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, desc, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.cache_manager import CacheManager


class AnalysisService:
    """Service for analysis report CRUD and file scanning."""

    def __init__(self, db_session: AsyncSession) -> None:
        self._db = db_session
        self._cache = CacheManager()

    # ═══════════════════════════════════════════════════════
    # CRUD
    # ═══════════════════════════════════════════════════════

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        from app.models.analysis import AnalysisReport
        report = AnalysisReport(**data)
        self._db.add(report)
        await self._db.flush()
        await self._db.commit()
        return report.to_dict(include_content=True)

    async def get(self, report_id: int) -> Optional[Dict[str, Any]]:
        from app.models.analysis import AnalysisReport
        result = await self._db.execute(select(AnalysisReport).where(AnalysisReport.id == report_id))
        row = result.scalar_one_or_none()
        return row.to_dict(include_content=True) if row else None

    async def list_reports(
        self,
        analysis_type: Optional[str] = None,
        ticker: Optional[str] = None,
        industry: Optional[str] = None,
        verdict: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        from app.models.analysis import AnalysisReport
        query = select(AnalysisReport).order_by(desc(AnalysisReport.report_date), desc(AnalysisReport.created_at))
        conditions = []
        if analysis_type:
            conditions.append(AnalysisReport.analysis_type == analysis_type)
        if ticker:
            conditions.append(AnalysisReport.target_ticker.ilike(f"%{ticker}%"))
        if industry:
            conditions.append(AnalysisReport.target_industry.ilike(f"%{industry}%"))
        if verdict:
            conditions.append(AnalysisReport.verdict == verdict)
        if start_date:
            conditions.append(AnalysisReport.report_date >= start_date)
        if end_date:
            conditions.append(AnalysisReport.report_date <= end_date)
        if conditions:
            query = query.where(and_(*conditions))

        # Count
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self._db.execute(count_query)
        total = count_result.scalar() or 0

        query = query.limit(limit).offset(offset)
        result = await self._db.execute(query)
        items = [row.to_dict(include_content=False) for row in result.scalars().all()]
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    async def update(self, report_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from app.models.analysis import AnalysisReport
        from sqlalchemy import update as sa_update
        result = await self._db.execute(select(AnalysisReport).where(AnalysisReport.id == report_id))
        row = result.scalar_one_or_none()
        if not row:
            return None
        allowed = {"title", "verdict", "score", "confidence", "summary", "key_points",
                   "risk_points", "opportunities", "content", "linked_position_id", "linked_thesis_id"}
        update_data = {k: v for k, v in data.items() if k in allowed}
        if update_data:
            update_data["updated_at"] = datetime.now(timezone.utc)
            await self._db.execute(sa_update(AnalysisReport).where(AnalysisReport.id == report_id).values(**update_data))
            await self._db.commit()
        return await self.get(report_id)

    async def delete(self, report_id: int) -> bool:
        from app.models.analysis import AnalysisReport
        result = await self._db.execute(select(AnalysisReport).where(AnalysisReport.id == report_id))
        row = result.scalar_one_or_none()
        if row:
            await self._db.delete(row)
            await self._db.commit()
            return True
        return False

    # ═══════════════════════════════════════════════════════
    # Ticker / Industry lookups
    # ═══════════════════════════════════════════════════════

    async def get_by_ticker(self, ticker: str, market: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        from app.models.analysis import AnalysisReport
        query = select(AnalysisReport).where(AnalysisReport.target_ticker == ticker).order_by(desc(AnalysisReport.report_date))
        if market:
            query = query.where(AnalysisReport.target_market == market)
        query = query.limit(limit)
        result = await self._db.execute(query)
        return [row.to_dict(include_content=False) for row in result.scalars().all()]

    async def get_latest_by_ticker(self, ticker: str, market: Optional[str] = None) -> Optional[Dict[str, Any]]:
        from app.models.analysis import AnalysisReport
        query = select(AnalysisReport).where(AnalysisReport.target_ticker == ticker).order_by(desc(AnalysisReport.report_date)).limit(1)
        if market:
            query = query.where(AnalysisReport.target_market == market)
        result = await self._db.execute(query)
        row = result.scalar_one_or_none()
        return row.to_dict(include_content=True) if row else None

    async def get_by_industry(self, industry: str, limit: int = 20) -> List[Dict[str, Any]]:
        from app.models.analysis import AnalysisReport
        result = await self._db.execute(
            select(AnalysisReport)
            .where(AnalysisReport.target_industry == industry)
            .order_by(desc(AnalysisReport.report_date))
            .limit(limit)
        )
        return [row.to_dict(include_content=False) for row in result.scalars().all()]

    async def get_portfolio_summary(self, ticker_list: List[str]) -> Dict[str, Any]:
        """获取持仓标的的分析汇总"""
        from app.models.analysis import AnalysisReport
        result = await self._db.execute(
            select(AnalysisReport)
            .where(AnalysisReport.target_ticker.in_(ticker_list))
            .order_by(desc(AnalysisReport.report_date))
        )
        rows = result.scalars().all()
        # 每个 ticker 取最新的一条
        latest_map = {}
        for row in rows:
            key = f"{row.target_ticker}.{row.target_market or ''}"
            if key not in latest_map:
                latest_map[key] = row.to_dict(include_content=False)
        return {
            "total_reports": len(rows),
            "latest_by_ticker": list(latest_map.values()),
            "ticker_count": len(latest_map),
            "bullish_count": sum(1 for r in latest_map.values() if r["verdict"] == "bullish"),
            "bearish_count": sum(1 for r in latest_map.values() if r["verdict"] == "bearish"),
            "neutral_count": sum(1 for r in latest_map.values() if r["verdict"] == "neutral"),
        }

    # ═══════════════════════════════════════════════════════
    # File scanning
    # ═══════════════════════════════════════════════════════

    async def scan_reports_directory(self, reports_dir: str = None) -> Dict[str, Any]:
        """扫描 reports 目录下的分析文件，自动导入数据库.

        默认扫描目录可通过环境变量 ANALYSIS_REPORTS_DIR 配置，
        未设置时默认扫描 ./analysis_reports/。

        支持缓存：如果 1 小时内已扫描过同一目录，直接返回缓存结果。

        支持的文件名格式:
        - 公司分析_{ticker}_{name}_{YYYYMMDD}.md  (如: 公司分析_MSFT_微软_20260603.md)
        - 公司分析_{name}_{YYYYMMDD}.md          (如: 公司分析_微软_20260603.md)
        - 行业分析_{industry}_{YYYYMMDD}.md       (如: 行业分析_AI基建_20260603.md)
        - 宏观分析_{YYYYMMDD}.md                  (如: 宏观分析_20260603.md)
        """
        if not reports_dir:
            reports_dir = os.environ.get("ANALYSIS_REPORTS_DIR", "./analysis_reports")
        
        if not os.path.isdir(reports_dir):
            return {"scanned": 0, "imported": 0, "errors": [], "message": f"目录不存在: {reports_dir}"}

        # 检查缓存（1 小时内扫描过的同一目录直接返回缓存）
        cache_key = f"scan_{os.path.abspath(reports_dir).replace('/', '_').replace('\\', '_')}"
        cached = await self._cache.get(cache_key, "analysis_scan")
        if cached:
            cached_data = cached["data"]
            cached_data["cached"] = True
            cached_data["cached_at"] = cached["created_at"]
            return cached_data

        imported = 0
        errors = []

        for filename in os.listdir(reports_dir):
            if not filename.endswith(".md"):
                continue
            filepath = os.path.join(reports_dir, filename)
            try:
                parsed = self._parse_filename(filename)
                if not parsed:
                    continue

                # 读取文件内容
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                # 提取结构化数据
                extracted = self._extract_from_markdown(content, parsed["analysis_type"])

                # 合并数据
                data = {**parsed, **extracted, "source_file": filepath, "content": content}

                # 检查是否已存在（同一天+同类型+同目标）
                exists = await self._check_exists(data)
                if exists:
                    # 更新已有记录
                    await self.update(exists, {
                        "summary": data.get("summary", ""),
                        "content": content,
                        "key_points": data.get("key_points", []),
                        "risk_points": data.get("risk_points", []),
                        "opportunities": data.get("opportunities", []),
                        "verdict": data.get("verdict"),
                        "score": data.get("score"),
                        "confidence": data.get("confidence"),
                    })
                else:
                    await self.create(data)
                    imported += 1

            except Exception as e:
                errors.append({"file": filename, "error": str(e)})

        result = {
            "scanned": len(os.listdir(reports_dir)),
            "imported": imported,
            "errors": errors,
            "cached": False,
        }

        # 写入缓存
        try:
            await self._cache.set(cache_key, "analysis_scan", result, ttl=3600, source="scan")
        except Exception:
            pass

        return result

    def _parse_filename(self, filename: str) -> Optional[Dict[str, Any]]:
        """从文件名解析分析类型、目标标的和日期."""
        # 移除 .md 后缀
        name = filename.replace(".md", "")

        # 宏观分析_YYYYMMDD
        macro_match = re.match(r"宏观分析_(\d{8})", name)
        if macro_match:
            date_str = macro_match.group(1)
            return {
                "analysis_type": "macro",
                "title": f"宏观分析 {date_str}",
                "report_date": self._parse_date(date_str),
            }

        # 行业分析_{行业名}_{YYYYMMDD}
        industry_match = re.match(r"行业分析_(.+?)_(\d{8})", name)
        if industry_match:
            industry_name = industry_match.group(1)
            date_str = industry_match.group(2)
            return {
                "analysis_type": "industry",
                "title": f"{industry_name} 行业分析",
                "target_industry": industry_name,
                "report_date": self._parse_date(date_str),
            }

        # 公司分析_{ticker}_{公司名}_{YYYYMMDD}
        company_match = re.match(r"公司分析_([^_]+)_(.+?)_(\d{8})", name)
        if company_match:
            ticker = company_match.group(1)
            company_name = company_match.group(2)
            date_str = company_match.group(3)
            market = self._guess_market(ticker)
            return {
                "analysis_type": "company",
                "title": f"{company_name} ({ticker}) 公司分析",
                "target_ticker": ticker,
                "target_market": market,
                "report_date": self._parse_date(date_str),
            }

        # 公司分析_{公司名}_{YYYYMMDD} (无 ticker)
        company_match2 = re.match(r"公司分析_(.+?)_(\d{8})", name)
        if company_match2:
            company_name = company_match2.group(1)
            date_str = company_match2.group(2)
            return {
                "analysis_type": "company",
                "title": f"{company_name} 公司分析",
                "report_date": self._parse_date(date_str),
            }

        return None

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None

    def _guess_market(self, ticker: str) -> Optional[str]:
        """根据 ticker 格式猜测市场."""
        if ".HK" in ticker.upper():
            return "HK"
        if ".SZ" in ticker.upper() or ".SH" in ticker.upper():
            return "CN"
        if len(ticker) <= 5 and ticker.isalpha():
            return "US"
        if ticker.isdigit():
            return "HK"
        return "US"

    def _extract_from_markdown(self, content: str, analysis_type: str) -> Dict[str, Any]:
        """从 markdown 内容中提取结构化数据."""
        result = {
            "summary": "",
            "key_points": [],
            "risk_points": [],
            "opportunities": [],
            "verdict": None,
            "score": None,
            "confidence": None,
        }

        # 提取摘要 (第一个 ## 前的内容，或前500字)
        lines = content.split("\n")
        summary_lines = []
        for line in lines:
            if line.startswith("#"):
                break
            summary_lines.append(line)
        result["summary"] = "\n".join(summary_lines).strip()[:500]

        # 提取关键要点（## 关键要点 / ## 核心观点 下的内容）
        result["key_points"] = self._extract_section(content, ["关键要点", "核心观点", "要点", "结论", "投资要点"])

        # 提取风险点
        result["risk_points"] = self._extract_section(content, ["风险", "风险点", "风险提示", "风险因素", "RISK"])

        # 提取机会点
        result["opportunities"] = self._extract_section(content, ["机会", "机会点", "投资机会", "利好", "催化剂"])

        # 判断 verdict
        content_lower = content.lower()
        if "看涨" in content or "买入" in content or "bullish" in content_lower or "推荐" in content:
            result["verdict"] = "bullish"
        elif "看跌" in content or "卖出" in content or "bearish" in content_lower or "回避" in content:
            result["verdict"] = "bearish"
        elif "中性" in content or "观望" in content or "neutral" in content_lower or "持有" in content:
            result["verdict"] = "neutral"
        else:
            result["verdict"] = "watch"

        # 尝试提取打分
        score_match = re.search(r"(?:打分|评分|综合评分|score)[:：]?\s*(\d+(?:\.\d+)?)", content)
        if score_match:
            score = float(score_match.group(1))
            if score <= 1:  # 可能是 0-1 的置信度
                result["confidence"] = score
            else:
                result["score"] = min(score, 100)

        return result

    def _extract_section(self, content: str, headers: List[str]) -> List[str]:
        """从 markdown 中提取指定 section 下的列表项."""
        lines = content.split("\n")
        in_section = False
        items = []
        for line in lines:
            stripped = line.strip()
            # 检查是否是目标 section 的标题
            if stripped.startswith("##") or stripped.startswith("###"):
                header_text = re.sub(r"#+\s*", "", stripped).strip()
                in_section = any(h in header_text for h in headers)
                continue
            if in_section:
                if stripped.startswith("-") or stripped.startswith("*") or re.match(r"^\d+[\.\)]", stripped):
                    item = re.sub(r"^[\-\*\d\.\)]+\s*", "", stripped).strip()
                    if item:
                        items.append(item)
                elif stripped.startswith("##") or stripped.startswith("###"):
                    in_section = False
        return items[:20]  # 限制数量

    async def _check_exists(self, data: Dict[str, Any]) -> Optional[int]:
        """检查同一天同类型同目标的分析是否已存在."""
        from app.models.analysis import AnalysisReport
        from sqlalchemy import and_
        query = select(AnalysisReport)
        conditions = [AnalysisReport.analysis_type == data["analysis_type"]]
        if data.get("report_date"):
            conditions.append(AnalysisReport.report_date == data["report_date"])
        if data.get("target_ticker"):
            conditions.append(AnalysisReport.target_ticker == data["target_ticker"])
        if data.get("target_industry"):
            conditions.append(AnalysisReport.target_industry == data["target_industry"])

        result = await self._db.execute(query.where(and_(*conditions)).limit(1))
        row = result.scalar_one_or_none()
        return row.id if row else None

    # ═══════════════════════════════════════════════════════
    # Analysis Tag CRUD
    # ═══════════════════════════════════════════════════════

    async def create_tag(self, data: Dict[str, Any]) -> Dict[str, Any]:
        from app.models.analysis import AnalysisTag
        tag = AnalysisTag(**data)
        self._db.add(tag)
        await self._db.flush()
        await self._db.commit()
        return tag.to_dict()

    async def list_tags(self) -> List[Dict[str, Any]]:
        from app.models.analysis import AnalysisTag
        from sqlalchemy import select
        result = await self._db.execute(select(AnalysisTag).order_by(AnalysisTag.name))
        return [row.to_dict() for row in result.scalars().all()]

    async def get_tag(self, tag_id: int) -> Optional[Dict[str, Any]]:
        from app.models.analysis import AnalysisTag
        result = await self._db.execute(select(AnalysisTag).where(AnalysisTag.id == tag_id))
        row = result.scalar_one_or_none()
        return row.to_dict() if row else None

    async def update_tag(self, tag_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from app.models.analysis import AnalysisTag
        from sqlalchemy import update as sa_update
        result = await self._db.execute(select(AnalysisTag).where(AnalysisTag.id == tag_id))
        row = result.scalar_one_or_none()
        if not row:
            return None
        allowed = {"name", "description", "color"}
        update_data = {k: v for k, v in data.items() if k in allowed}
        if update_data:
            await self._db.execute(sa_update(AnalysisTag).where(AnalysisTag.id == tag_id).values(**update_data))
            await self._db.commit()
        return await self.get_tag(tag_id)

    async def delete_tag(self, tag_id: int) -> bool:
        from app.models.analysis import AnalysisTag
        result = await self._db.execute(select(AnalysisTag).where(AnalysisTag.id == tag_id))
        row = result.scalar_one_or_none()
        if row:
            await self._db.delete(row)
            await self._db.commit()
            return True
        return False
