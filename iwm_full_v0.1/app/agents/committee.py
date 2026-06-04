"""
委员会工作流模块（核心文件）

实现投资分析Agent集群的委员会辩论工作流。

两种实现方式：
1. LangGraph版本：使用StateGraph构建状态机，支持可视化
2. Asyncio版本：不依赖LangGraph，使用asyncio.gather实现并行

工作流阶段：
- Phase 1: 并行运行6个分析Agent
- Phase 2: Devil Advocate + Risk Analyst串行分析
- Phase 3: CIO汇总综合判断
- Phase 4: 生成最终报告
"""

import asyncio
import json
import logging
import os
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime

from app.agents.agent_configs import (
    AgentConfig,
    AGENT_REGISTRY,
    PARALLEL_AGENTS,
    AGENT_WEIGHTS,
)
from app.agents.analysis_engine import AnalysisEngine

logger = logging.getLogger(__name__)


# ============================================================================
# 状态定义
# ============================================================================

class CommitteeState(TypedDict, total=False):
    """委员会工作流的状态定义"""

    topic: str
    context: Dict[str, Any]
    phase: str  # phase1 / phase2 / phase3 / phase4 / completed / error
    individual_analyses: Dict[str, Dict[str, Any]]
    devil_report: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    final_report: Dict[str, Any]
    errors: List[str]


# ============================================================================
# 工具函数
# ============================================================================

def _get_project_root() -> str:
    """获取项目根目录"""
    current_file = os.path.abspath(__file__)
    # 从 app/agents/committee.py 向上两级到项目根
    return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))


