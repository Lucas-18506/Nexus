"""Preset company knowledge base data."""

from typing import Dict, Any, List


# Predefined company data with comprehensive attributes
PRESET_COMPANIES: List[Dict[str, Any]] = [
    # US Stocks
    {
        "ticker": "NVDA",
        "market": "US",
        "name": "NVIDIA",
        "industry_name": "AI",
        "description": (
            "NVIDIA是全球AI芯片龙头，GPU产品在深度学习训练/推理市场占据主导地位。 "
            "数据中心业务（含AI芯片）已成为公司第一大收入来源，占比超80%。 "
            "最新Blackwell架构B200 GPU算力提升4倍，客户覆盖所有主流云厂商和AI公司。"
        ),
        "business_model": (
            "硬件销售（GPU/ DPU/ 网络芯片）+ 软件平台（CUDA生态/ AI Enterprise） "
            "+ 云服务（DGX Cloud）。通过CUDA软件生态锁定开发者，形成硬件-软件-服务的 "
            "闭环商业模式。"
        ),
        "moat": (
            "1. CUDA生态护城河：15年积累，400万+开发者，深度学习框架标准绑定； "
            "2. 制程领先：与台积电深度合作，率先采用先进制程； "
            "3. 全栈能力：从芯片到系统到软件的唯一全栈供应商； "
            "4. 网络效应：越多开发者使用CUDA，生态越强大。"
        ),
        "risk_points": [
            "客户自研芯片风险（Google TPU、Amazon Trainium、微软Maia）",
            "地缘政治出口管制限制中国市场收入",
            "估值处于历史高位，业绩增速需持续超预期",
            "AI投资泡沫破裂风险",
            "AMD竞争加剧及开源ROCm生态发展",
        ],
    },
    {
        "ticker": "TSLA",
        "market": "US",
        "name": "Tesla",
        "industry_name": "新能源汽车",
        "description": (
            "Tesla是全球电动车龙头，同时布局能源存储（Megapack/Powerwall）和 "
            "自动驾驶（FSD）业务。2023年全球交付量超180万辆，上海工厂产能占全球一半。 "
            "FSD V12采用端到端神经网络，Robotaxi服务计划2024年推出。"
        ),
        "business_model": (
            "整车销售 + 软件订阅（FSD/OTA升级）+ 能源业务（储能/太阳能） "
            "+ 服务收入（超充网络/保险）。毛利率目标长期维持20%+， "
            "软件和服务是利润增长的关键驱动力。"
        ),
        "moat": (
            "1. 垂直整合能力：自研电池、电机、芯片、软件； "
            "2. 制造效率：一体化压铸等工艺创新带来成本优势； "
            "3. 超充网络：全球最大快充网络，向第三方开放； "
            "4. FSD数据闭环：数百万辆车实时采集驾驶数据，算法迭代速度快于竞争对手。"
        ),
        "risk_points": [
            "电动车需求增速放缓",
            "中国竞争对手价格战压力（比亚迪、蔚来、小鹏）",
            "FSD商业化进度不确定性",
            "马斯克精力分散（X、xAI、SpaceX等）",
            "自动驾驶安全事故与监管风险",
        ],
    },
    {
        "ticker": "AAPL",
        "market": "US",
        "name": "Apple",
        "industry_name": "消费电子",
        "description": (
            "Apple是全球最大的消费电子公司，iPhone占收入约50%，服务业务（App Store、 "
            "iCloud、Apple Music）快速增长。Apple Silicon自研芯片（M系列）性能领先， "
            "Vision Pro开创空间计算新品类。Apple Intelligence将AI功能深度集成至iOS生态。"
        ),
        "business_model": (
            "硬件销售（iPhone/Mac/iPad/Watch）+ 服务收入（App Store/云服务/支付/广告） "
            "+ 配件。服务业务毛利率70%+，是利润主要贡献来源。硬件毛利率约35%。"
        ),
        "moat": (
            "1. 品牌溢价：全球最有价值品牌，用户忠诚度极高； "
            "2. 生态锁定：iOS/macOS/watchOS无缝协同，切换成本高； "
            "3. App Store护城河：开发者-用户双边网络效应； "
            "4. 自研芯片：M系列芯片性能功耗比领先行业。"
        ),
        "risk_points": [
            "iPhone换机周期延长，硬件增长乏力",
            "App Store反垄断监管压力（欧盟DMA）",
            "中国市场竞争加剧（华为回归）",
            "Vision Pro短期难以贡献显著收入",
            "AI功能落地进度落后竞争对手",
        ],
    },
    {
        "ticker": "MSFT",
        "market": "US",
        "name": "Microsoft",
        "industry_name": "AI",
        "description": (
            "Microsoft是全球最大的软件公司，Azure云业务是第二增长曲线，OpenAI最大投资方。 "
            "Copilot AI助手已整合至Office 365、GitHub、Bing等产品线。Azure市场份额约23%， "
            "稳居全球第二大云厂商。游戏业务通过收购Activision Blizzard实力大增。"
        ),
        "business_model": (
            "软件许可/订阅（Office 365/Windows）+ 云服务（Azure/IaaS/PaaS/SaaS） "
            "+ 游戏（Xbox/Game Pass）+ 广告（Bing/LinkedIn）。 "
            "云业务增速30%+，是估值的核心支撑。"
        ),
        "moat": (
            "1. 企业软件垄断：Office 365在办公套件市场绝对领先； "
            "2. Azure生态：与Windows/Office深度集成，企业客户粘性高； "
            "3. OpenAI绑定：独家云合作伙伴，AI时代先发优势； "
            "4. GitHub开发者生态：1亿+开发者，Copilot代码助手收费模式验证成功。"
        ),
        "risk_points": [
            "Azure增速放缓云市场竞争加剧（AWS/Google Cloud）",
            "AI巨额投资回报不确定性",
            "OpenAI关系变化及治理风险",
            "反垄断监管（Teams捆绑等）",
            "企业IT支出周期性下行",
        ],
    },
    {
        "ticker": "AMD",
        "market": "US",
        "name": "AMD",
        "industry_name": "半导体",
        "description": (
            "AMD是全球第二大CPU和GPU供应商，x86服务器CPU市场份额持续提升（超25%）。 "
            "收购Xilinx后成为FPGA龙头，MI300X AI加速器直接对标NVIDIA H100。 "
            "数据中心业务增速超50%，是核心增长引擎。"
        ),
        "business_model": (
            "芯片销售（CPU/GPU/FPGA/AI加速器）+ 嵌入式解决方案。 "
            "数据中心业务占比持续提升，目标在AI训练/推理市场获得显著份额。"
        ),
        "moat": (
            "1. x86架构双寡头之一，Zen架构性能追平/超越Intel； "
            "2. 开放生态（ROCm）挑战CUDA垄断； "
            "3. Chiplet设计灵活性，成本效益优势； "
            "4. Xilinx FPGA在通信/工业/汽车领域的客户关系。"
        ),
        "risk_points": [
            "AI芯片市场竞争激烈，NVIDIA领先优势显著",
            "ROCm生态远弱于CUDA，开发者迁移意愿低",
            "对台积电产能依赖度高",
            "PC市场周期性波动",
            "Intel反击（至强/ARC显卡）",
        ],
    },
    {
        "ticker": "COIN",
        "market": "US",
        "name": "Coinbase",
        "industry_name": "稳定币",
        "description": (
            "Coinbase是美国最大的加密货币交易所，上市公司中唯一 pure-play 加密标的。 "
            "提供零售/机构交易、托管、质押等全栈服务。收入主要来自交易手续费（约50%） "
            "和订阅服务（USDC利息分成、质押收入等）。ETF获批后托管业务大幅增长。"
        ),
        "business_model": (
            "交易手续费 + 订阅与服务收入（托管/质押/USDC）+ 利息收入。 "
            "致力于降低对交易手续费的依赖，提升经常性收入占比。"
        ),
        "moat": (
            "1. 合规优势：美国最合规的交易所，机构客户首选； "
            "2. 品牌信任：上市交易所，财务透明，托管业务优势； "
            "3. ETF托管：8只比特币ETF中7只选择Coinbase托管； "
            "4. 监管壁垒：BitLicense等牌照难以获取。"
        ),
        "risk_points": [
            "加密货币价格剧烈波动影响交易量",
            "SEC诉讼结果不确定性",
            "交易费率下行竞争压力",
            "黑客攻击与安全事件",
            "去中心化交易所（DEX）替代风险",
        ],
    },
    # HK Stocks
    {
        "ticker": "0700.HK",
        "market": "HK",
        "name": "腾讯",
        "industry_name": "AI",
        "description": (
            "腾讯是中国最大的互联网公司，微信月活超13亿，游戏业务全球第一（按收入）。 "
            "业务涵盖社交（微信/QQ）、游戏（王者/和平精英）、广告、金融科技（微信支付） "
            "及企业服务（腾讯云）。混元大模型已应用于微信搜一搜、腾讯文档等产品。"
        ),
        "business_model": (
            "游戏（内购/订阅）+ 社交网络（增值会员）+ 广告（社交广告/媒体广告） "
            "+ 金融科技（支付/理财）+ 企业服务（腾讯云）。游戏贡献约30%收入， "
            "广告和金融科技增速较快。"
        ),
        "moat": (
            "1. 微信超级APP：13亿月活，社交关系链难以迁移； "
            "2. 游戏IP储备：王者荣耀、和平精英等长青游戏持续贡献现金流； "
            "3. 投资组合：持有美团、拼多多、SEA等大量优质股权； "
            "4. 小程序生态：连接商家-用户，构建商业闭环。"
        ),
        "risk_points": [
            "游戏版号政策不确定性",
            "未成年人保护限制游戏收入",
            "广告业务受宏观经济影响",
            "云业务竞争激烈（阿里云/华为云）",
            "反垄断监管持续",
        ],
    },
    {
        "ticker": "9988.HK",
        "market": "HK",
        "name": "阿里巴巴",
        "industry_name": "AI",
        "description": (
            "阿里巴巴是中国最大的电商平台和云计算公司。业务包括淘宝天猫（国内电商）、 "
            "阿里云（国内云市场第一）、菜鸟物流、国际业务（Lazada/速卖通）及本地生活。 "
            "通义千问大模型在中文模型中处于第一梯队。组织变革后拆分为1+6+N架构。"
        ),
        "business_model": (
            "电商（佣金/广告）+ 云计算（IaaS/PaaS/SaaS）+ 物流（菜鸟） "
            "+ 国际零售/批发。云业务增速回升，电商面临拼多多/抖音激烈竞争。"
        ),
        "moat": (
            "1. 淘宝天猫品牌效应：用户心智中第一电商平台； "
            "2. 阿里云领先：国内公有云市场份额第一； "
            "3. 菜鸟物流网络：覆盖全国的高效物流基础设施； "
            "4. 数据资产：20年电商数据积累，AI训练数据优势。"
        ),
        "risk_points": [
            "电商市场份额被拼多多/抖音蚕食",
            "云业务增速放缓",
            "组织变革效果待验证",
            "中美关系对中概股估值压制",
            "蚂蚁集团整改进展",
        ],
    },
    {
        "ticker": "1211.HK",
        "market": "HK",
        "name": "比亚迪",
        "industry_name": "新能源汽车",
        "description": (
            "比亚迪是全球新能源汽车龙头，2023年销量超300万辆，超越Tesla成为全球第一。 "
            "垂直整合能力行业最强，自研电池（刀片电池）、电机、电控、芯片。 "
            "旗下高端品牌（仰望/方程豹/腾势）提升品牌形象和盈利能力。海外市场加速扩张。"
        ),
        "business_model": (
            "整车销售（王朝/海洋/高端品牌）+ 动力电池外供 + 手机部件/组装 "
            "+ 轨道交通。汽车业务毛利率约20%，规模效应持续释放。"
        ),
        "moat": (
            "1. 垂直整合：自研电池、电机、电控、芯片，成本控制能力最强； "
            "2. 规模优势：年销300万辆+，采购议价能力强； "
            "3. 刀片电池安全性：磷酸铁锂路线，热失控风险低； "
            "4. 品牌矩阵完善：从10万到100万价位全覆盖。"
        ),
        "risk_points": [
            "价格战侵蚀利润",
            "高端品牌形象建设挑战",
            "海外市场关税/政策壁垒",
            "智能驾驶技术落后于华为/小鹏",
            "电池技术路线竞争（固态电池）",
        ],
    },
    # A-Shares
    {
        "ticker": "比亚迪",
        "market": "CN",
        "name": "比亚迪股份有限公司",
        "industry_name": "新能源汽车",
        "description": (
            "A股上市的比亚迪股份有限公司，与港股1211.HK为同一主体不同市场上市。 "
            "中国新能源汽车绝对龙头，刀片电池技术领先，DM-i混动系统深受市场欢迎。 "
            "深圳总部，王传福为创始人/董事长。"
        ),
        "business_model": (
            "与港股一致：整车销售+电池外供+电子代工。 "
            "A股投资者以国内机构和个人为主，估值体系与港股存在差异。"
        ),
        "moat": (
            "1. 同港股：垂直整合与规模优势； "
            "2. A股流动性溢价：国内投资者更便利的标的； "
            "3. 政策红利：深圳本土企业，受益于大湾区新能源汽车产业政策。"
        ),
        "risk_points": [
            "与港股联动但溢价波动",
            "A股市场情绪波动大",
            "同港股业务风险因素",
        ],
    },
    {
        "ticker": "宁德时代",
        "market": "CN",
        "name": "宁德时代新能源科技股份有限公司",
        "industry_name": "新能源汽车",
        "description": (
            "宁德时代（CATL）是全球最大的动力电池制造商，2023年全球市场份额约37%。 "
            "客户包括Tesla、BMW、奔驰、蔚来、理想等主流车企。技术路线覆盖磷酸铁锂和三元锂， "
            "麒麟电池（CTP3.0）和神行电池（4C超充）代表行业最高技术水平。 "
            "储能电池业务增速超50%，是第二增长曲线。"
        ),
        "business_model": (
            "动力电池销售（占收入~80%）+ 储能电池销售（~15%）+ 电池材料回收。 "
            "与车企深度绑定，采用合资建厂模式锁定产能。技术授权收入（LRS模式）拓展新收入来源。"
        ),
        "moat": (
            "1. 规模与技术双领先：研发投入行业最高，专利数量第一； "
            "2. 客户绑定：与全球主流车企深度绑定，切换成本高； "
            "3. 制造效率：极限制造技术，良品率和产能利用率领先； "
            "4. 全产业链布局：从锂矿到材料到电池到回收的闭环。"
        ),
        "risk_points": [
            "二线电池厂（比亚迪/中创新航/亿纬锂能）竞争加剧",
            "整车厂自研电池趋势",
            "锂价波动影响盈利稳定性",
            "海外市场政策壁垒（美国IRA）",
            "新技术路线颠覆风险（固态电池/钠离子电池）",
        ],
    },
]


def get_company_data(ticker: str, market: str) -> Dict[str, Any] | None:
    """Get preset data for a specific company.
    
    Args:
        ticker: Company ticker symbol.
        market: Market code.
        
    Returns:
        Company data dictionary or None if not found.
    """
    for company in PRESET_COMPANIES:
        if company["ticker"] == ticker and company["market"] == market:
            return company
    return None


def get_companies_by_industry(industry_name: str) -> List[Dict[str, Any]]:
    """Get all preset companies in a specific industry.
    
    Args:
        industry_name: Industry name.
        
    Returns:
        List of company data dictionaries.
    """
    return [c for c in PRESET_COMPANIES if c["industry_name"] == industry_name]


def get_all_companies() -> List[Dict[str, Any]]:
    """Get all preset company data.
    
    Returns:
        List of all company data dictionaries.
    """
    return list(PRESET_COMPANIES)
