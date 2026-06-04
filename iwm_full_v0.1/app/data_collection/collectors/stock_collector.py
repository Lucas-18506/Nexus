"""Stock data collector."""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.data_collection.collectors.base import BaseCollector


class StockCollector(BaseCollector):
    """Collector for stock market data.
    
    Supports markets: US (NYSE/NASDAQ), HK (Hong Kong), CN (A-shares).
    Provides historical prices, fundamentals, and real-time quotes.
    """
    
    # Market-specific configuration
    MARKET_CONFIG: Dict[str, Dict[str, Any]] = {
        "US": {"currency": "USD", "exchange": "NYSE/NASDAQ", "trading_hours": "9:30-16:00 EST"},
        "HK": {"currency": "HKD", "exchange": "HKEX", "trading_hours": "9:30-16:00 HKT"},
        "CN": {"currency": "CNY", "exchange": "SSE/SZSE", "trading_hours": "9:30-15:00 CST"},
    }
    
    # Simulated fundamental data templates by sector
    FUNDAMENTAL_TEMPLATES: Dict[str, Dict[str, Any]] = {
        "technology": {"pe_ttm": 35.0, "pb": 8.0, "ps_ttm": 10.0, "profit_margin": 0.25, "roe": 0.30, "debt_to_equity": 0.5},
        "semiconductor": {"pe_ttm": 45.0, "pb": 12.0, "ps_ttm": 15.0, "profit_margin": 0.20, "roe": 0.25, "debt_to_equity": 0.4},
        "automotive": {"pe_ttm": 25.0, "pb": 3.0, "ps_ttm": 2.0, "profit_margin": 0.10, "roe": 0.15, "debt_to_equity": 1.0},
        "consumer_electronics": {"pe_ttm": 28.0, "pb": 35.0, "ps_ttm": 7.0, "profit_margin": 0.22, "roe": 0.80, "debt_to_equity": 2.0},
        "financial": {"pe_ttm": 15.0, "pb": 1.5, "ps_ttm": 3.0, "profit_margin": 0.30, "roe": 0.12, "debt_to_equity": 5.0},
        "energy": {"pe_ttm": 18.0, "pb": 2.0, "ps_ttm": 2.5, "profit_margin": 0.12, "roe": 0.10, "debt_to_equity": 0.8},
        "crypto": {"pe_ttm": 30.0, "pb": 5.0, "ps_ttm": 8.0, "profit_margin": 0.40, "roe": 0.15, "debt_to_equity": 0.3},
        "gaming": {"pe_ttm": 22.0, "pb": 4.0, "ps_ttm": 5.0, "profit_margin": 0.28, "roe": 0.18, "debt_to_equity": 0.4},
        "ecommerce": {"pe_ttm": 20.0, "pb": 2.5, "ps_ttm": 3.0, "profit_margin": 0.15, "roe": 0.12, "debt_to_equity": 0.6},
    }
    
    def __init__(self) -> None:
        self._price_cache: Dict[str, List[Dict[str, Any]]] = {}
    
    def get_name(self) -> str:
        return "Stock Data Collector"
    
    @property
    def data_type(self) -> str:
        return "stock_data"
    
    async def collect(self, **kwargs) -> List[Dict[str, Any]]:
        """Collect stock data for specified tickers."""
        tickers = kwargs.get("tickers", [])
        market = kwargs.get("market", "US")
        results = []
        for ticker in tickers:
            try:
                quote = await self.get_stock_quote(ticker, market)
                results.append(quote)
            except Exception as e:
                print(f"Error collecting {ticker}: {e}")
        return results
    
    async def get_stock_history(
        self,
        ticker: str,
        market: str,
        period: str = "1y"
    ) -> List[Dict[str, Any]]:
        """Get historical OHLCV data for a stock.
        
        Args:
            ticker: Stock ticker symbol.
            market: Market code (US, HK, CN).
            period: Time period (1m, 3m, 6m, 1y, 2y, 5y).
            
        Returns:
            List of daily OHLCV records.
        """
        try:
            period_days = self._parse_period(period)
            return self._generate_ohlcv(ticker, market, period_days)
        except Exception as e:
            print(f"Error getting history for {ticker}: {e}")
            return self._generate_ohlcv(ticker, market, 252)
    
    async def get_stock_fundamentals(self, ticker: str, market: str) -> Dict[str, Any]:
        """Get fundamental data for a stock.
        
        Args:
            ticker: Stock ticker symbol.
            market: Market code (US, HK, CN).
            
        Returns:
            Dictionary with PE, PB, PS, and other fundamentals.
        """
        try:
            return self._generate_fundamentals(ticker, market)
        except Exception as e:
            print(f"Error getting fundamentals for {ticker}: {e}")
            return self._generate_fundamentals(ticker, market)
    
    async def get_stock_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        """Get real-time quote for a stock.
        
        Args:
            ticker: Stock ticker symbol.
            market: Market code (US, HK, CN).
            
        Returns:
            Dictionary with price, change, volume, etc.
        """
        try:
            return self._generate_quote(ticker, market)
        except Exception as e:
            print(f"Error getting quote for {ticker}: {e}")
            return self._generate_quote(ticker, market)
    
    def _parse_period(self, period: str) -> int:
        """Convert period string to number of trading days."""
        period_map = {
            "1m": 21,
            "3m": 63,
            "6m": 126,
            "1y": 252,
            "2y": 504,
            "5y": 1260,
        }
        return period_map.get(period, 252)
    
    def _generate_ohlcv(self, ticker: str, market: str, days: int) -> List[Dict[str, Any]]:
        """Generate simulated OHLCV data."""
        random.seed(hash(f"{ticker}_{market}"))
        
        # Base price varies by ticker for differentiation
        base_price = 50.0 + (hash(ticker) % 200)
        if market == "HK":
            base_price *= 5  # HK stocks tend to have higher nominal prices
        elif market == "CN":
            base_price *= 0.5  # A-shares tend to have lower nominal prices
        
        volatility = 0.02  # 2% daily volatility
        
        results: List[Dict[str, Any]] = []
        current_price = base_price
        
        end_date = datetime.now()
        for i in range(days):
            trade_date = end_date - timedelta(days=i)
            # Skip weekends
            if trade_date.weekday() >= 5:
                continue
            
            # Random walk
            daily_return = random.gauss(0.0005, volatility)
            open_price = current_price * (1 + random.gauss(0, 0.005))
            close_price = current_price * (1 + daily_return)
            high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, 0.005)))
            low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, 0.005)))
            volume = int(random.uniform(1e6, 50e6))
            
            results.append({
                "ticker": ticker,
                "market": market,
                "trade_date": trade_date.strftime("%Y-%m-%d"),
                "open_price": round(open_price, 2),
                "high_price": round(high_price, 2),
                "low_price": round(low_price, 2),
                "close_price": round(close_price, 2),
                "volume": volume,
                "adj_close": round(close_price, 2),
            })
            
            current_price = close_price
        
        random.seed()  # Reset seed
        return list(reversed(results))
    
    def _detect_sector(self, ticker: str) -> str:
        """Detect sector based on ticker for differentiated fundamentals."""
        sector_map = {
            "NVDA": "semiconductor", "AMD": "semiconductor",
            "TSLA": "automotive", "1211": "automotive", "比亚迪": "automotive",
            "AAPL": "consumer_electronics",
            "MSFT": "technology",
            "COIN": "crypto",
            "0700": "gaming", "腾讯": "gaming",
            "9988": "ecommerce", "阿里": "ecommerce",
            "宁德时代": "automotive",
        }
        return sector_map.get(ticker, "technology")
    
    def _generate_fundamentals(self, ticker: str, market: str) -> Dict[str, Any]:
        """Generate simulated fundamental data."""
        sector = self._detect_sector(ticker)
        template = self.FUNDAMENTAL_TEMPLATES.get(sector, self.FUNDAMENTAL_TEMPLATES["technology"])
        
        random.seed(hash(f"{ticker}_{market}_fund"))
        
        market_cap = round(random.uniform(50, 3000), 1)  # in billions
        revenue_ttm = round(market_cap / random.uniform(3, 10), 1)
        
        result = {
            "ticker": ticker,
            "market": market,
            "pe_ttm": round(template["pe_ttm"] * random.uniform(0.8, 1.2), 1),
            "pb": round(template["pb"] * random.uniform(0.8, 1.2), 1),
            "ps_ttm": round(template["ps_ttm"] * random.uniform(0.8, 1.2), 1),
            "market_cap": market_cap,
            "revenue_ttm": revenue_ttm,
            "profit_margin": round(template["profit_margin"] * random.uniform(0.8, 1.2), 3),
            "roe": round(template["roe"] * random.uniform(0.8, 1.2), 3),
            "debt_to_equity": round(template["debt_to_equity"] * random.uniform(0.8, 1.2), 1),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        random.seed()
        return result
    
    def _generate_quote(self, ticker: str, market: str) -> Dict[str, Any]:
        """Generate simulated real-time quote."""
        random.seed(hash(f"{ticker}_{market}_quote") + int(datetime.now().timestamp()) // 60)
        
        base_price = 50.0 + (hash(ticker) % 200)
        if market == "HK":
            base_price *= 5
        elif market == "CN":
            base_price *= 0.5
        
        price = round(base_price * random.uniform(0.98, 1.02), 2)
        change = round(price - base_price, 2)
        change_percent = round(change / base_price * 100, 2)
        
        result = {
            "ticker": ticker,
            "market": market,
            "price": price,
            "change": change,
            "change_percent": change_percent,
            "volume": int(random.uniform(1e6, 50e6)),
            "day_high": round(price * 1.02, 2),
            "day_low": round(price * 0.98, 2),
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        random.seed()
        return result
