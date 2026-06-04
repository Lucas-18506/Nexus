"""
报告生成器模块

负责将委员会分析结果格式化为多种类型的报告：
- 日报（Daily Report）
- 机会报告（Opportunity Report）
- 行业深度报告（Industry Deep Dive Report）
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


class ReportGenerator:
    """
    报告生成器。

    将CommitteeOrchestrator的分析结果转换为可读的Markdown报告。
    """

    def __init__(self, template_dir: Optional[str] = None) -> None:
        """
        初始化报告生成器

        Args:
            template_dir: 模板目录，默认不使用模板
        """
        self.template_dir = template_dir

    def generate_daily_report(
        self, committee_result: Dict[str, Any], market_data: Dict[str, Any]
    ) -> str:
        """
        生成日报（Markdown格式）

        Args:
            committee_result: 委员会分析结果
            market_data: 市场数据

        Returns:
            Markdown格式的日报字符串
        """
        now = self._format_date()
        topic = committee_result.get("topic", "市场分析")
        final_report = committee_result.get("final_report", {})
        analyses = committee_result.get("individual_analyses", {})
        devil = committee_result.get("devil_report", {})
        risk = committee_result.get("risk_assessment", {})

        # 提取概率分布
        prob_dist = final_report.get("probability_distribution", {})
        bullish = prob_dist.get("bullish", 0.33)
        neutral = prob_dist.get("neutral", 0.34)
        bearish = prob_dist.get("bearish", 0.33)

        # 风险等级
        risk_score = risk.get("overall_risk_score", 50) if isinstance(risk, dict) else 50
        risk_level = self._risk_level_text(risk_score)

        # 操作建议
        action = final_report.get("action_suggestion", {}) if isinstance(final_report, dict) else {}
        direction = action.get("direction", "观望") if isinstance(action, dict) else "观望"
        position = action.get("position_sizing", "轻仓") if isinstance(action, dict) else "轻仓"

        # 各市场概况
        a_share = market_data.get("a_share", "数据未提供")
        hk_share = market_data.get("hk_share", "数据未提供")
        us_share = market_data.get("us_share", "数据未提供")

        # 构建报告
        lines = [
            f"# IWM 投资参谋日报 - {now}",
            "",
            f"**分析主题**: {topic}",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**整体判断**: {final_report.get('final_conclusion', '暂无结论')[:200] if isinstance(final_report, dict) else '暂无结论'}...",
            "",
            "---",
            "",
            "## 1. 市场概况",
            "",
            f"- **A股**: {a_share}",
            f"- **港股**: {hk_share}",
            f"- **美股**: {us_share}",
            f"- **风险等级**: {risk_level} (评分: {risk_score}/100)",
            "",
            "---",
            "",
            "## 2. 概率分布",
            "",
            f"| 方向 | 概率 | 可视化 |",
            f"|------|------|--------|",
            f"| 看多 | {bullish:.0%} | {'█' * int(bullish * 20)} |",
            f"| 中性 | {neutral:.0%} | {'█' * int(neutral * 20)} |",
            f"| 看空 | {bearish:.0%} | {'█' * int(bearish * 20)} |",
            "",
            f"**综合置信度**: {final_report.get('confidence', 0) * 100:.0f}%" if isinstance(final_report, dict) else "",
            "",
            "---",
            "",
            "## 3. Agent委员会观点",
            "",
        ]

        # 各Agent观点
        for agent_name, analysis in analyses.items():
            if isinstance(analysis, dict):
                name_zh = self._agent_name_zh(agent_name)
                conclusion = analysis.get("conclusion", "无结论")
                confidence = analysis.get("confidence", 0)
                lines.append(f"### {name_zh} ({agent_name})")
                lines.append(f"- **结论**: {conclusion[:150]}...")
                lines.append(f"- **置信度**: {confidence * 100:.0f}%")
                lines.append("")

        # 风险提示
        lines.extend([
            "---",
            "",
            "## 4. 反驳者观点 (Devil's Advocate)",
            "",
        ])
        if isinstance(devil, dict) and devil.get("refutation_summary"):
            lines.append(f"**核心质疑**: {devil['refutation_summary'][:300]}...")
            lines.append("")
            # 具体挑战
            challenges = devil.get("specific_challenges", [])
            if challenges:
                lines.append("**具体挑战**:")
                for ch in challenges[:3]:
                    if isinstance(ch, dict):
                        lines.append(f"- 对 **{ch.get('target_agent', '未知')}**: {ch.get('challenge', '')[:100]}...")
                lines.append("")
        else:
            lines.append("暂无反驳数据")
            lines.append("")

        # 风险提示
        lines.extend([
            "---",
            "",
            "## 5. 风险提示",
            "",
        ])
        if isinstance(risk, dict):
            risk_scenarios = risk.get("risk_scenarios", [])
            if risk_scenarios:
                lines.append("| 情景 | 概率 | 预期收益/损失 |")
                lines.append("|------|------|--------------|")
                for scenario in risk_scenarios[:4]:
                    if isinstance(scenario, dict):
                        lines.append(f"| {scenario.get('scenario', '')} | {scenario.get('probability', '')} | {scenario.get('expected_return', '')} |")
                lines.append("")

            # 各维度风险
            for risk_type in ["valuation_risk", "policy_risk", "liquidity_risk", "cycle_risk", "tail_risk_blackswan"]:
                r = risk.get(risk_type, {})
                if isinstance(r, dict):
                    lines.append(f"- **{self._risk_type_name(risk_type)}**: {r.get('level', '未知')} - {r.get('description', '')[:80]}")
            lines.append("")
        else:
            lines.append("暂无风险数据")
            lines.append("")

        # 操作建议
        lines.extend([
            "---",
            "",
            "## 6. 操作建议",
            "",
            f"- **方向**: {direction}",
            f"- **仓位建议**: {position}",
            f"- **紧急程度**: {action.get('urgency', '常规跟踪') if isinstance(action, dict) else '常规跟踪'}",
            "",
        ])
        if isinstance(action, dict) and action.get("rationale"):
            lines.append(f"**理由**: {action['rationale'][:200]}")
            lines.append("")
        if isinstance(action, dict) and action.get("key_triggers"):
            lines.append("**关键触发条件**:")
            for trigger in action["key_triggers"]:
                lines.append(f"- {trigger}")
            lines.append("")

        # 支持/反对观点
        lines.extend([
            "---",
            "",
            "## 7. 观点汇总",
            "",
            "### 支持观点",
            "",
        ])
        supporting = final_report.get("supporting_views_summary", []) if isinstance(final_report, dict) else []
        if supporting:
            for view in supporting[:5]:
                if isinstance(view, dict):
                    lines.append(f"- **{view.get('agent', '')}**: {view.get('view', '')[:120]}")
        else:
            lines.append("- 各Agent整体偏向积极")
        lines.append("")

        lines.append("### 反对/质疑观点")
        lines.append("")
        opposing = final_report.get("opposing_views_summary", []) if isinstance(final_report, dict) else []
        if opposing:
            for view in opposing[:5]:
                if isinstance(view, dict):
                    lines.append(f"- **{view.get('agent', '')}**: {view.get('view', '')[:120]}")
        else:
            lines.append("- 暂无显著反对观点")
        lines.append("")

        # 页脚
        lines.extend([
            "---",
            "",
            f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 系统: IWM投资参谋 | 版本: v1.0*",
        ])

        return "\n".join(lines)

    def generate_opportunity_report(
        self, committee_result: Dict[str, Any], opportunity_data: Dict[str, Any]
    ) -> str:
        """
        生成机会报告

        Args:
            committee_result: 委员会分析结果
            opportunity_data: 机会相关数据

        Returns:
            Markdown格式的机会报告
        """
        now = self._format_date()
        sector = opportunity_data.get("sector", "未知板块")
        ticker = opportunity_data.get("ticker", "")
        final_report = committee_result.get("final_report", {})
        analyses = committee_result.get("individual_analyses", {})

        # 稀缺性分析
        scarcity = analyses.get("scarcity_analyst", {})
        scarcity_score = scarcity.get("scarcity_score", 0) if isinstance(scarcity, dict) else 0
        alpha = scarcity.get("alpha_opportunity", {}) if isinstance(scarcity, dict) else {}

        lines = [
            f"# 机会深度报告: {sector} {ticker}",
            "",
            f"**报告日期**: {now}",
            f"**稀缺性评分**: {scarcity_score}/100",
            f"**CIO综合判断**: {final_report.get('final_conclusion', '暂无')[:200] if isinstance(final_report, dict) else '暂无'}...",
            "",
            "---",
            "",
            "## 1. 机会概述",
            "",
            f"**标的**: {sector} {ticker}",
            f"**机会类型**: {opportunity_data.get('opportunity_type', '结构性机会')}",
            f"**时间框架**: {opportunity_data.get('time_horizon', '中期(1-3月)')}",
            "",
            "---",
            "",
            "## 2. 稀缺性分析",
            "",
        ]

        if isinstance(scarcity, dict):
            gap = scarcity.get("supply_demand_gap", {})
            if isinstance(gap, dict):
                lines.extend([
                    f"- **需求CAGR**: {gap.get('demand_cagr', 'N/A')}",
                    f"- **供给CAGR**: {gap.get('supply_cagr', 'N/A')}",
                    f"- **缺口方向**: {gap.get('gap_direction', 'N/A')}",
                    f"- **缺口幅度**: {gap.get('gap_magnitude', 'N/A')}",
                    f"- **持续时间**: {gap.get('duration', 'N/A')}",
                    "",
                ])

            # 卡脖子环节
            chokepoints = scarcity.get("chokepoint_identified", [])
            if chokepoints:
                lines.append("**卡脖子环节**:")
                for cp in chokepoints[:3]:
                    if isinstance(cp, dict):
                        lines.append(f"- {cp.get('chokepoint', '')} (严重程度: {cp.get('severity', '')}, 类型: {cp.get('bottleneck_type', '')})")
                lines.append("")

            # Alpha机会
            if isinstance(alpha, dict):
                lines.extend([
                    "**Alpha机会**:",
                    f"- 描述: {alpha.get('description', 'N/A')}",
                    f"- 幅度: {alpha.get('magnitude', 'N/A')}",
                    f"- 持续时间: {alpha.get('duration', 'N/A')}",
                    f"- 催化剂: {alpha.get('catalyst', 'N/A')}",
                    f"- 乐观情景: {alpha.get('upside_scenario', 'N/A')}",
                    f"- 基准情景: {alpha.get('base_case', 'N/A')}",
                    f"- 悲观情景: {alpha.get('downside_scenario', 'N/A')}",
                    "",
                ])

        # 产业链分析
        supply = analyses.get("supply_chain_analyst", {})
        lines.extend([
            "---",
            "",
            "## 3. 产业链分析",
            "",
        ])
        if isinstance(supply, dict):
            bottlenecks = supply.get("bottleneck_nodes", [])
            if bottlenecks:
                lines.append("**瓶颈节点**:")
                for bn in bottlenecks[:3]:
                    if isinstance(bn, dict):
                        lines.append(f"- {bn.get('node', '')}: {bn.get('reason', '')[:100]}")
                lines.append("")

            margin = supply.get("margin_distribution", {})
            if isinstance(margin, dict):
                lines.extend([
                    "**利润分配**:",
                    f"- 上游: {margin.get('upstream_margin', 'N/A')}",
                    f"- 中游: {margin.get('midstream_margin', 'N/A')}",
                    f"- 下游: {margin.get('downstream_margin', 'N/A')}",
                    f"- 趋势: {margin.get('trend', 'N/A')}",
                    "",
                ])

        # 公司分析
        company = analyses.get("company_analyst", {})
        lines.extend([
            "---",
            "",
            "## 4. 公司基本面",
            "",
        ])
        if isinstance(company, dict):
            lines.extend([
                f"- **护城河强度**: {company.get('moat_strength', 0)}/100",
                f"- **估值判断**: {company.get('valuation_assessment', 'N/A')}",
                f"- **管理层质量**: {company.get('management_quality', 'N/A')}",
                "",
            ])
            health = company.get("financial_health", {})
            if isinstance(health, dict):
                lines.extend([
                    "**财务健康度**:",
                    f"- 整体: {health.get('overall', 'N/A')}",
                    f"- 盈利能力: {health.get('profitability', 'N/A')}",
                    f"- 杠杆水平: {health.get('leverage', 'N/A')}",
                    f"- 现金流: {health.get('cash_flow', 'N/A')}",
                    "",
                ])

        # 风险-收益评估
        lines.extend([
            "---",
            "",
            "## 5. 风险-收益评估",
            "",
        ])
        risk_reward = final_report.get("risk_reward_assessment", {}) if isinstance(final_report, dict) else {}
        if isinstance(risk_reward, dict):
            lines.extend([
                f"- **上行空间**: {risk_reward.get('upside_potential', 'N/A')}",
                f"- **下行风险**: {risk_reward.get('downside_risk', 'N/A')}",
                f"- **风险收益比**: {risk_reward.get('risk_reward_ratio', 'N/A')}",
                f"- **评估**: {risk_reward.get('assessment', 'N/A')}",
                "",
            ])

        # 操作建议
        action = final_report.get("action_suggestion", {}) if isinstance(final_report, dict) else {}
        lines.extend([
            "---",
            "",
            "## 6. 操作建议",
            "",
        ])
        if isinstance(action, dict):
            lines.extend([
                f"- **方向**: {action.get('direction', '观望')}",
                f"- **仓位**: {action.get('position_sizing', '轻仓')}",
                f"- **理由**: {action.get('rationale', 'N/A')[:200]}",
                "",
            ])
            triggers = action.get("key_triggers", [])
            if triggers:
                lines.append("**关键触发条件**:")
                for t in triggers:
                    lines.append(f"- {t}")
                lines.append("")

        lines.extend([
            "---",
            "",
            f"*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | IWM投资参谋*",
        ])

        return "\n".join(lines)

    def generate_industry_report(
        self, committee_result: Dict[str, Any], industry_data: Dict[str, Any]
    ) -> str:
        """
        生成行业深度报告

        Args:
            committee_result: 委员会分析结果
            industry_data: 行业数据

        Returns:
            Markdown格式的行业深度报告
        """
        now = self._format_date()
        industry_name = industry_data.get("industry_name", "未知行业")
        analyses = committee_result.get("individual_analyses", {})
        final_report = committee_result.get("final_report", {})

        # 各行业Agent分析
        industry = analyses.get("industry_analyst", {})
        macro = analyses.get("macro_analyst", {})
        supply = analyses.get("supply_chain_analyst", {})
        sentiment = analyses.get("sentiment_analyst", {})

        lines = [
            f"# 行业深度报告: {industry_name}",
            "",
            f"**报告日期**: {now}",
            f"**报告类型**: 行业全景分析",
            "",
            "---",
            "",
            "## 1. 行业概览",
            "",
            f"**行业名称**: {industry_name}",
            f"**市场规模**: {industry_data.get('market_size', 'N/A')}",
            f"**行业增速**: {industry_data.get('growth_rate', 'N/A')}",
            f"**生命周期**: {industry_data.get('life_cycle', 'N/A')}",
            "",
            "---",
            "",
            "## 2. 宏观环境",
            "",
        ]

        if isinstance(macro, dict):
            lines.extend([
                f"**经济周期**: {macro.get('cycle_phase', 'N/A')}",
                f"**风险偏好**: {macro.get('risk_appetite', 'N/A')}",
                f"**对权益影响**: {macro.get('impact_on_equity', 'N/A')}",
                "",
                "**关键宏观因素**:",
            ])
            for factor in macro.get("key_factors", [])[:5]:
                if isinstance(factor, dict):
                    lines.append(f"- {factor.get('factor', '')}: {factor.get('direction', '')} ({factor.get('description', '')[:80]})")
            lines.append("")

        lines.extend([
            "---",
            "",
            "## 3. 行业景气度",
            "",
        ])
        if isinstance(industry, dict):
            lines.extend([
                f"**景气度评分**: {industry.get('prosperity_score', 0)}/100",
                f"**增长前景**: {industry.get('growth_outlook', 'N/A')}",
                f"**置信度**: {industry.get('confidence', 0) * 100:.0f}%",
                "",
            ])

            # 关键驱动因素
            drivers = industry.get("key_drivers", [])
            if drivers:
                lines.append("**关键驱动因素**:")
                lines.append("| 驱动因素 | 影响 | 强度 | 持续时间 |")
                lines.append("|----------|------|------|----------|")
                for d in drivers[:6]:
                    if isinstance(d, dict):
                        lines.append(f"| {d.get('driver', '')} | {d.get('impact', '')} | {d.get('strength', '')} | {d.get('duration', '')} |")
                lines.append("")

            # 竞争格局
            comp = industry.get("competitive_landscape", {})
            if isinstance(comp, dict):
                lines.extend([
                    "**竞争格局**:",
                    f"- 集中度: {comp.get('concentration', 'N/A')}",
                    f"- 进入壁垒: {comp.get('barriers', 'N/A')}",
                    f"- 定价权: {comp.get('pricing_power', 'N/A')}",
                    f"- 趋势: {comp.get('trend', 'N/A')}",
                    "",
                ])

            # 政策支持
            policy = industry.get("policy_support", {})
            if isinstance(policy, dict):
                lines.extend([
                    "**政策支持**:",
                    f"- 方向: {policy.get('direction', 'N/A')}",
                    f"- 力度: {policy.get('strength', 'N/A')}",
                    f"- 可持续性: {policy.get('sustainability', 'N/A')}",
                    "",
                ])

            # 风险因素
            risks = industry.get("risk_factors", [])
            if risks:
                lines.append("**行业风险**:")
                for r in risks[:5]:
                    lines.append(f"- {r}")
                lines.append("")

        # 产业链
        lines.extend([
            "---",
            "",
            "## 4. 产业链深度分析",
            "",
        ])
        if isinstance(supply, dict):
            structure = supply.get("chain_structure", {})
            if isinstance(structure, dict):
                lines.extend([
                    f"**产业链结构**: {structure.get('description', 'N/A')}",
                    f"**复杂度**: {structure.get('complexity', 'N/A')}",
                    "",
                ])

            bottlenecks = supply.get("bottleneck_nodes", [])
            if bottlenecks:
                lines.append("**瓶颈节点**:")
                for bn in bottlenecks[:4]:
                    if isinstance(bn, dict):
                        lines.append(f"- **{bn.get('node', '')}** (严重度: {bn.get('severity', '')})")
                        lines.append(f"  - 原因: {bn.get('reason', '')[:120]}")
                        lines.append(f"  - 持续性: {bn.get('duration', '')}")
                lines.append("")

            alternatives = supply.get("alternative_paths", [])
            if alternatives:
                lines.append("**替代方案**:")
                for alt in alternatives[:4]:
                    if isinstance(alt, dict):
                        lines.append(f"- {alt.get('alternative', '')} -> 可行性: {alt.get('feasibility', '')}, 时间: {alt.get('timeline', '')}")
                lines.append("")

            margin = supply.get("margin_distribution", {})
            if isinstance(margin, dict):
                lines.extend([
                    "**利润分配格局**:",
                    f"- 上游利润: {margin.get('upstream_margin', 'N/A')}",
                    f"- 中游利润: {margin.get('midstream_margin', 'N/A')}",
                    f"- 下游利润: {margin.get('downstream_margin', 'N/A')}",
                    f"- 趋势: {margin.get('trend', 'N/A')}",
                    f"- 价格传导时滞: {supply.get('transmission_lag', 'N/A')}",
                    "",
                ])

        # 情绪面
        lines.extend([
            "---",
            "",
            "## 5. 市场情绪",
            "",
        ])
        if isinstance(sentiment, dict):
            lines.extend([
                f"**情绪评分**: {sentiment.get('sentiment_score', 50)}/100 (50为中性)",
                f"**FOMO程度**: {sentiment.get('fomo_level', 0)}/100",
                f"**恐惧程度**: {sentiment.get('fear_level', 0)}/100",
                f"**机构行为**: {sentiment.get('institutional_behavior', 'N/A')}",
                f"**散户行为**: {sentiment.get('retail_behavior', 'N/A')}",
                "",
            ])
            signals = sentiment.get("key_signals", [])
            if signals:
                lines.append("**关键情绪信号**:")
                for s in signals[:5]:
                    if isinstance(s, dict):
                        lines.append(f"- {s.get('signal', '')}: {s.get('reading', '')} ({s.get('direction', '')})")
                lines.append("")

        # CIO综合判断
        lines.extend([
            "---",
            "",
            "## 6. CIO综合判断",
            "",
        ])
        if isinstance(final_report, dict):
            lines.extend([
                f"**最终结论**: {final_report.get('final_conclusion', '暂无')[:300]}",
                f"**综合置信度**: {final_report.get('confidence', 0) * 100:.0f}%",
                "",
            ])

            prob = final_report.get("probability_distribution", {})
            if isinstance(prob, dict):
                lines.extend([
                    "**概率分布**:",
                    f"- 看多: {prob.get('bullish', 0):.0%}",
                    f"- 中性: {prob.get('neutral', 0):.0%}",
                    f"- 看空: {prob.get('bearish', 0):.0%}",
                    "",
                ])

            action = final_report.get("action_suggestion", {})
            if isinstance(action, dict):
                lines.extend([
                    "**操作建议**:",
                    f"- 方向: {action.get('direction', '观望')}",
                    f"- 仓位: {action.get('position_sizing', '轻仓')}",
                    f"- 理由: {action.get('rationale', 'N/A')[:200]}",
                    "",
                ])

        # 附录：证据汇总
        lines.extend([
            "---",
            "",
            "## 附录: 证据汇总",
            "",
        ])
        for agent_name, analysis in analyses.items():
            if isinstance(analysis, dict):
                name_zh = self._agent_name_zh(agent_name)
                lines.append(f"### {name_zh}")
                lines.append("")

                sup = analysis.get("supporting_evidence", [])
                if sup:
                    lines.append("**支持证据**:")
                    for ev in sup[:3]:
                        if isinstance(ev, dict):
                            lines.append(f"- {ev}")
                    lines.append("")

                contra = analysis.get("contradicting_evidence", [])
                if contra:
                    lines.append("**反对证据**:")
                    for ev in contra[:3]:
                        if isinstance(ev, dict):
                            lines.append(f"- {ev}")
                    lines.append("")

        lines.extend([
            "---",
            "",
            f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | IWM投资参谋*",
        ])

        return "\n".join(lines)

    def _format_date(self) -> str:
        """格式化当前日期"""
        return datetime.now().strftime("%Y年%m月%d日")

    def _risk_level_text(self, score: int) -> str:
        """将风险分数转换为文字描述"""
        if score >= 70:
            return "高风险"
        elif score >= 50:
            return "中等风险"
        elif score >= 30:
            return "低风险"
        else:
            return "极低风险"

    def _agent_name_zh(self, agent_name: str) -> str:
        """将Agent英文名转换为中文"""
        name_map = {
            "macro_analyst": "宏观分析师",
            "industry_analyst": "行业分析师",
            "supply_chain_analyst": "产业链分析师",
            "scarcity_analyst": "稀缺性分析师",
            "company_analyst": "公司分析师",
            "sentiment_analyst": "情绪分析师",
            "risk_analyst": "风险分析师",
            "devil_advocate": "反驳者",
            "cio_synthesizer": "CIO汇总者",
        }
        return name_map.get(agent_name, agent_name)

    def _risk_type_name(self, risk_type: str) -> str:
        """将风险类型转换为中文"""
        type_map = {
            "valuation_risk": "估值风险",
            "policy_risk": "政策风险",
            "liquidity_risk": "流动性风险",
            "cycle_risk": "周期风险",
            "tail_risk_blackswan": "黑天鹅风险",
        }
        return type_map.get(risk_type, risk_type)

    def save_report(self, report: str, filepath: str) -> str:
        """
        保存报告到文件

        Args:
            report: 报告内容
            filepath: 文件路径

        Returns:
            保存的文件路径
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        return filepath
