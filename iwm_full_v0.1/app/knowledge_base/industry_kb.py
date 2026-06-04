"""Preset industry knowledge base data."""

from typing import Dict, Any, List


# Predefined industry data with comprehensive attributes
PRESET_INDUSTRIES: List[Dict[str, Any]] = [
    {
        "name": "AI",
        "description": (
            "人工智能行业涵盖大语言模型、计算机视觉、机器学习平台及AI应用。 "
            "当前处于由大模型驱动的技术爆发期，算力需求呈指数级增长，应用场景从 "
            "代码生成、内容创作快速扩展至科研、金融、医疗等专业领域。行业核心围绕 "
            "模型能力、算力基础设施、数据资产和应用层创新展开竞争。"
        ),
        "lifecycle_stage": "growth",
        "key_drivers": ["大模型迭代", "算力需求", "应用场景扩展"],
        "supply_chain": "GPU→HBM→光模块→数据中心→电力",
        "bottleneck": "高端GPU供应",
        "risk_factors": [
            "高端GPU出口管制风险",
            "大模型商业化落地不及预期",
            "监管政策不确定性",
            "算力成本持续高企",
            "技术路线更迭风险",
        ],
        "opportunities": [
            "企业AI渗透率仅15%，空间巨大",
            "AI Agent商业化前景",
            "端侧AI设备换机周期",
            "垂直行业AI解决方案",
            "国产算力替代机遇",
        ],
    },
    {
        "name": "机器人",
        "description": (
            "机器人行业包括工业机器人、服务机器人及新兴的人形机器人赛道。 "
            "随着AI大模型与机器人控制技术融合，人形机器人正从实验室走向商业化。 "
            "特斯拉Optimus、Figure AI等产品引领技术方向，制造业自动化升级和劳动力 "
            "短缺问题推动需求增长。产业链涵盖减速器、伺服电机、控制器、传感器到整机集成。"
        ),
        "lifecycle_stage": "emerging",
        "key_drivers": ["AI+机器人融合", "劳动力成本上升", "制造业自动化需求"],
        "supply_chain": "减速器→伺服电机→控制器→传感器→整机集成",
        "bottleneck": "高精度减速器与力矩传感器",
        "risk_factors": [
            "人形机器人商业化进度慢于预期",
            "核心零部件依赖进口",
            "安全与伦理监管风险",
            "场景落地成本高昂",
            "技术成熟度不足",
        ],
        "opportunities": [
            "人形机器人万亿级潜在市场",
            "制造业自动化升级需求",
            "老龄化社会服务机器人需求",
            "国产核心零部件替代空间",
            "AI赋能机器人智能化升级",
        ],
    },
    {
        "name": "稳定币",
        "description": (
            "稳定币及加密货币基础设施行业，涵盖数字资产交易、区块链技术、 "
            "DeFi协议及加密金融服务。随着美国SEC批准比特币和以太坊现货ETF， "
            "传统金融机构加速入场。稳定币作为连接传统金融与加密世界的桥梁， "
            "在跨境支付、资产代币化等领域展现应用价值。监管框架逐步明朗化。"
        ),
        "lifecycle_stage": "expansion",
        "key_drivers": ["ETF获批机构入场", "监管框架明朗化", "代币化资产趋势"],
        "supply_chain": "矿机/验证节点→交易所→托管→ETF→衍生品",
        "bottleneck": "监管合规与机构信任建设",
        "risk_factors": [
            "监管政策重大变化风险",
            "价格剧烈波动风险",
            "黑客攻击与安全事件",
            "市场情绪与流动性风险",
            "技术漏洞与智能合约风险",
        ],
        "opportunities": [
            "机构资金持续流入",
            "代币化资产万亿市场",
            "跨境支付效率提升",
            "DeFi创新应用场景",
            "合规基础设施需求",
        ],
    },
    {
        "name": "电力",
        "description": (
            "电力行业包括发电（火电、水电、核电、风光）、输配电和电力交易。 "
            "AI算力爆发带动数据中心电力需求激增，预计未来五年全球数据中心用电量 "
            "将翻倍。核电因基荷稳定性和低碳属性重新受到关注，小型模块化反应堆(SMR) "
            "技术路线备受关注。新能源消纳和电网智能化是行业核心议题。"
        ),
        "lifecycle_stage": "growth",
        "key_drivers": ["AI算力电力需求", "新能源装机增长", "核电重启"],
        "supply_chain": "燃料/铀→发电设备→输配电→售电→用户",
        "bottleneck": "电网消纳能力与输电通道",
        "risk_factors": [
            "燃料价格波动风险",
            "新能源消纳压力",
            "核电安全与审批风险",
            "电力市场化改革不确定性",
            "环保政策趋严",
        ],
        "opportunities": [
            "AI数据中心电力需求爆发",
            "核电SMR技术突破",
            "储能成本快速下降",
            "电网智能化改造",
            "绿电交易规模扩大",
        ],
    },
    {
        "name": "半导体",
        "description": (
            "半导体行业是电子信息产业的基础，涵盖芯片设计、制造、封测及设备材料。 "
            "AI芯片需求爆发式增长，先进制程（3nm及以下）竞争加剧，台积电、三星、 "
            "Intel三强争霸。成熟制程（28nm及以上）因汽车和工业需求保持景气。 "
            "国产替代在设备和材料领域持续推进，但光刻机等核心设备仍受制于人。"
        ),
        "lifecycle_stage": "mature",
        "key_drivers": ["AI芯片需求", "先进制程竞赛", "国产替代"],
        "supply_chain": "EDA/IP→设计→晶圆制造→封测→终端",
        "bottleneck": "EUV光刻机",
        "risk_factors": [
            "地缘政治与出口管制风险",
            "行业周期性波动",
            "先进制程资本开支巨大",
            "人才短缺",
            "技术追赶难度加大",
        ],
        "opportunities": [
            "AI芯片市场规模高速增长",
            "Chiplet技术降低门槛",
            "汽车半导体需求增长",
            "国产设备材料替代空间",
            "RISC-V开源架构机遇",
        ],
    },
    {
        "name": "消费电子",
        "description": (
            "消费电子行业包括智能手机、PC、平板、可穿戴设备及智能家居产品。 "
            "行业进入成熟期，换机周期延长，但AI功能集成有望刺激新一轮换机需求。 "
            "苹果生态闭环维持高端市场主导地位，安卓阵营在折叠屏、AI功能上寻求差异化。 "
            "Vision Pro等空间计算产品开辟新赛道，但短期内难以贡献显著收入。"
        ),
        "lifecycle_stage": "mature",
        "key_drivers": ["AI功能集成换机", "折叠屏渗透率", "空间计算新赛道"],
        "supply_chain": "芯片→屏幕→电池→结构件→组装→品牌",
        "bottleneck": "高端芯片供应",
        "risk_factors": [
            "换机周期延长",
            "创新乏力同质化竞争",
            "供应链集中度风险",
            "宏观经济影响消费意愿",
            "地缘政治关税风险",
        ],
        "opportunities": [
            "AI手机/PC换机周期",
            "折叠屏渗透率提升",
            "AR/VR新形态设备",
            "印度等新兴市场增长",
            "汽车电子跨界融合",
        ],
    },
    {
        "name": "新能源汽车",
        "description": (
            "新能源汽车行业涵盖电动车整车、动力电池、电机电控、充电桩及智能驾驶。 "
            "中国新能源车渗透率已超40%，进入市场化驱动阶段。全球来看，欧洲碳排放法规 "
            "和美国IRA补贴推动电动化转型。固态电池、高压快充、城市NOA智能驾驶是技术 "
            "竞争焦点。行业从高速增长转向高质量竞争，价格战趋缓但格局尚未稳定。"
        ),
        "lifecycle_stage": "growth",
        "key_drivers": ["渗透率持续提升", "电池技术进步", "智能驾驶普及"],
        "supply_chain": "锂矿→正极/负极→电芯→电池Pack→整车→充电",
        "bottleneck": "优质锂资源供应",
        "risk_factors": [
            "锂等原材料价格波动",
            "行业竞争加剧盈利压力",
            "欧美贸易壁垒升级",
            "技术路线不确定性",
            "充电基础设施不足",
        ],
        "opportunities": [
            "全球渗透率仍低于20%",
            "固态电池技术突破",
            "储能第二增长曲线",
            "智能驾驶商业化",
            "出海市场空间广阔",
        ],
    },
]


def get_industry_data(name: str) -> Dict[str, Any] | None:
    """Get preset data for a specific industry.
    
    Args:
        name: Industry name.
        
    Returns:
        Industry data dictionary or None if not found.
    """
    for industry in PRESET_INDUSTRIES:
        if industry["name"] == name:
            return industry
    return None


def get_all_industries() -> List[Dict[str, Any]]:
    """Get all preset industry data.
    
    Returns:
        List of all industry data dictionaries.
    """
    return list(PRESET_INDUSTRIES)
