"""
分析引擎模块
负责执行单个Agent的分析任务：加载提示词、调用LLM、解析输出。
提供LLM调用和模拟结果两种模式。
"""

import json
import os
import re
from typing import Dict, Any, Optional
from dataclasses import asdict

from app.agents.agent_configs import AgentConfig


class AnalysisEngine:
    """
    单个Agent的分析引擎。

    职责：
    1. 加载Agent对应的提示词文件
    2. 将用户上下文与系统提示词组合
    3. 调用LLM（或返回模拟结果）
    4. 解析LLM输出的JSON
    5. 返回结构化的分析结果
    """

    def __init__(self, agent_config: AgentConfig, prompts_dir: Optional[str] = None) -> None:
        """
        初始化分析引擎

        Args:
            agent_config: Agent配置对象
            prompts_dir: 提示词文件目录，默认为 app/agents/prompts
        """
        self.config = agent_config
        self.prompts_dir = prompts_dir or os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "prompts"
        )
        self.prompt_content: Optional[str] = None
        self._llm_client: Optional[Any] = None

        # 尝试初始化LLM客户端
        self._init_llm_client()

    def _init_llm_client(self) -> None:
        """尝试初始化OpenAI客户端，如果失败则标记为不可用"""
        try:
            from openai import AsyncOpenAI
            import os

            api_key = os.environ.get("OPENAI_API_KEY")
            if api_key:
                self._llm_client = AsyncOpenAI(api_key=api_key)
        except ImportError:
            self._llm_client = None
        except Exception:
            self._llm_client = None

    @property
    def llm_available(self) -> bool:
        """判断LLM是否可用"""
        return self._llm_client is not None

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行分析。

        流程：
        1. 读取prompt文件
        2. 构建完整prompt
        3. 调用LLM（或模拟）
        4. 解析JSON输出
        5. 返回结果

        Args:
            context: 分析上下文数据字典

        Returns:
            结构化的分析结果字典
        """
        # 步骤1：加载提示词
        system_prompt = self._load_prompt(self.config.prompt_file)

        # 步骤2：构建完整prompt
        user_context = json.dumps(context, ensure_ascii=False, indent=2)
        full_prompt = f"{system_prompt}\n\n# 待分析数据\n{user_context}"

        # 步骤3：调用LLM或生成模拟结果
        if self.llm_available and self._llm_client is not None:
            try:
                response = await self._call_llm(full_prompt)
                result = self._parse_json_response(response)
                result["_source"] = "llm"
                result["_agent_name"] = self.config.name
                return result
            except Exception as e:
                # LLM调用失败，降级到模拟结果
                result = self._generate_mock_result(context)
                result["_source"] = "mock_fallback"
                result["_agent_name"] = self.config.name
                result["_error"] = str(e)
                return result
        else:
            # LLM不可用，使用模拟结果
            result = self._generate_mock_result(context)
            result["_source"] = "mock"
            result["_agent_name"] = self.config.name
            return result

    def _load_prompt(self, prompt_file: str) -> str:
        """
        从prompts目录读取提示词文件

        Args:
            prompt_file: 提示词文件名

        Returns:
            提示词文件内容字符串
        """
        prompt_path = os.path.join(self.prompts_dir, prompt_file)
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"提示词文件未找到: {prompt_path}")
        except Exception as e:
            raise RuntimeError(f"读取提示词文件失败: {prompt_path}, 错误: {e}")

    async def _call_llm(self, prompt: str) -> str:
        """
        调用LLM获取分析结果

        Args:
            prompt: 完整的提示词

        Returns:
            LLM的文本响应
        """
        if self._llm_client is None:
            raise RuntimeError("LLM客户端未初始化")

        response = await self._llm_client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": "你是一个专业的投资分析师。请严格按照提示词要求输出JSON格式结果。"},
                {"role": "user", "content": prompt},
            ],
            temperature=self.config.temperature,
            max_tokens=4000,
        )

        return response.choices[0].message.content or "{}"

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """
        从LLM输出中提取JSON

        处理策略：
        1. 先尝试直接解析整个响应
        2. 如果失败，尝试提取markdown代码块中的JSON
        3. 如果还失败，尝试用正则表达式提取JSON对象

        Args:
            response: LLM的原始文本响应

        Returns:
            解析后的字典
        """
        # 策略1：直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 策略2：提取markdown代码块
        try:
            code_block_pattern = r"```(?:json)?\s*\n?(.*?)\n?```"
            matches = re.findall(code_block_pattern, response, re.DOTALL)
            if matches:
                return json.loads(matches[0].strip())
        except (json.JSONDecodeError, IndexError):
            pass

        # 策略3：正则提取JSON对象
        try:
            json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
            matches = re.findall(json_pattern, response, re.DOTALL)
            if matches:
                # 尝试解析最大的匹配（通常是最完整的JSON）
                for match in sorted(matches, key=len, reverse=True):
                    try:
                        return json.loads(match)
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

        # 所有策略都失败，返回原始文本包裹的错误结果
        return {
            "agent_name": self.config.name,
            "conclusion": f"JSON解析失败，原始响应: {response[:500]}",
            "confidence": 0.0,
            "_parse_error": True,
            "_raw_response": response[:2000],
        }

    def _generate_mock_result(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成模拟分析结果（当LLM不可用时）。

        根据Agent类型和上下文生成合理的模拟结果，
        确保系统在没有LLM的情况下也能演示运行。

        Args:
            context: 分析上下文

        Returns:
            模拟的分析结果字典
        """
        agent_name = self.config.name
        topic = context.get("topic", context.get("industry_name", context.get("target_sector", "未知主题")))

        # 根据Agent类型生成不同的模拟结果
        mock_generators = {
            "macro_analyst": self._mock_macro,
            "industry_analyst": self._mock_industry,
            "supply_chain_analyst": self._mock_supply_chain,
            "scarcity_analyst": self._mock_scarcity,
            "company_analyst": self._mock_company,
            "sentiment_analyst": self._mock_sentiment,
            "risk_analyst": self._mock_risk,
            "devil_advocate": self._mock_devil,
            "cio_synthesizer": self._mock_cio,
        }

        generator = mock_generators.get(agent_name, self._mock_default)
        return generator(topic, context)

    def _mock_macro(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """宏观分析模拟结果"""
        cycle_phase = "复苏"
        risk_appetite = "risk_on"
        confidence = 0.70
        return {
            "agent_name": "macro_analyst",
            "conclusion": f"当前宏观经济处于{cycle_phase}阶段，政策支持持续发力，流动性环境相对宽松。通胀压力温和，利率处于下行通道，有利于风险资产表现。需关注外部环境变化和内需恢复的节奏。",
            "cycle_phase": cycle_phase,
            "risk_appetite": risk_appetite,
            "confidence": confidence,
            "key_factors": [
                {"factor": "货币政策", "direction": "positive", "magnitude": "high", "description": "央行维持宽松基调，降准降息空间仍存"},
                {"factor": "通胀水平", "direction": "neutral", "magnitude": "medium", "description": "CPI温和，PPI偏弱，暂无通胀压力"},
                {"factor": "经济增长", "direction": "positive", "magnitude": "medium", "description": "GDP增速逐季改善，内需回暖"},
            ],
            "impact_on_equity": "positive",
            "impact_on_bonds": "neutral",
            "impact_on_commodities": "positive",
            "risk_warnings": ["美联储政策转向风险", "地缘政治不确定性"],
            "supporting_evidence": [
                {"indicator": "PMI", "value": "50.8", "trend": "上升", "implication": "制造业景气回升"},
                {"indicator": "社融增速", "value": "10.5%", "trend": "上升", "implication": "信用扩张加速"},
            ],
            "contradicting_evidence": [
                {"indicator": "房地产销售", "value": "-8.5%", "trend": "下降", "implication": "地产拖累经济"},
                {"indicator": "出口增速", "value": "3.2%", "trend": "放缓", "implication": "外需走弱"},
            ],
        }

    def _mock_industry(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """行业分析模拟结果"""
        return {
            "agent_name": "industry_analyst",
            "conclusion": f"{topic}行业整体景气度处于中性偏积极区间，政策支持明确，技术升级加速推进。行业增速高于GDP增速，竞争格局正在优化，龙头企业优势扩大。",
            "prosperity_score": 62,
            "growth_outlook": "稳健增长",
            "key_drivers": [
                {"driver": "政策扶持", "impact": "positive", "strength": "strong", "duration": "中期"},
                {"driver": "技术升级", "impact": "positive", "strength": "moderate", "duration": "长期"},
                {"driver": "需求复苏", "impact": "positive", "strength": "moderate", "duration": "短期"},
            ],
            "competitive_landscape": {
                "concentration": "中度集中",
                "barriers": "中",
                "pricing_power": "均衡",
                "trend": "改善",
            },
            "policy_support": {"direction": "支持", "strength": "中", "sustainability": "可持续"},
            "risk_factors": ["技术迭代风险", "政策执行不及预期"],
            "confidence": 0.68,
            "supporting_evidence": [
                {"data_point": "行业收入增速", "value": "15.2%", "significance": "高于GDP增速，景气度确认"},
                {"data_point": "龙头企业市占率", "value": "35%", "significance": "集中度提升，竞争格局优化"},
            ],
            "contradicting_evidence": [
                {"data_point": "中小企业盈利", "value": "-5%", "significance": "分化严重，行业并非全面向好"},
            ],
        }

    def _mock_supply_chain(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """产业链分析模拟结果"""
        return {
            "agent_name": "supply_chain_analyst",
            "conclusion": f"{topic}产业链上游资源环节定价权较强，中游制造竞争激烈，下游渠道分散。核心瓶颈在上游关键材料，扩产周期较长，短期难以缓解。",
            "chain_structure": {
                "segments": ["上游原材料", "中游制造", "下游应用"],
                "description": "产业链呈金字塔结构，上游集中度高，下游分散",
                "complexity": "中等",
            },
            "bottleneck_nodes": [
                {"node": "上游关键材料", "severity": "high", "reason": "全球供应集中，扩产周期18-24个月", "duration": "中期持续"},
            ],
            "alternative_paths": [
                {"target_bottleneck": "上游关键材料", "alternative": "国产替代方案", "feasibility": "中", "timeline": "12-18个月", "cost_implication": "成本增加10-15%"},
            ],
            "margin_distribution": {
                "upstream_margin": "高",
                "midstream_margin": "中",
                "downstream_margin": "低",
                "trend": "利润向上游集中",
            },
            "transmission_lag": "3-6个月",
            "confidence": 0.72,
            "supporting_evidence": [
                {"observation": "上游材料价格持续上涨", "implication": "瓶颈确认，供给弹性不足"},
            ],
            "contradicting_evidence": [
                {"observation": "部分中游企业库存高企", "implication": "需求可能不及预期，瓶颈或缓解"},
            ],
        }

    def _mock_scarcity(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """稀缺性分析模拟结果"""
        return {
            "agent_name": "scarcity_analyst",
            "conclusion": f"{topic}领域存在结构性供需缺口，需求CAGR显著高于供给CAGR。核心卡脖子环节短期内难以突破，市场对该稀缺性的定价尚不充分，存在Alpha机会。",
            "scarcity_score": 72,
            "supply_demand_gap": {
                "demand_cagr": "22%",
                "supply_cagr": "12%",
                "gap_direction": "需求>供给",
                "gap_magnitude": "10个百分点缺口",
                "duration": "预计持续2-3年",
            },
            "chokepoint_identified": [
                {"chokepoint": "关键设备/材料", "bottleneck_type": "技术", "severity": "critical", "reversibility": "不可逆（短期）"},
            ],
            "alpha_opportunity": {
                "description": "稀缺环节龙头企业将享受量价齐升",
                "magnitude": "高",
                "duration": "中期(1-3年)",
                "catalyst": "下游需求超预期释放",
                "upside_scenario": "股价翻倍",
                "base_case": "上涨30-50%",
                "downside_scenario": "震荡整理",
            },
            "market_pricing_efficiency": {
                "efficiency_score": 45,
                "description": "市场认知存在偏差，稀缺性未被充分定价",
                "mispricing_degree": "轻度低估",
            },
            "confidence": 0.68,
            "supporting_evidence": [
                {"evidence": "需求端连续超预期", "weight": "high", "implication": "需求确定性高"},
                {"evidence": "核心供应商交付周期延长至6个月以上", "weight": "high", "implication": "供给瓶颈真实存在"},
            ],
            "contradicting_evidence": [
                {"evidence": "部分新进入者已宣布扩产计划", "weight": "medium", "implication": "中长期供给可能跟上"},
                {"evidence": "当前估值已高于历史均值", "weight": "medium", "implication": "部分稀缺性可能已被定价"},
            ],
        }

    def _mock_company(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """公司分析模拟结果"""
        return {
            "agent_name": "company_analyst",
            "conclusion": f"{topic}商业模式清晰，在细分领域具有技术护城河。财务状况健康，ROE稳定在较高水平。当前估值处于历史中位，安全边际适中。",
            "moat_strength": 68,
            "valuation_assessment": "合理",
            "financial_health": {
                "overall": "健康",
                "profitability": "强",
                "leverage": "安全",
                "cash_flow": "充沛",
                "working_capital": "高效",
            },
            "management_quality": "良好",
            "key_strengths": ["技术领先", "客户粘性强", "现金流充裕"],
            "key_concerns": ["估值不便宜", "单一客户集中度较高"],
            "confidence": 0.75,
            "supporting_evidence": [
                {"metric": "ROE", "value": "18.5%", "assessment": "高于行业平均"},
                {"metric": "毛利率", "value": "42%", "assessment": "护城河体现"},
            ],
            "contradicting_evidence": [
                {"metric": "PE", "value": "35x", "assessment": "估值处于历史高位"},
                {"metric": "客户集中度", "value": "前五大客户占比65%", "assessment": "存在依赖风险"},
            ],
        }

    def _mock_sentiment(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """情绪分析模拟结果"""
        return {
            "agent_name": "sentiment_analyst",
            "conclusion": f"市场情绪整体中性偏谨慎，未出现明显FOMO或恐慌迹象。机构资金保持观望，散户参与度一般。情绪指标未发出极端信号，市场处于蓄力阶段。",
            "sentiment_score": 52,
            "fomo_level": 35,
            "fear_level": 28,
            "institutional_behavior": "观望",
            "retail_behavior": "观望",
            "key_signals": [
                {"signal": "成交量", "reading": "缩量整理", "direction": "neutral", "strength": "中"},
                {"signal": "融资余额", "reading": "小幅增加", "direction": "bullish", "strength": "弱"},
            ],
            "divergences": [],
            "confidence": 0.65,
            "supporting_evidence": [
                {"indicator": "恐惧贪婪指数", "value": "52", "interpretation": "中性区域"},
                {"indicator": "换手率", "value": "2.1%", "interpretation": "正常水平"},
            ],
            "contradicting_evidence": [
                {"indicator": "北向资金流向", "value": "净流出", "interpretation": "外资偏谨慎"},
            ],
        }

    def _mock_risk(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """风险分析模拟结果"""
        return {
            "agent_name": "risk_analyst",
            "conclusion": f"{topic}整体风险水平中等，主要风险来自估值压力和政策不确定性。尾部风险可控，但需密切关注宏观环境变化和流动性收紧信号。",
            "overall_risk_score": 55,
            "valuation_risk": {"score": 60, "level": "中", "description": "估值处于历史中高位", "key_trigger": "盈利增速不及预期"},
            "policy_risk": {"score": 55, "level": "中", "description": "政策方向积极但执行存在不确定性", "key_trigger": "政策执行力度低于预期"},
            "liquidity_risk": {"score": 40, "level": "低", "description": "流动性环境整体宽松", "key_trigger": "央行政策转向"},
            "cycle_risk": {"score": 58, "level": "中", "description": "经济复苏初期，周期波动风险仍存", "key_trigger": "经济复苏中断"},
            "tail_risk_blackswan": {"score": 45, "level": "低", "description": "尾部风险概率较低", "key_trigger": "地缘冲突升级"},
            "risk_scenarios": [
                {"scenario": "基准情景", "probability": "50%", "impact": "中性", "expected_return": "0%~+10%", "description": "经济温和复苏，政策持续支持"},
                {"scenario": "乐观情景", "probability": "25%", "impact": "正面", "expected_return": "+20%~+30%", "description": "政策超预期，需求强劲释放"},
                {"scenario": "悲观情景", "probability": "20%", "impact": "负面", "expected_return": "-10%~-15%", "description": "复苏乏力，外部冲击"},
                {"scenario": "极端情景", "probability": "5%", "impact": "严重", "expected_return": "-20%以上", "description": "多重风险共振"},
            ],
            "risk_dashboard": {"color": "黄", "trend": "稳定", "urgency": "持续监控"},
            "confidence": 0.70,
            "supporting_evidence": [
                {"risk_factor": "估值", "indicator": "PE分位", "reading": "65%"},
                {"risk_factor": "波动率", "indicator": "VIX", "reading": "偏低"},
            ],
            "contradicting_evidence": [
                {"risk_factor": "流动性", "indicator": "M2增速", "reading": "充裕，缓解流动性风险"},
            ],
        }

    def _mock_devil(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Devil Advocate模拟结果"""
        analyses = context.get("analyses", {})
        return {
            "agent_name": "devil_advocate",
            "refutation_summary": "对各位分析师的结论进行审查后，发现以下关键问题：(1)宏观复苏的持续性存疑，地产拖累尚未出清；(2)行业景气度可能被短期政策刺激扭曲；(3)稀缺性叙事可能过度吸引人而忽视了周期性回落风险；(4)当前估值已反映部分乐观预期，安全边际不足。",
            "confidence": 0.72,
            "specific_challenges": [
                {
                    "target_agent": "macro_analyst",
                    "challenge": "复苏判断可能过度依赖PMI等领先指标，忽视了地产投资持续负增长对经济的拖累",
                    "alternative_hypothesis": "经济可能处于L型底部震荡，而非V型复苏",
                    "fatal_flaw": "no",
                    "severity": "medium",
                },
                {
                    "target_agent": "scarcity_analyst",
                    "challenge": "稀缺性叙事最容易产生认知偏差，产能扩张计划可能被系统性低估",
                    "alternative_hypothesis": "稀缺性可能在12-18个月内缓解，当前股价已透支",
                    "fatal_flaw": "possibly",
                    "severity": "high",
                },
                {
                    "target_agent": "company_analyst",
                    "challenge": "护城河评估可能过于静态，未充分考虑技术变革的颠覆性",
                    "alternative_hypothesis": "护城河可能在2-3年内被新技术侵蚀",
                    "fatal_flaw": "no",
                    "severity": "medium",
                },
            ],
            "neglected_risks": [
                {"risk": "全球供应链重组导致的长期需求萎缩", "probability": "中", "impact": "高", "why_missed": "其他Agent聚焦于国内供需，忽视全球格局变化"},
                {"risk": "技术路线突变导致存量投资贬值", "probability": "低中", "impact": "极高", "why_missed": "线性外推思维，未考虑颠覆性创新"},
            ],
            "assumption_challenges": [
                {"assumption": "政策将持续宽松", "challenged_by": "汇率和通胀约束可能限制政策空间", "if_wrong": "流动性收紧将冲击估值"},
                {"assumption": "需求增长可持续", "challenged_by": "下游库存积累可能预示需求透支", "if_wrong": "供需格局逆转，价格下行"},
            ],
            "scenario_if_wrong": {
                "description": "如果多数Agent判断错误，最可能的情景是经济二次探底叠加估值收缩，股价回调20-30%",
                "trigger": "政策转向或外部冲击",
                "downside": "-20%~-30%",
                "timeline": "6-12个月",
            },
            "groupthink_assessment": {
                "groupthink_risk": "中",
                "description": "各Agent观点方向性一致，存在隐性共识风险",
                "divergent_views": "情绪分析师相对谨慎，但整体多样性不足",
            },
            "supporting_evidence": [
                {"point": "历史数据显示稀缺性主题投资在第二年后往往表现不佳"},
                {"point": "当前估值水平已高于过去3年80%的时间"},
            ],
            "contradicting_evidence": [
                {"point": "龙头企业订单确实在增长，基本面有支撑"},
                {"point": "政策文件明确表态长期支持，方向确定"},
            ],
        }

    def _mock_cio(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """CIO汇总模拟结果"""
        return {
            "agent_name": "cio_synthesizer",
            "final_conclusion": f"综合各方分析，{topic}呈现\"基本面改善但估值已部分反映\"的格局。多数Agent看好中长期前景，但Devil的质疑值得重视——当前位置安全边际有限，不宜追高。建议采用分批建仓策略，等待回调加仓。",
            "confidence": 0.68,
            "probability_distribution": {"bullish": 0.40, "neutral": 0.35, "bearish": 0.25},
            "supporting_views_summary": [
                {"agent": "宏观分析师", "view": "复苏阶段有利于风险资产", "weight": 0.15, "confidence": 0.70},
                {"agent": "行业分析师", "view": "景气度上行，政策支持明确", "weight": 0.20, "confidence": 0.68},
                {"agent": "稀缺性分析师", "view": "结构性供需缺口提供Alpha", "weight": 0.15, "confidence": 0.68},
            ],
            "opposing_views_summary": [
                {"agent": "反驳者", "view": "群体思维风险，估值安全边际不足", "weight": 0.10, "confidence": 0.72},
                {"agent": "情绪分析师", "view": "市场未达极度悲观，逆向信号不足", "weight": 0.05, "confidence": 0.65},
            ],
            "max_risk": {
                "risk_type": "估值收缩+基本面恶化双杀",
                "probability": "20%",
                "potential_loss": "-20%~-30%",
                "mitigation": "控制仓位，设置止损",
            },
            "risk_reward_assessment": {
                "upside_potential": "+30%~+50%",
                "downside_risk": "-15%~-20%",
                "risk_reward_ratio": 1.8,
                "assessment": "中性偏有利",
            },
            "action_suggestion": {
                "direction": "持有",
                "urgency": "近期关注",
                "position_sizing": "半仓",
                "rationale": "基本面支撑存在，但估值限制了上行空间，等待更好的入场时机",
                "stop_loss": "下跌15%或基本面恶化信号",
                "key_triggers": ["回调10%以上加仓", "稀缺性确认信号加码", "情绪极度悲观时加仓"],
            },
            "key_assumptions": [
                {"assumption": "经济复苏持续", "importance": "critical", "if_wrong": "所有看多逻辑失效"},
                {"assumption": "政策不发生180度转向", "importance": "critical", "if_wrong": "估值全面收缩"},
                {"assumption": "稀缺性持续1年以上", "importance": "important", "if_wrong": "Alpha来源消失"},
            ],
            "confidence_breakdown": {
                "macro": 0.65,
                "industry": 0.70,
                "company": 0.75,
                "sentiment": 0.60,
                "overall": 0.68,
            },
            "agent_weights_used": {
                "macro_analyst": 0.15,
                "industry_analyst": 0.20,
                "supply_chain_analyst": 0.15,
                "scarcity_analyst": 0.15,
                "company_analyst": 0.10,
                "sentiment_analyst": 0.05,
                "risk_analyst": 0.10,
                "devil_advocate": 0.10,
            },
            "devil_impact_assessment": "Devil的质疑有效降低了整体置信度，从0.75调整至0.68。其核心关切（估值安全边际不足、群体思维风险）已被纳入最终判断，导致操作建议偏向保守。",
            "decision_rationale": "加权评分计算：宏观(+0.105) + 行业(+0.136) + 产业链(+0.081) + 稀缺性(+0.102) + 公司(+0.080) + 情绪(-0.003) + 风险(-0.028) + Devil(-0.072) = 合计+0.401，归一化后bullish概率40%。鉴于风险收益比1.8尚可但未达强烈信号阈值，建议持有观望。",
        }

    def _mock_default(self, topic: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """默认模拟结果"""
        return {
            "agent_name": self.config.name,
            "conclusion": f"[{self.config.role}] 对{topic}的分析完成。基于可用信息，整体判断偏向积极，但需关注不确定性因素。",
            "confidence": 0.60,
            "supporting_evidence": [],
            "contradicting_evidence": [],
        }