def _make_context_for_agent(agent_name: str, base_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    为特定Agent构建上下文。
    根据不同Agent类型，从base_context中提取相关数据。
    """
    context = {"topic": base_context.get("topic", ""), **base_context}

    # 特定Agent的特殊上下文处理
    if agent_name == "macro_analyst":
        context.update({
            "macro_indicators": base_context.get("macro_indicators", {}),
            "central_bank_policy": base_context.get("central_bank_policy", ""),
            "exchange_rates": base_context.get("exchange_rates", {}),
            "global_macro": base_context.get("global_macro", ""),
        })
    elif agent_name == "industry_analyst":
        context.update({
            "industry_name": base_context.get("industry", base_context.get("topic", "未知行业")),
            "industry_data": base_context.get("industry_data", {}),
            "policy_updates": base_context.get("policy_updates", ""),
            "technology_trends": base_context.get("technology_trends", ""),
            "competitive_landscape": base_context.get("competitive_landscape", ""),
            "market_size": base_context.get("market_size", ""),
        })
    elif agent_name == "scarcity_analyst":
        context.update({
            "target_sector": base_context.get("sector", base_context.get("topic", "")),
            "supply_data": base_context.get("supply_data", ""),
            "demand_data": base_context.get("demand_data", ""),
            "price_data": base_context.get("price_data", ""),
            "market_consensus": base_context.get("market_consensus", ""),
            "capacity_expansion": base_context.get("capacity_expansion", ""),
        })
    elif agent_name == "company_analyst":
        context.update({
            "company_name": base_context.get("company", base_context.get("topic", "")),
            "business_model": base_context.get("business_model", ""),
            "financials": base_context.get("financials", {}),
            "valuation": base_context.get("valuation", {}),
            "competitive_position": base_context.get("competitive_position", ""),
        })
    elif agent_name == "sentiment_analyst":
        context.update({
            "market_data": base_context.get("market_data", {}),
            "sentiment_indicators": base_context.get("sentiment_indicators", {}),
            "social_media": base_context.get("social_media", ""),
            "institutional_activity": base_context.get("institutional_activity", ""),
            "retail_activity": base_context.get("retail_activity", ""),
        })
    elif agent_name == "risk_analyst":
        context.update({
            "target": base_context.get("topic", ""),
            "market_environment": base_context.get("market_environment", ""),
            "valuation_metrics": base_context.get("valuation", {}),
            "policy_landscape": base_context.get("policy_landscape", ""),
            "liquidity_conditions": base_context.get("liquidity_conditions", ""),
            "other_agent_conclusions": _summarize_other_analyses(
                base_context.get("_individual_analyses", {})
            ),
        })
    elif agent_name == "devil_advocate":
        context.update({
            "topic": base_context.get("topic", ""),
            "analyses": base_context.get("_individual_analyses", {}),
            "risk_analyst_report": base_context.get("_risk_assessment", {}),
        })
    elif agent_name == "cio_synthesizer":
        context.update({
            "topic": base_context.get("topic", ""),
            "individual_analyses": base_context.get("_individual_analyses", {}),
            "devil_report": base_context.get("_devil_report", {}),
            "risk_assessment": base_context.get("_risk_assessment", {}),
        })

    return context


def _summarize_other_analyses(analyses: Dict[str, Any]) -> str:
    """为Risk Analyst汇总其他Agent的结论"""
    summaries = []
    for agent_name, analysis in analyses.items():
        conclusion = analysis.get("conclusion", "无结论") if isinstance(analysis, dict) else str(analysis)[:200]
        summaries.append(f"- {agent_name}: {conclusion[:200]}")
    return "\n".join(summaries) if summaries else "暂无其他Agent分析结果"


# ============================================================================
# Phase 执行函数
# ============================================================================

async def phase1_parallel_analysis(state: CommitteeState) -> CommitteeState:
    """
    Phase 1: 并行运行6个分析Agent

    同时启动：宏观、行业、产业链、稀缺性、公司、情绪分析师
    """
    logger.info("[Phase 1] 启动并行分析: %s", ", ".join(PARALLEL_AGENTS))
    state["phase"] = "phase1"

    project_root = _get_project_root()
    prompts_dir = os.path.join(project_root, "app", "agents", "prompts")

    # 创建所有引擎
    engines: Dict[str, AnalysisEngine] = {}
    for agent_name in PARALLEL_AGENTS:
        config = AGENT_REGISTRY[agent_name]
        engines[agent_name] = AnalysisEngine(config, prompts_dir=prompts_dir)

    # 构建并行任务
    async def run_one_agent(agent_name: str) -> tuple:
        try:
            engine = engines[agent_name]
            context = _make_context_for_agent(agent_name, state["context"])
            result = await engine.analyze(context)
            return agent_name, result
        except Exception as e:
            logger.error(f"Agent {agent_name} 分析失败: {e}")
            return agent_name, {"agent_name": agent_name, "error": str(e), "confidence": 0.0}

    # 并行执行
    tasks = [run_one_agent(name) for name in PARALLEL_AGENTS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 收集结果
    individual_analyses: Dict[str, Dict[str, Any]] = {}
    for result in results:
        if isinstance(result, Exception):
            state["errors"].append(str(result))
            continue
        agent_name, analysis = result
        individual_analyses[agent_name] = analysis

    state["individual_analyses"] = individual_analyses

    # 将个体分析结果注入context供后续Phase使用
    state["context"]["_individual_analyses"] = individual_analyses

    logger.info("[Phase 1] 完成，成功: %d/%d", len(individual_analyses), len(PARALLEL_AGENTS))
    return state


async def phase2_devil_analysis(state: CommitteeState) -> CommitteeState:
    """
    Phase 2a: Devil Advocate分析

    Devil阅读所有其他Agent的结论，提出反驳。
    """
    logger.info("[Phase 2a] 启动Devil Advocate分析")
    state["phase"] = "phase2_devil"

    project_root = _get_project_root()
    prompts_dir = os.path.join(project_root, "app", "agents", "prompts")

    try:
        config = AGENT_REGISTRY["devil_advocate"]
        engine = AnalysisEngine(config, prompts_dir=prompts_dir)
        context = _make_context_for_agent("devil_advocate", state["context"])
        result = await engine.analyze(context)
        state["devil_report"] = result
        state["context"]["_devil_report"] = result
    except Exception as e:
        logger.error(f"Devil Advocate 分析失败: {e}")
        state["errors"].append(f"devil_advocate: {str(e)}")
        state["devil_report"] = {"agent_name": "devil_advocate", "error": str(e), "confidence": 0.0}

    logger.info("[Phase 2a] Devil Advocate分析完成")
    return state


async def phase2_risk_analysis(state: CommitteeState) -> CommitteeState:
    """
    Phase 2b: Risk Analyst分析

    风险分析师基于所有其他Agent的结论进行风险评估。
    """
    logger.info("[Phase 2b] 启动Risk Analyst分析")
    state["phase"] = "phase2_risk"

    project_root = _get_project_root()
    prompts_dir = os.path.join(project_root, "app", "agents", "prompts")

    try:
        config = AGENT_REGISTRY["risk_analyst"]
        engine = AnalysisEngine(config, prompts_dir=prompts_dir)
        context = _make_context_for_agent("risk_analyst", state["context"])
        result = await engine.analyze(context)
        state["risk_assessment"] = result
        state["context"]["_risk_assessment"] = result
    except Exception as e:
        logger.error(f"Risk Analyst 分析失败: {e}")
        state["errors"].append(f"risk_analyst: {str(e)}")
        state["risk_assessment"] = {"agent_name": "risk_analyst", "error": str(e), "overall_risk_score": 50}

    logger.info("[Phase 2b] Risk Analyst分析完成")
    return state


async def phase2_combined(state: CommitteeState) -> CommitteeState:
    """
    Phase 2: 串行执行Devil和Risk分析（Devil先，Risk后）

    也可以并行执行，但串行可以让Risk看到Devil的质疑。
    """
    # 先执行Devil
    state = await phase2_devil_analysis(state)
    # 更新context让Risk也能看到Devil的报告
    state["context"]["_devil_report"] = state.get("devil_report", {})
    # 再执行Risk
    state = await phase2_risk_analysis(state)
    return state


async def phase3_consensus(state: CommitteeState) -> CommitteeState:
    """
    Phase 3: CIO汇总综合判断

    CIO综合所有Agent观点、Devil反驳和风险评估，做出最终判断。
    """
    logger.info("[Phase 3] 启动CIO汇总")
    state["phase"] = "phase3"

    project_root = _get_project_root()
    prompts_dir = os.path.join(project_root, "app", "agents", "prompts")

    try:
        config = AGENT_REGISTRY["cio_synthesizer"]
        engine = AnalysisEngine(config, prompts_dir=prompts_dir)
        context = _make_context_for_agent("cio_synthesizer", state["context"])
        result = await engine.analyze(context)
        state["final_report"] = result
    except Exception as e:
        logger.error(f"CIO汇总 失败: {e}")
        state["errors"].append(f"cio_synthesizer: {str(e)}")
        # 生成降级报告
        state["final_report"] = _generate_fallback_report(state)

    logger.info("[Phase 3] CIO汇总完成")
    return state


async def phase4_report(state: CommitteeState) -> CommitteeState:
    """
    Phase 4: 生成最终报告

    整合所有阶段的结果，输出完整报告。
    """
    logger.info("[Phase 4] 生成最终报告")
    state["phase"] = "phase4"

    final_report = state.get("final_report", {})
    if not final_report:
        final_report = _generate_fallback_report(state)
        state["final_report"] = final_report

    # 在报告中添加元数据
    final_report["_metadata"] = {
        "topic": state["topic"],
        "timestamp": datetime.now().isoformat(),
        "agents_participated": list(state.get("individual_analyses", {}).keys()),
        "phases_completed": ["phase1", "phase2", "phase3", "phase4"],
        "errors": state.get("errors", []),
    }

    state["phase"] = "completed"
    logger.info("[Phase 4] 最终报告生成完成")
    return state


def _generate_fallback_report(state: CommitteeState) -> Dict[str, Any]:
    """当CIO汇总失败时生成降级报告"""
    analyses = state.get("individual_analyses", {})

    # 简单多数投票
    bullish_count = sum(1 for a in analyses.values() if isinstance(a, dict) and "conclusion" in a and "积极" in str(a.get("conclusion", "")))
    bearish_count = sum(1 for a in analyses.values() if isinstance(a, dict) and "conclusion" in a and ("谨慎" in str(a.get("conclusion", "")) or "风险" in str(a.get("conclusion", ""))))
    total = len(analyses)

    return {
        "agent_name": "cio_synthesizer",
        "final_conclusion": f"[降级报告] 基于{total}个Agent的分析，看多{bullish_count}票，看空{bearish_count}票。因CIO汇总失败，此报告为简化版本。",
        "confidence": 0.5,
        "probability_distribution": {
            "bullish": bullish_count / total if total > 0 else 0.33,
            "neutral": (total - bullish_count - bearish_count) / total if total > 0 else 0.34,
            "bearish": bearish_count / total if total > 0 else 0.33,
        },
        "supporting_views_summary": [],
        "opposing_views_summary": [],
        "max_risk": {"risk_type": "未知", "probability": "N/A", "potential_loss": "N/A"},
        "risk_reward_assessment": {"upside_potential": "N/A", "downside_risk": "N/A", "risk_reward_ratio": 1.0, "assessment": "未知"},
        "action_suggestion": {"direction": "观望", "urgency": "常规跟踪", "position_sizing": "轻仓", "rationale": "CIO汇总失败，建议观望"},
        "key_assumptions": [],
        "_fallback": True,
    }


# ============================================================================
# LangGraph版本（如果可用）
# ============================================================================

def create_committee_graph() -> Optional[Any]:
    """
    创建LangGraph的StateGraph。

    如果LangGraph不可用，返回None。

    Returns:
        编译后的StateGraph，或None
    """
    try:
        from langgraph.graph import StateGraph, END

        # 定义图
        builder = StateGraph(CommitteeState)

        # 添加节点
        builder.add_node("phase1", phase1_parallel_analysis)
        builder.add_node("phase2_devil", phase2_devil_analysis)
        builder.add_node("phase2_risk", phase2_risk_analysis)
        builder.add_node("phase3", phase3_consensus)
        builder.add_node("phase4", phase4_report)

        # 添加边
        builder.set_entry_point("phase1")
        builder.add_edge("phase1", "phase2_devil")
        builder.add_edge("phase2_devil", "phase2_risk")
        builder.add_edge("phase2_risk", "phase3")
        builder.add_edge("phase3", "phase4")
        builder.add_edge("phase4", END)

        # 编译
        graph = builder.compile()
        logger.info("LangGraph委员会图创建成功")
        return graph

    except ImportError:
        logger.warning("LangGraph不可用，将使用asyncio版本")
        return None
    except Exception as e:
        logger.error(f"创建LangGraph失败: {e}")
        return None


# ============================================================================
# CommitteeOrchestrator 编排器
# ============================================================================

class CommitteeOrchestrator:
    """
    委员会编排器。

    负责初始化所有Agent引擎、管理工作流执行、
    提供同步和异步接口。
    """

    def __init__(self, prompts_dir: Optional[str] = None) -> None:
        """
        初始化编排器

        Args:
            prompts_dir: 提示词文件目录，默认自动推断
        """
        self.engines: Dict[str, AnalysisEngine] = {}
        self.prompts_dir = prompts_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "prompts"
        )

        # 尝试创建LangGraph
        self.graph = create_committee_graph()
        self.use_langgraph = self.graph is not None

        # 初始化所有Agent引擎
        self._init_engines()

        logger.info(
            "CommitteeOrchestrator初始化完成。LangGraph: %s",
            "可用" if self.use_langgraph else "不可用(asyncio模式)",
        )

    def _init_engines(self) -> None:
        """初始化所有Agent的分析引擎"""
        for agent_name, config in AGENT_REGISTRY.items():
            try:
                self.engines[agent_name] = AnalysisEngine(config, prompts_dir=self.prompts_dir)
            except Exception as e:
                logger.warning(f"初始化引擎 {agent_name} 失败: {e}")

    async def run_debate(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行完整的委员会辩论流程。

        这是主要的入口方法，执行所有4个Phase。

        Args:
            topic: 分析主题
            context: 分析上下文数据

        Returns:
            完整的委员会分析结果
        """
        logger.info("=" * 60)
        logger.info("启动委员会辩论: %s", topic)
        logger.info("=" * 60)

        start_time = datetime.now()

        # 初始化状态
        state: CommitteeState = {
            "topic": topic,
            "context": {**context, "topic": topic},
            "phase": "init",
            "individual_analyses": {},
            "devil_report": {},
            "risk_assessment": {},
            "final_report": {},
            "errors": [],
        }

        try:
            # Phase 1: 并行分析
            state = await phase1_parallel_analysis(state)

            # Phase 2: Devil + Risk（串行，Devil先Risk后）
            state = await phase2_combined(state)

            # Phase 3: CIO汇总
            state = await phase3_consensus(state)

            # Phase 4: 生成报告
            state = await phase4_report(state)

        except Exception as e:
            logger.error(f"委员会辩论流程失败: {e}")
            state["errors"].append(f"workflow: {str(e)}")
            state["phase"] = "error"

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("委员会辩论完成，耗时: %.1f秒", elapsed)

        return self._format_result(state)

    async def run_daily_pipeline(
        self,
        market_summary: Dict[str, Any],
        news: List[Dict[str, Any]],
        macro_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        每日流水线。

        整合市场数据、新闻和宏观数据，运行完整分析。

        Args:
            market_summary: 市场概况（A股/港股/美股）
            news: 今日新闻列表
            macro_data: 宏观数据列表

        Returns:
            完整的每日分析报告
        """
        context = {
            "market_summary": market_summary,
            "news": news,
            "macro_data": macro_data,
            "market_environment": self._build_market_env(market_summary),
        }

        topic = f"每日市场分析 - {datetime.now().strftime('%Y-%m-%d')}"
        return await self.run_debate(topic, context)

    def _build_market_env(self, market_summary: Dict[str, Any]) -> str:
        """从市场摘要构建市场环境描述"""
        parts = []
        for market, data in market_summary.items():
            if isinstance(data, dict):
                change = data.get("change", "N/A")
                parts.append(f"{market}: {change}")
            else:
                parts.append(f"{market}: {data}")
        return "; ".join(parts)

    def _format_result(self, state: CommitteeState) -> Dict[str, Any]:
        """格式化最终输出结果"""
        return {
            "topic": state["topic"],
            "phase": state["phase"],
            "timestamp": datetime.now().isoformat(),
            "individual_analyses": state.get("individual_analyses", {}),
            "devil_report": state.get("devil_report", {}),
            "risk_assessment": state.get("risk_assessment", {}),
            "final_report": state.get("final_report", {}),
            "errors": state.get("errors", []),
            "status": "success" if state["phase"] == "completed" else "partial" if state.get("final_report") else "failed",
        }

    async def run_single_agent(self, agent_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行单个Agent分析（用于快速查询）。

        Args:
            agent_name: Agent名称
            context: 分析上下文

        Returns:
            单个Agent的分析结果
        """
        if agent_name not in AGENT_REGISTRY:
            return {"error": f"未知Agent: {agent_name}", "available": list(AGENT_REGISTRY.keys())}

        engine = self.engines.get(agent_name)
        if not engine:
            return {"error": f"Agent {agent_name} 引擎未初始化"}

        ctx = _make_context_for_agent(agent_name, context)
        return await engine.analyze(ctx)


# ============================================================================
# 纯Asyncio版本（不依赖LangGraph）
# ============================================================================

class AsyncCommitteeRunner:
    """
    纯Asyncio版本的委员会运行器。

    不依赖LangGraph，使用asyncio.gather实现并行，
    使用普通async函数实现串行。

    与CommitteeOrchestrator提供相同的接口。
    """

    def __init__(self, prompts_dir: Optional[str] = None) -> None:
        """
        初始化运行器

        Args:
            prompts_dir: 提示词文件目录
        """
        self.prompts_dir = prompts_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "prompts"
        )
        self.engines: Dict[str, AnalysisEngine] = {}
        self._init_engines()

    def _init_engines(self) -> None:
        """初始化所有Agent引擎"""
        for agent_name, config in AGENT_REGISTRY.items():
            try:
                self.engines[agent_name] = AnalysisEngine(config, prompts_dir=self.prompts_dir)
            except Exception as e:
                logger.warning(f"初始化引擎 {agent_name} 失败: {e}")

    async def run_debate(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行完整的委员会辩论（asyncio版本）。

        执行流程：
        1. Phase1: 并行运行6个Agent
        2. Phase2: 串行运行Devil（看到Phase1结果）+ Risk（看到Phase1+Devil结果）
        3. Phase3: CIO汇总（看到所有结果）
        4. Phase4: 格式化输出

        Args:
            topic: 分析主题
            context: 分析上下文

        Returns:
            完整的委员会分析结果
        """
        logger.info("[AsyncCommittee] 启动辩论: %s", topic)
        start_time = datetime.now()

        # Phase 1: 并行分析
        logger.info("[AsyncCommittee] Phase 1: 并行分析6个Agent")
        individual_analyses = await self._phase1_parallel(topic, context)

        # Phase 2a: Devil Advocate（看到所有Phase1结果）
        logger.info("[AsyncCommittee] Phase 2a: Devil Advocate")
        devil_report = await self._phase2_devil(topic, individual_analyses)

        # Phase 2b: Risk Analyst（看到Phase1 + Devil结果）
        logger.info("[AsyncCommittee] Phase 2b: Risk Analyst")
        risk_assessment = await self._phase2_risk(topic, individual_analyses, devil_report)

        # Phase 3: CIO汇总（看到所有结果）
        logger.info("[AsyncCommittee] Phase 3: CIO汇总")
        final_report = await self._phase3_cio(topic, individual_analyses, devil_report, risk_assessment)

        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("[AsyncCommittee] 辩论完成，耗时: %.1f秒", elapsed)

        return {
            "topic": topic,
            "phase": "completed",
            "timestamp": datetime.now().isoformat(),
            "individual_analyses": individual_analyses,
            "devil_report": devil_report,
            "risk_assessment": risk_assessment,
            "final_report": final_report,
            "errors": [],
            "status": "success",
            "elapsed_seconds": elapsed,
        }

    async def _phase1_parallel(
        self, topic: str, context: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Phase 1: 并行运行6个分析Agent"""

        async def run_one(agent_name: str) -> tuple:
            try:
                engine = self.engines[agent_name]
                ctx = _make_context_for_agent(agent_name, {**context, "topic": topic})
                result = await engine.analyze(ctx)
                return agent_name, result
            except Exception as e:
                logger.error(f"Agent {agent_name} 失败: {e}")
                return agent_name, {"agent_name": agent_name, "error": str(e), "confidence": 0.0}

        tasks = [run_one(name) for name in PARALLEL_AGENTS]
        results = await asyncio.gather(*tasks)

        return {name: result for name, result in results}

    async def _phase2_devil(
        self, topic: str, individual_analyses: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Phase 2a: Devil Advocate分析"""
        try:
            engine = self.engines["devil_advocate"]
            ctx = {
                "topic": topic,
                "analyses": individual_analyses,
                "risk_analyst_report": {},
            }
            return await engine.analyze(ctx)
        except Exception as e:
            logger.error(f"Devil Advocate 失败: {e}")
            return {"agent_name": "devil_advocate", "error": str(e), "confidence": 0.0}

    async def _phase2_risk(
        self,
        topic: str,
        individual_analyses: Dict[str, Dict[str, Any]],
        devil_report: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Phase 2b: Risk Analyst分析"""
        try:
            engine = self.engines["risk_analyst"]
            ctx = {
                "topic": topic,
                "_individual_analyses": individual_analyses,
                "_devil_report": devil_report,
                "target": topic,
                "market_environment": "",
                "valuation_metrics": {},
            }
            return await engine.analyze(ctx)
        except Exception as e:
            logger.error(f"Risk Analyst 失败: {e}")
            return {"agent_name": "risk_analyst", "error": str(e), "overall_risk_score": 50}

    async def _phase3_cio(
        self,
        topic: str,
        individual_analyses: Dict[str, Dict[str, Any]],
        devil_report: Dict[str, Any],
        risk_assessment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Phase 3: CIO汇总"""
        try:
            engine = self.engines["cio_synthesizer"]
            ctx = {
                "topic": topic,
                "_individual_analyses": individual_analyses,
                "_devil_report": devil_report,
                "_risk_assessment": risk_assessment,
            }
            return await engine.analyze(ctx)
        except Exception as e:
            logger.error(f"CIO汇总 失败: {e}")
            return {
                "agent_name": "cio_synthesizer",
                "error": str(e),
                "final_conclusion": "CIO汇总失败，请参考各Agent独立分析",
                "confidence": 0.0,
                "probability_distribution": {"bullish": 0.33, "neutral": 0.34, "bearish": 0.33},
            }

    async def run_daily_pipeline(
        self,
        market_summary: Dict[str, Any],
        news: List[Dict[str, Any]],
        macro_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        每日流水线（asyncio版本）。

        Args:
            market_summary: 市场概况
            news: 新闻列表
            macro_data: 宏观数据

        Returns:
            完整的每日分析报告
        """
        context = {
            "market_summary": market_summary,
            "news": news,
            "macro_data": macro_data,
        }
        topic = f"每日市场分析 - {datetime.now().strftime('%Y-%m-%d')}"
        return await self.run_debate(topic, context)


# ============================================================================
# 便捷函数
# ============================================================================

async def run_committee_debate(topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    便捷函数：一键运行委员会辩论。

    自动选择可用的实现（LangGraph或asyncio）。

    Args:
        topic: 分析主题
        context: 分析上下文

    Returns:
        完整的委员会分析结果
    """
    orchestrator = CommitteeOrchestrator()
    return await orchestrator.run_debate(topic, context)
