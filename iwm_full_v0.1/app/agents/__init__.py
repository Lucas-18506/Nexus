"""
Agent集群模块

IWM投资参谋系统的核心Agent集群。

包含以下组件：
- 配置管理（agent_configs.py）
- 分析引擎（analysis_engine.py）
- 委员会工作流（committee.py）
- 报告生成器（report_generator.py）
- 记忆模块（memory/）
"""

from app.agents.agent_configs import (
    AgentConfig,
    AGENT_REGISTRY,
    AGENT_WEIGHTS,
    PARALLEL_AGENTS,
    SEQUENTIAL_AGENTS,
    get_agent_config,
    get_prompt_path,
)
from app.agents.analysis_engine import AnalysisEngine
from app.agents.committee import (
    CommitteeOrchestrator,
    AsyncCommitteeRunner,
    CommitteeState,
    create_committee_graph,
    run_committee_debate,
    phase1_parallel_analysis,
    phase2_devil_analysis,
    phase2_risk_analysis,
    phase3_consensus,
    phase4_report,
)
from app.agents.report_generator import ReportGenerator

__all__ = [
    # 配置
    "AgentConfig",
    "AGENT_REGISTRY",
    "AGENT_WEIGHTS",
    "PARALLEL_AGENTS",
    "SEQUENTIAL_AGENTS",
    "get_agent_config",
    "get_prompt_path",
    # 引擎
    "AnalysisEngine",
    # 委员会
    "CommitteeOrchestrator",
    "AsyncCommitteeRunner",
    "CommitteeState",
    "create_committee_graph",
    "run_committee_debate",
    "phase1_parallel_analysis",
    "phase2_devil_analysis",
    "phase2_risk_analysis",
    "phase3_consensus",
    "phase4_report",
    # 报告
    "ReportGenerator",
]
