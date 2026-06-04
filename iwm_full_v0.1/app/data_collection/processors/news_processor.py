"""News data processor."""

import re
from datetime import datetime
from typing import List, Dict, Any
from app.data_collection.processors.base import BaseProcessor


class NewsProcessor(BaseProcessor):
    """Processor for news articles.
    
    Extracts events, classifies impact, extracts entities,
    determines sentiment, and enriches news items.
    """
    
    # Impact keywords for scoring
    IMPACT_KEYWORDS: Dict[str, int] = {
        # High impact (5)
        "破产": 5, "bankruptcy": 5, "崩盘": 5, "crash": 5, "制裁": 5, "sanctions": 5,
        "违约": 5, "default": 5, "暴跌": 5, "plunge": 5, "腰斩": 5,
        # Strong impact (4)
        "暴跌": 4, "surge": 4, "飙升": 4, "飙升": 4, "大涨": 4, "soar": 4,
        " merger": 4, "收购": 4, "acquisition": 4, "合并": 4, "restructuring": 4,
        # Moderate impact (3)
        "上调": 3, "upgrade": 3, "下调": 3, "downgrade": 3, "超预期": 3,
        "beat": 3, "miss": 3, "不及预期": 3, "涨价": 3, "price hike": 3,
        # Low-moderate impact (2)
        "增长": 2, "growth": 2, "下滑": 2, "decline": 2, "放缓": 2, "slowdown": 2,
        "expansion": 2, "扩张": 2, "合作": 2, "partnership": 2,
        # Low impact (1)
        "计划": 1, "plan": 1, "考虑": 1, "consider": 1, "或将": 1, "may": 1,
    }
    
    # Sentiment keywords
    POSITIVE_KEYWORDS = [
        "增长", "growth", "上涨", "rise", "rally", "surge", "soar", "突破", "breakthrough",
        "超预期", "beat", "强劲", "strong", "利好", "bullish", "上调", "upgrade",
        "扩张", "expansion", "创新", "innovation", "领先", "leading", "success",
        "盈利", "profit", "增长", "increase", "复苏", "recovery", "改善", "improve",
        "乐观", "optimistic", "积极", "positive", "看好", "opportunity",
    ]
    
    NEGATIVE_KEYWORDS = [
        "下跌", "decline", "drop", "fall", "plunge", "crash", "暴跌", "崩盘",
        "不及预期", "miss", "疲软", "weak", "利空", "bearish", "下调", "downgrade",
        "萎缩", "shrinkage", "衰退", "recession", "亏损", "loss", "下降", "decrease",
        "放缓", "slowdown", "风险", "risk", "危机", "crisis", "违约", "default",
        "悲观", "pessimistic", "消极", "negative", "担忧", "concern", "制裁", "sanctions",
    ]
    
    # Ticker patterns
    TICKER_PATTERNS = {
        "US": re.compile(r'\b(AAPL|MSFT|GOOGL|AMZN|TSLA|NVDA|META|NFLX|AMD|INTC|CRM|COIN|UBER|LYFT|BABA|PDD)\b'),
        "HK": re.compile(r'\b(0700|9988|1211|3690|1810|2318|1299|0883|0005)\b'),
    }
    
    INDUSTRY_KEYWORDS: Dict[str, List[str]] = {
        "AI": ["AI", "人工智能", "大模型", "LLM", "GPT", "机器学习", "machine learning", "generative AI"],
        "半导体": ["半导体", "芯片", "chip", "GPU", "CPU", "晶圆", "foundry", "semiconductor", "台积电"],
        "新能源汽车": ["新能源", "电动车", "EV", "electric vehicle", "Tesla", "特斯拉", "比亚迪", "battery"],
        "消费电子": ["消费电子", "consumer electronics", "iPhone", "smartphone", "可穿戴", "wearable"],
        "机器人": ["机器人", "robot", "robotics", "人形机器人", "humanoid", "automation"],
        "稳定币": ["加密货币", "crypto", "比特币", "bitcoin", "ethereum", "区块链", "blockchain", "ETF"],
        "电力": ["电力", "electricity", "发电", "power", "电网", "grid", "renewable", "核电", "nuclear"],
        "金融": ["金融", "银行", "bank", "保险", "insurance", "券商", "证券", "SEC", "美联储", "Fed"],
        "云计算": ["云计算", "cloud", "AWS", "Azure", "data center", "数据中心"],
    }
    
    async def process(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Main processing pipeline for news items.
        
        Args:
            raw_data: List of raw news dictionaries.
            
        Returns:
            List of processed and enriched news dictionaries.
        """
        processed = []
        for item in raw_data:
            try:
                enriched = await self._process_single(item)
                processed.append(enriched)
            except Exception as e:
                print(f"Error processing news item: {e}")
                # Include original item with minimal processing
                item["sentiment"] = "neutral"
                item["impact_score"] = 0
                item["processed"] = True
                processed.append(item)
        return processed
    
    async def _process_single(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single news item."""
        # Extract entities
        entities = self.extract_entities(item)
        item["related_tickers"] = entities.get("tickers", item.get("related_tickers", []))
        item["related_industries"] = entities.get("industries", item.get("related_industries", []))
        
        # Determine sentiment
        item["sentiment"] = self.determine_sentiment(item)
        
        # Classify impact
        item["impact_score"] = self.classify_impact(item)
        
        # Mark as processed
        item["processed"] = True
        item["processed_at"] = datetime.utcnow().isoformat()
        
        return item
    
    def extract_events(self, news_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract events from a list of news items.
        
        Uses keyword matching to identify significant events.
        
        Args:
            news_items: List of processed news items.
            
        Returns:
            List of extracted events.
        """
        events = []
        event_keywords = {
            "earnings": ["财报", "earnings", "revenue", "profit", "EPS", "业绩"],
            "product_launch": ["发布", "launch", "新品", "new product", " unveil"],
            "merger_acquisition": ["收购", "acquisition", "合并", "merger", "M&A"],
            "policy_change": ["政策", "policy", "监管", "regulation", "SEC", "美联储"],
            "partnership": ["合作", "partnership", "alliance", "strategic"],
            "personnel": ["CEO", "高管", "executive", "resign", "appointment", "任命"],
            "market_movement": ["暴涨", "暴跌", "涨停", "跌停", "all-time high", "record low"],
        }
        
        for item in news_items:
            try:
                title = item.get("title", "")
                content = item.get("content", "")
                text = f"{title} {content}"
                
                for event_type, keywords in event_keywords.items():
                    if any(kw in text for kw in keywords):
                        event = {
                            "title": title,
                            "description": content[:500] if content else title,
                            "event_type": event_type,
                            "severity": item.get("impact_score", 2),
                            "related_tickers": item.get("related_tickers", []),
                            "related_industries": item.get("related_industries", []),
                            "source_news_ids": [item.get("id", 0)],
                            "occurred_at": item.get("published_at", datetime.utcnow().isoformat()),
                            "created_at": datetime.utcnow().isoformat(),
                        }
                        events.append(event)
                        break  # One event per news item
            except Exception as e:
                print(f"Error extracting event: {e}")
                continue
        
        return events
    
    def classify_impact(self, news_item: Dict[str, Any]) -> int:
        """Classify the impact level of a news item (0-5).
        
        Args:
            news_item: News item dictionary with title and content.
            
        Returns:
            Impact score from 0 (no impact) to 5 (maximum impact).
        """
        try:
            text = f"{news_item.get('title', '')} {news_item.get('content', '')}"
            score = 0
            
            for keyword, weight in self.IMPACT_KEYWORDS.items():
                if keyword in text:
                    score = max(score, weight)
            
            # Boost score for breaking/financial news sources
            high_impact_sources = ["Bloomberg", "Reuters", "WSJ", "Financial Times"]
            source = news_item.get("source", "")
            if any(s in source for s in high_impact_sources):
                score = min(5, score + 1)
            
            return min(5, max(0, score))
        except Exception:
            return 0
    
    def extract_entities(self, news_item: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract ticker symbols and industries from a news item.
        
        Args:
            news_item: News item dictionary.
            
        Returns:
            Dictionary with 'tickers' and 'industries' lists.
        """
        result = {"tickers": [], "industries": []}
        
        try:
            text = f"{news_item.get('title', '')} {news_item.get('content', '')}"
            
            # Extract tickers from text
            existing_tickers = news_item.get("related_tickers", [])
            result["tickers"] = list(existing_tickers) if existing_tickers else []
            
            for pattern in self.TICKER_PATTERNS.values():
                matches = pattern.findall(text)
                for match in matches:
                    if match not in result["tickers"]:
                        result["tickers"].append(match)
            
            # Extract industries
            existing_industries = news_item.get("related_industries", [])
            result["industries"] = list(existing_industries) if existing_industries else []
            
            for industry, keywords in self.INDUSTRY_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    if industry not in result["industries"]:
                        result["industries"].append(industry)
            
            return result
        except Exception as e:
            print(f"Error extracting entities: {e}")
            return result
    
    def determine_sentiment(self, news_item: Dict[str, Any]) -> str:
        """Determine sentiment of a news item.
        
        Args:
            news_item: News item dictionary.
            
        Returns:
            Sentiment string: 'positive', 'negative', or 'neutral'.
        """
        try:
            text = f"{news_item.get('title', '')} {news_item.get('content', '')}"
            
            positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in text)
            negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in text)
            
            # Consider impact score as additional signal
            impact = news_item.get("impact_score", 0)
            if impact >= 4:
                # High impact events tend to be negative (crashes, defaults)
                negative_count += 1
            
            if positive_count > negative_count + 1:
                return "positive"
            elif negative_count > positive_count + 1:
                return "negative"
            else:
                return "neutral"
        except Exception:
            return "neutral"
