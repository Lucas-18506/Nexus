"""报告渲染器 - Jinja2模板渲染"""
from jinja2 import Template
from pathlib import Path
from datetime import datetime


class ReportRenderer:
    """报告渲染器，负责加载和渲染Jinja2模板"""

    def __init__(self) -> None:
        """初始化模板目录路径"""
        self.templates_dir: Path = Path(__file__).parent / "templates"

    def render(self, template_name: str, context: dict) -> str:
        """渲染指定模板

        Args:
            template_name: 模板文件名(不含.md后缀)
            context: 模板上下文变量字典

        Returns:
            渲染后的Markdown字符串
        """
        template_path = self.templates_dir / f"{template_name}.md"
        if not template_path.exists():
            return f"# 报告\n\n模板 {template_name} 不存在"
        template = Template(
            template_path.read_text(encoding="utf-8"),
            trim_blocks=True,
            lstrip_blocks=True
        )
        return template.render(**context)

    def render_daily_report(self, context: dict) -> str:
        """渲染日报报告

        Args:
            context: 日报上下文数据

        Returns:
            渲染后的日报Markdown字符串
        """
        context.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
        context.setdefault("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M"))
        context.setdefault("a_share_index", "沪深300")
        context.setdefault("a_share_change", "-")
        context.setdefault("a_share_note", "-")
        context.setdefault("hk_index", "恒生指数")
        context.setdefault("hk_change", "-")
        context.setdefault("hk_note", "-")
        context.setdefault("us_index", "标普500")
        context.setdefault("us_change", "-")
        context.setdefault("us_note", "-")
        context.setdefault("top_events", [])
        context.setdefault("committee_conclusion", "暂无分析结论")
        context.setdefault("supporting_views", [])
        context.setdefault("opposing_views", [])
        context.setdefault("risk_warnings", [])
        context.setdefault("new_opportunities", [])
        context.setdefault("risk_level", "中等")
        context.setdefault("confidence", "N/A")
        return self.render("daily_report", context)

    def render_opportunity_scan(self, context: dict) -> str:
        """渲染机会扫描报告

        Args:
            context: 机会扫描上下文数据

        Returns:
            渲染后的机会扫描报告Markdown字符串
        """
        context.setdefault("date", datetime.now().strftime("%Y-%m-%d"))
        context.setdefault("generated_at", datetime.now().strftime("%Y-%m-%d %H:%M"))
        context.setdefault("opportunities", [])
        context.setdefault("market_sentiment", "中性")
        context.setdefault("industry_heatmap", [])
        return self.render("opportunity_scan", context)
