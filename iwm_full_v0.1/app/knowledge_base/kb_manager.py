"""Knowledge base manager - central coordinator for all KB operations."""

from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge_base.industry_kb import get_all_industries
from app.knowledge_base.company_kb import get_all_companies


class KnowledgeBaseManager:
    """Central manager for knowledge base operations.
    
    Coordinates between database storage, vector store, and preset data.
    Provides unified interface for industry, company, and thesis management.
    """
    
    def __init__(self, db_session: AsyncSession, vector_store: Optional[Any] = None) -> None:
        """Initialize the knowledge base manager.
        
        Args:
            db_session: SQLAlchemy async database session.
            vector_store: Optional vector store for semantic search.
        """
        self._db = db_session
        self._vector_store = vector_store
    
    # ─── Industry Operations ──────────────────────────────────────
    
    async def upsert_industry(self, data: Dict[str, Any]) -> int:
        """Update or create an industry record."""
        from app.models.industry import Industry
        try:
            name = data["name"]
            result = await self._db.execute(
                select(Industry).where(Industry.name == name)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                for field in ["description", "lifecycle_stage", "key_drivers",
                              "supply_chain", "bottleneck", "risk_factors", "opportunities"]:
                    if field in data:
                        setattr(existing, field, data[field])
                existing.updated_at = datetime.utcnow()
                await self._db.flush()
                return existing.id
            else:
                industry = Industry(
                    name=name,
                    description=data.get("description"),
                    lifecycle_stage=data.get("lifecycle_stage"),
                    key_drivers=data.get("key_drivers"),
                    supply_chain=data.get("supply_chain"),
                    bottleneck=data.get("bottleneck"),
                    risk_factors=data.get("risk_factors"),
                    opportunities=data.get("opportunities"),
                )
                self._db.add(industry)
                await self._db.flush()
                return industry.id
        except Exception as e:
            print(f"Error upserting industry: {e}")
            await self._db.rollback()
            raise
    
    async def search(
        self,
        query: str,
        kb_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search the knowledge base."""
        results: List[Dict[str, Any]] = []
        
        try:
            if kb_type is None or kb_type == "industry":
                from app.models.industry import Industry
                result = await self._db.execute(
                    select(Industry).where(
                        Industry.name.ilike(f"%{query}%") |
                        Industry.description.ilike(f"%{query}%")
                    ).limit(limit)
                )
                for row in result.scalars().all():
                    results.append({
                        "type": "industry",
                        "id": row.id,
                        "name": row.name,
                        "description": row.description,
                        "lifecycle_stage": row.lifecycle_stage,
                    })
            
            if kb_type is None or kb_type == "company":
                from app.models.company import Company
                result = await self._db.execute(
                    select(Company).where(
                        Company.name.ilike(f"%{query}%") |
                        Company.ticker.ilike(f"%{query}%") |
                        Company.description.ilike(f"%{query}%")
                    ).limit(limit)
                )
                for row in result.scalars().all():
                    results.append({
                        "type": "company",
                        "id": row.id,
                        "name": row.name,
                        "ticker": row.ticker,
                        "market": row.market,
                        "description": row.description,
                    })
            
            if kb_type is None or kb_type == "thesis":
                from app.models.thesis import Thesis
                result = await self._db.execute(
                    select(Thesis).where(
                        Thesis.title.ilike(f"%{query}%") |
                        Thesis.description.ilike(f"%{query}%")
                    ).limit(limit)
                )
                for row in result.scalars().all():
                    results.append({
                        "type": "thesis",
                        "id": row.id,
                        "title": row.title,
                        "description": row.description,
                        "confidence": float(row.confidence) if row.confidence is not None else None,
                    })
        except Exception as e:
            print(f"Error searching knowledge base: {e}")
        
        return results[:limit]
    
    async def get_industry_detail(self, industry_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about an industry."""
        from app.models.industry import Industry
        try:
            result = await self._db.execute(
                select(Industry).where(Industry.id == industry_id)
            )
            row = result.scalar_one_or_none()
            if row:
                return {
                    "id": row.id,
                    "name": row.name,
                    "description": row.description,
                    "lifecycle_stage": row.lifecycle_stage,
                    "key_drivers": row.key_drivers,
                    "supply_chain": row.supply_chain,
                    "bottleneck": row.bottleneck,
                    "risk_factors": row.risk_factors,
                    "opportunities": row.opportunities,
                }
        except Exception as e:
            print(f"Error getting industry detail: {e}")
        return None
    
    async def get_company_detail(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Get detailed information about a company."""
        from app.models.industry import Industry
        from app.models.company import Company
        try:
            result = await self._db.execute(
                select(Company).where(Company.id == company_id)
            )
            row = result.scalar_one_or_none()
            if row:
                industry_name = None
                if row.industry_id:
                    ind_result = await self._db.execute(
                        select(Industry.name).where(Industry.id == row.industry_id)
                    )
                    industry_name = ind_result.scalar_one_or_none()
                
                return {
                    "id": row.id,
                    "ticker": row.ticker,
                    "market": row.market,
                    "name": row.name,
                    "industry": industry_name,
                    "description": row.description,
                    "business_model": row.business_model,
                    "moat": row.moat,
                    "risk_points": row.risk_points,
                }
        except Exception as e:
            print(f"Error getting company detail: {e}")
        return None
    
    async def get_industry_list(self) -> List[Dict[str, Any]]:
        """Get list of all industries."""
        from app.models.industry import Industry
        try:
            result = await self._db.execute(
                select(Industry).order_by(Industry.name)
            )
            return [
                {
                    "id": row.id,
                    "name": row.name,
                    "lifecycle_stage": row.lifecycle_stage,
                    "description": row.description,
                }
                for row in result.scalars().all()
            ]
        except Exception as e:
            print(f"Error getting industry list: {e}")
            return []
    
    async def get_company_list(
        self,
        industry_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get list of companies, optionally filtered by industry."""
        from app.models.company import Company
        try:
            query = select(Company).order_by(Company.name)
            if industry_id:
                query = query.where(Company.industry_id == industry_id)
            
            result = await self._db.execute(query)
            return [
                {
                    "id": row.id,
                    "ticker": row.ticker,
                    "market": row.market,
                    "name": row.name,
                    "industry_id": row.industry_id,
                }
                for row in result.scalars().all()
            ]
        except Exception as e:
            print(f"Error getting company list: {e}")
            return []
    
    # ─── Company Operations ───────────────────────────────────────
    
    async def upsert_company(self, data: Dict[str, Any]) -> int:
        """Update or create a company record."""
        from app.models.industry import Industry
        from app.models.company import Company
        try:
            ticker = data["ticker"]
            market = data["market"]
            
            result = await self._db.execute(
                select(Company).where(
                    Company.ticker == ticker,
                    Company.market == market,
                )
            )
            existing = result.scalar_one_or_none()
            
            industry_id = None
            if "industry_name" in data:
                ind_result = await self._db.execute(
                    select(Industry.id).where(Industry.name == data["industry_name"])
                )
                industry_id = ind_result.scalar_one_or_none()
            
            if existing:
                for field in ["name", "description", "business_model", "moat", "risk_points"]:
                    if field in data:
                        setattr(existing, field, data[field])
                if industry_id:
                    existing.industry_id = industry_id
                existing.updated_at = datetime.utcnow()
                await self._db.flush()
                return existing.id
            else:
                company = Company(
                    ticker=ticker,
                    market=market,
                    name=data.get("name", ticker),
                    industry_id=industry_id,
                    description=data.get("description"),
                    business_model=data.get("business_model"),
                    moat=data.get("moat"),
                    risk_points=data.get("risk_points"),
                )
                self._db.add(company)
                await self._db.flush()
                return company.id
        except Exception as e:
            print(f"Error upserting company: {e}")
            await self._db.rollback()
            raise
    
    # ─── Thesis Operations ────────────────────────────────────────
    
    async def upsert_thesis(self, data: Dict[str, Any]) -> int:
        """Update or create a thesis record."""
        from app.models.thesis import Thesis
        try:
            thesis_id = data.get("id")
            if thesis_id:
                result = await self._db.execute(
                    select(Thesis).where(Thesis.id == thesis_id)
                )
                existing = result.scalar_one_or_none()
                if existing:
                    for field in ["title", "description", "confidence",
                                  "related_industry", "related_tickers", "status"]:
                        if field in data:
                            setattr(existing, field, data[field])
                    existing.updated_at = datetime.utcnow()
                    await self._db.flush()
                    return existing.id
            
            thesis = Thesis(
                title=data["title"],
                description=data.get("description", ""),
                confidence=data.get("confidence", 0.5),
                related_industry=data.get("related_industry"),
                related_tickers=data.get("related_tickers", []),
                status=data.get("status", "active"),
            )
            self._db.add(thesis)
            await self._db.flush()
            return thesis.id
        except Exception as e:
            print(f"Error upserting thesis: {e}")
            await self._db.rollback()
            raise
    
    # ─── Preset Data Initialization ──────────────────────────────
    
    async def initialize_preset_data(self) -> Dict[str, int]:
        """Initialize knowledge base with preset industry and company data."""
        industry_count = 0
        company_count = 0
        
        try:
            for industry_data in get_all_industries():
                try:
                    await self.upsert_industry(industry_data)
                    industry_count += 1
                except Exception as ie:
                    print(f"Error importing industry {industry_data['name']}: {ie}")
            
            for company_data in get_all_companies():
                try:
                    await self.upsert_company(company_data)
                    company_count += 1
                except Exception as ce:
                    print(f"Error importing company {company_data['ticker']}: {ce}")
            
            await self._db.commit()
            
        except Exception as e:
            print(f"Error initializing preset data: {e}")
            await self._db.rollback()
        
        return {
            "industries": industry_count,
            "companies": company_count,
        }
