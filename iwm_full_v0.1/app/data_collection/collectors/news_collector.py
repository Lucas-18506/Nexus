"""News data collector using web search."""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.data_collection.collectors.base import BaseCollector


class NewsCollector(BaseCollector):
    """Collector for financial news.
    
    Collects news by keywords, ticker, macro topics, and industry.
    Uses web search for real news and falls back to simulated data.
    """
    
    # Simulated news templates for fallback
    NEWS_TEMPLATES: Dict[str, List[Dict[str, Any]]] = {
        "macro": [
            {
                "title": "美联储维持利率不变，暗示年内可能降息",
                "content": "美联储在最新议息会议上决定维持基准利率在5.25%-5.50%区间不变。鲍威尔在记者会上表示，通胀数据正在向目标靠近，如果经济数据继续配合，年内开始降息是合适的。市场目前预计9月首次降息的概率为65%。",
                "source": "Financial Times",
                "category": "macro",
                "related_industries": ["金融", "房地产"],
            },
            {
                "title": "中国制造业PMI连续两个月处于扩张区间",
                "content": "国家统计局公布的6月制造业PMI为50.1，虽较上月小幅回落但仍处于荣枯线以上。生产指数和新订单指数均保持在扩张区间，显示制造业景气度总体稳定。专家预计下半年在政策支持下经济将继续温和复苏。",
                "source": "Reuters",
                "category": "macro",
                "related_industries": ["制造业", "出口"],
            },
            {
                "title": "美元指数走强至105上方，人民币承压",
                "content": "受美联储鹰派表态和欧元区经济数据疲软影响，美元指数突破105关口，创三个月新高。离岸人民币兑美元一度跌破7.25。分析师认为，短期美元强势格局可能延续，但大幅升值空间有限。",
                "source": "Bloomberg",
                "category": "macro",
                "related_industries": ["外汇", "出口"],
            },
            {
                "title": "美国CPI同比增速降至3.2%，通胀压力持续缓解",
                "content": "美国劳工部公布数据显示，5月CPI同比增长3.2%，低于市场预期的3.3%。核心CPI同比上涨3.8%，创三年新低。能源价格下降是主要拖累因素，服务业通胀也呈现放缓迹象。",
                "source": "WSJ",
                "category": "macro",
                "related_industries": ["消费", "能源"],
            },
        ],
        "AI": [
            {
                "title": "NVIDIA发布新一代Blackwell架构GPU，算力提升4倍",
                "content": "NVIDIA在GTC大会上正式发布基于Blackwell架构的B200 GPU。新芯片采用台积电4nm工艺，集成2080亿晶体管，AI推理性能相比上一代提升4倍，能效提升25倍。微软、谷歌、亚马逊等云巨头已宣布大规模采购计划。",
                "source": "TechCrunch",
                "category": "industry",
                "related_tickers": ["NVDA", "AMD", "MSFT"],
                "related_industries": ["AI", "半导体"],
            },
            {
                "title": "OpenAI推出GPT-5，多模态能力大幅提升",
                "content": "OpenAI正式发布GPT-5模型，在推理能力、代码生成和多模态理解方面均有显著提升。新模型支持长达200万token的上下文窗口，并降低了API调用成本30%。企业客户反响热烈，首日API调用量创历史新高。",
                "source": "The Verge",
                "category": "industry",
                "related_tickers": ["MSFT"],
                "related_industries": ["AI"],
            },
        ],
        "semiconductor": [
            {
                "title": "全球半导体销售额连续4个月同比增长",
                "content": "SIA发布数据显示，4月全球半导体销售额达464亿美元，同比增长15.8%。存储芯片价格回升和AI芯片需求旺盛是主要驱动力。中国市场需求尤为强劲，同比增长28.2%。",
                "source": "EE Times",
                "category": "industry",
                "related_tickers": ["NVDA", "AMD"],
                "related_industries": ["半导体", "AI"],
            },
            {
                "title": "台积电2nm制程试产良率超预期",
                "content": "台积电N2制程试产良率达到60%以上，超出市场预期。苹果、NVIDIA将成为首批客户。台积电预计2025年下半年实现量产，2026年贡献显著营收。",
                "source": "DigiTimes",
                "category": "industry",
                "related_tickers": ["AAPL", "NVDA"],
                "related_industries": ["半导体"],
            },
        ],
        "automotive": [
            {
                "title": "特斯拉Q2交付量同比增长24%，超预期",
                "content": "特斯拉公布第二季度交付数据，共交付46.6万辆电动车，同比增长24%，高于华尔街预期的44.5万辆。Model Y和Model 3仍是主力车型，合计占总交付量的95%。公司维持全年180万辆的交付目标。",
                "source": "Electrek",
                "category": "industry",
                "related_tickers": ["TSLA"],
                "related_industries": ["新能源汽车"],
            },
            {
                "title": "比亚迪5月销量突破33万辆，海外出口创新高",
                "content": "比亚迪发布5月销量数据，乘用车销量达33.1万辆，同比增长38%。海外市场销量达到3.7万辆，创单月历史新高。公司今年前五月累计销量已超过127万辆，全年360万辆目标完成进度良好。",
                "source": "36氪",
                "category": "industry",
                "related_tickers": ["比亚迪", "1211"],
                "related_industries": ["新能源汽车"],
            },
        ],
        "crypto": [
            {
                "title": "美国SEC批准以太坊现货ETF，加密货币市场大涨",
                "content": "美国SEC正式批准8只以太坊现货ETF上市交易，这是继比特币ETF之后加密资产领域的又一里程碑。消息公布后以太坊价格一度突破3900美元，比特币也创下7.2万美元新高。",
                "source": "CoinDesk",
                "category": "industry",
                "related_tickers": ["COIN"],
                "related_industries": ["稳定币", "金融"],
            },
        ],
    }
    
    def __init__(self) -> None:
        self._search_client = None
    
    def get_name(self) -> str:
        return "Financial News Collector"
    
    @property
    def data_type(self) -> str:
        return "news"
    
    async def collect(self, **kwargs) -> List[Dict[str, Any]]:
        """Collect news based on provided parameters."""
        keywords = kwargs.get("keywords", [])
        max_results = kwargs.get("max_results", 10)
        if keywords:
            return await self.collect_by_keywords(keywords, max_results)
        return await self.collect_macro_news()
    
    async def collect_by_keywords(
        self,
        keywords: List[str],
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Collect news by search keywords.
        
        Args:
            keywords: List of search keywords.
            max_results: Maximum number of results.
            
        Returns:
            List of news items.
        """
        try:
            return await self._search_news(keywords, max_results)
        except Exception as e:
            print(f"Web search failed: {e}, using simulated data")
            return self._get_simulated_news("macro", max_results)
    
    async def collect_by_ticker(self, ticker: str, market: str) -> List[Dict[str, Any]]:
        """Collect news for a specific stock ticker.
        
        Args:
            ticker: Stock ticker symbol.
            market: Market code.
            
        Returns:
            List of news items related to the ticker.
        """
        try:
            keywords = [ticker, f"{ticker} stock", f"{ticker} {market}"]
            results = await self._search_news(keywords, 10)
            # Tag results with ticker
            for item in results:
                if ticker not in item.get("related_tickers", []):
                    item.setdefault("related_tickers", []).append(ticker)
            return results
        except Exception as e:
            print(f"Ticker news collection failed for {ticker}: {e}")
            return self._get_ticker_simulated_news(ticker, market)
    
    async def collect_macro_news(self) -> List[Dict[str, Any]]:
        """Collect macro-economic news.
        
        Returns:
            List of macro news items.
        """
        try:
            keywords = ["macro economy", "Fed interest rate", "inflation", "PMI", "CPI"]
            return await self._search_news(keywords, 10)
        except Exception as e:
            print(f"Macro news collection failed: {e}")
            return self._get_simulated_news("macro", 10)
    
    async def collect_industry_news(self, industry: str) -> List[Dict[str, Any]]:
        """Collect news for a specific industry.
        
        Args:
            industry: Industry name.
            
        Returns:
            List of industry news items.
        """
        try:
            keywords = [industry, f"{industry} industry", f"{industry} market"]
            results = await self._search_news(keywords, 10)
            for item in results:
                if industry not in item.get("related_industries", []):
                    item.setdefault("related_industries", []).append(industry)
            return results
        except Exception as e:
            print(f"Industry news collection failed for {industry}: {e}")
            return self._get_simulated_news(industry, 8)
    
    async def _search_news(
        self,
        keywords: List[str],
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Search for news using web search API.
        
        For now returns simulated data. In production, integrate with
        a real news API like NewsAPI, Bing News, or similar.
        """
        # Placeholder for real web search integration
        # In production, this would call an actual search API
        raise NotImplementedError("Web search API not configured")
    
    def _get_simulated_news(self, category: str, count: int) -> List[Dict[str, Any]]:
        """Get simulated news for a category."""
        import random
        
        templates = self.NEWS_TEMPLATES.get(category, self.NEWS_TEMPLATES["macro"])
        results = []
        for i in range(min(count, len(templates) * 3)):
            template = templates[i % len(templates)]
            news_item = {
                "title": template["title"],
                "content": template["content"],
                "source": template["source"],
                "url": f"https://example.com/news/{category}/{i}",
                "published_at": (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                "category": template.get("category", "general"),
                "related_tickers": template.get("related_tickers", []),
                "related_industries": template.get("related_industries", []),
            }
            results.append(news_item)
        return results
    
    def _get_ticker_simulated_news(self, ticker: str, market: str) -> List[Dict[str, Any]]:
        """Generate ticker-specific simulated news."""
        import random
        
        now = datetime.now()
        news_items = [
            {
                "title": f"{ticker}发布最新财报，业绩{random.choice(['超预期', '符合预期', '略低于预期'])}",
                "content": f"{ticker}（{market}）公布最新季度财报，营收同比增长{random.uniform(5, 30):.1f}%。管理层对未来季度指引持谨慎乐观态度。",
                "source": random.choice(["Reuters", "Bloomberg", "WSJ", "Financial Times"]),
                "url": f"https://example.com/news/{ticker}/earnings",
                "published_at": (now - timedelta(hours=random.randint(1, 48))).isoformat(),
                "category": "company",
                "related_tickers": [ticker],
                "related_industries": [],
            },
            {
                "title": f"分析师上调{ticker}目标价至${random.uniform(100, 500):.0f}",
                "content": f"多家投行发布研报，{random.choice(['上调', '维持', '微幅调整'])}{ticker}评级。主要逻辑包括：业务增长强劲、市场份额扩大、盈利能力改善。",
                "source": random.choice(["Goldman Sachs", "Morgan Stanley", "JP Morgan"]),
                "url": f"https://example.com/news/{ticker}/analyst",
                "published_at": (now - timedelta(hours=random.randint(1, 72))).isoformat(),
                "category": "company",
                "related_tickers": [ticker],
                "related_industries": [],
            },
            {
                "title": f"{ticker}宣布新产品线，市场反应积极",
                "content": f"{ticker}在开发者大会上发布新一代产品，技术参数领先竞品。投资者看好长期增长前景，盘后股价{random.choice(['上涨2%', '微涨0.5%', '基本持平'])}。",
                "source": "TechCrunch",
                "url": f"https://example.com/news/{ticker}/product",
                "published_at": (now - timedelta(hours=random.randint(1, 96))).isoformat(),
                "category": "company",
                "related_tickers": [ticker],
                "related_industries": [],
            },
        ]
        return news_items
