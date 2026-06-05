"""Stock-related database models."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, BigInteger
from sqlalchemy.sql import func
from app.core.database import Base


class StockPrice(Base):
    """Daily stock price data (OHLCV)."""
    
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    market = Column(String(10), nullable=False, index=True)  # US, HK, CN
    trade_date = Column(Date, nullable=False, index=True)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    adj_close = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class StockFundamental(Base):
    """Stock fundamental data."""
    
    __tablename__ = "stock_fundamentals"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    market = Column(String(10), nullable=False, index=True)
    pe_ttm = Column(Float, nullable=True)
    pb = Column(Float, nullable=True)
    ps_ttm = Column(Float, nullable=True)
    market_cap = Column(Float, nullable=True)  # in billions
    revenue_ttm = Column(Float, nullable=True)
    profit_margin = Column(Float, nullable=True)
    roe = Column(Float, nullable=True)
    debt_to_equity = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())


class StockQuote(Base):
    """Real-time stock quote snapshot."""
    
    __tablename__ = "stock_quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    market = Column(String(10), nullable=False, index=True)
    price = Column(Float, nullable=False)
    change = Column(Float, nullable=True)
    change_percent = Column(Float, nullable=True)
    volume = Column(BigInteger, nullable=True)
    day_high = Column(Float, nullable=True)
    day_low = Column(Float, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now())
