"""
Agent配置模块
定义所有分析Agent的配置参数、注册表和权重分配。
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class AgentConfig:
    """单个Agent的配置定义"""

    name: str
    role: str
    prompt_file: str
    model: str = "gpt-4o"
    temperature: float = 0.3
    expertise: List[str] = field(default_factory=list)
    weight: float = 0.1

    def __post_init__(self):
        """参数校验"""
        if not 0 <= self.temperature <= 2:
            raise ValueError(f"temperature必须在0-2之间，当前值: {self.temperature}")
        if not 0 <= self.weight <= 1:
            raise ValueError(f"weight必须在0-1之间，当前值: {self.weight}")


# Agent注册表：定义所有可用Agent
AGENT_REGISTRY: Dict[str, AgentConfig] = {
    "macro_analyst": AgentConfig(
        name="macro_analyst",
        role="宏观分析师",
        prompt_file="macro_analyst.txt",
        temperature=0.3,
        expertise=["利率", "通胀", "经济周期", "货币政策", "汇率"],
        weight=0.15,
    ),
    "industry_analyst": AgentConfig(
        name="industry_analyst",
        role="行业分析师",
        prompt_file="industry_analyst.txt",
        temperature=0.3,
        expertise=["行业景气度", "竞争格局", "技术变革", "政策分析"],
        weight=0.20,
    ),
    "supply_chain_analyst": AgentConfig(
        name="supply_chain_analyst",
        role="产业链分析师",
        prompt_file="supply_chain_analyst.txt",
        temperature=0.3,
        expertise=["供应链", "瓶颈分析", "利润分配", "传导机制"],
        weight=0.15,
    ),
    "scarcity_analyst": AgentConfig(
        name="scarcity_analyst",
        role="稀缺性分析师",
        prompt_file="scarcity_analyst.txt",
        temperature=0.3,
        expertise=["资源稀缺", "供需缺口", "卡脖子", "Alpha发现"],
        weight=0.15,
    ),
    "company_analyst": AgentConfig(
        name="company_analyst",
        role="公司分析师",
        prompt_file="company_analyst.txt",
        temperature=0.3,
        expertise=["基本面", "估值", "护城河", "财务分析"],
        weight=0.10,
    ),
    "sentiment_analyst": AgentConfig(
        name="sentiment_analyst",
        role="情绪分析师",
        prompt_file="sentiment_analyst.txt",
        temperature=0.4,
        expertise=["市场情绪", "行为金融", "逆向投资"],
        weight=0.05,
    ),
    "risk_analyst": AgentConfig(
        name="risk_analyst",
        role="风险分析师",
        prompt_file="risk_analyst.txt",
        temperature=0.3,
        expertise=["风险管理", "尾部风险", "情景分析"],
        weight=0.10,
    ),
    "devil_advocate": AgentConfig(
        name="devil_advocate",
        role="反驳者",
        prompt_file="devil_advocate.txt",
        temperature=0.5,
        expertise=["逆向思维", "逻辑审查", "群体思维识别"],
        weight=0.10,
    ),
    "cio_synthesizer": AgentConfig(
        name="cio_synthesizer",
        role="CIO汇总者",
        prompt_file="cio_synthesizer.txt",
        temperature=0.2,
        expertise=["投资决策", "组合管理", "综合判断"],
        weight=0.0,
    ),
}

# CIO汇总时各Agent的权重分配（必须与AGENT_REGISTRY中的weight一致）
AGENT_WEIGHTS: Dict[str, float] = {
    "macro_analyst": 0.15,
    "industry_analyst": 0.20,
    "supply_chain_analyst": 0.15,
    "scarcity_analyst": 0.15,
    "company_analyst": 0.10,
    "sentiment_analyst": 0.05,
    "risk_analyst": 0.10,
    "devil_advocate": 0.10,
}

# 并行分析阶段运行的Agent（不包括Devil、Risk、CIO）
PARALLEL_AGENTS: List[str] = [
    "macro_analyst",
    "industry_analyst",
    "supply_chain_analyst",
    "scarcity_analyst",
    "company_analyst",
    "sentiment_analyst",
]

# 串行阶段Agent
SEQUENTIAL_AGENTS: Dict[str, List[str]] = {
    "phase1_parallel": PARALLEL_AGENTS,
    "phase2_devil": ["devil_advocate"],
    "phase2_risk": ["risk_analyst"],
    "phase3_consensus": ["cio_synthesizer"],
}


def get_agent_config(agent_name: str) -> AgentConfig:
    """根据名称获取Agent配置"""
    if agent_name not in AGENT_REGISTRY:
        raise KeyError(f"未知Agent: {agent_name}。可用Agent: {list(AGENT_REGISTRY.keys())}")
    return AGENT_REGISTRY[agent_name]


def get_prompt_path(agent_name: str, prompts_dir: str = "app/agents/prompts") -> str:
    """获取Agent提示词文件的完整路径"""
    config = get_agent_config(agent_name)
    import os
    return os.path.join(prompts_dir, config.prompt_file)
