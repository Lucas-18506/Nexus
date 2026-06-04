"""Knowledge base database models."""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Industry(Base):
    """Industry knowledge base model."""
    
    __tablename__ = "industries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    lifecycle_stage = Column(String(20), nullable=True)  # emerging, growth, expansion, mature, decline
    key_drivers = Column(JSON, nullable=True, default=list)
    supply_chain = Column(Text, nullable=True)
    bottleneck = Column(Text, nullable=True)
    risk_factors = Column(JSON, nullable=True, default=list)
    opportunities = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    companies = relationship("Company", back_populates="industry")


class Company(Base):
    """Company knowledge base model."""
    
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), nullable=False, index=True)
    market = Column(String(10), nullable=False, index=True)  # US, HK, CN
    name = Column(String(100), nullable=False)
    industry_id = Column(Integer, ForeignKey("industries.id"), nullable=True)
    description = Column(Text, nullable=True)
    business_model = Column(Text, nullable=True)
    moat = Column(Text, nullable=True)
    risk_points = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    industry = relationship("Industry", back_populates="companies")


class Thesis(Base):
    """Investment thesis model."""
    
    __tablename__ = "theses"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)  # 0.0 - 1.0
    related_industry = Column(String(50), nullable=True)
    related_tickers = Column(JSON, nullable=True, default=list)
    status = Column(String(20), default="active")  # active, confirmed, invalidated, pending
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    evidences = relationship("ThesisEvidence", back_populates="thesis", cascade="all, delete-orphan")


class ThesisEvidence(Base):
    """Evidence supporting or refuting a thesis."""
    
    __tablename__ = "thesis_evidences"
    
    id = Column(Integer, primary_key=True, index=True)
    thesis_id = Column(Integer, ForeignKey("theses.id"), nullable=False)
    evidence_type = Column(String(20), nullable=False)  # supporting, refuting, neutral
    content = Column(Text, nullable=False)
    source = Column(String(200), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    thesis = relationship("Thesis", back_populates="evidences")


class Report(Base):
    """Generated report model."""
    
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(30), nullable=False, index=True)  # daily, opportunity, industry
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)
    data_snapshot = Column(JSON, nullable=True, default=dict)
    industry_id = Column(Integer, ForeignKey("industries.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
