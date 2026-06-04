"""Knowledge base service - simplified interface for KB operations."""

from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.knowledge_base.kb_manager import KnowledgeBaseManager


class KnowledgeBaseService:
    """Simplified service layer for knowledge base operations.
    
    Wraps KnowledgeBaseManager to provide a clean API for
    industry, company, and thesis operations.
    """
    
    def __init__(self, db_session: AsyncSession, vector_store: Optional[Any] = None) -> None:
        """Initialize the KB service.
        
        Args:
            db_session: SQLAlchemy async session.
            vector_store: Optional vector store.
        """
        self._manager = KnowledgeBaseManager(db_session, vector_store)
    
    # ─── Industry API ─────────────────────────────────────────────
    
    async def get_industries(self) -> List[Dict[str, Any]]:
        """Get all industries.
        
        Returns:
            List of industry dictionaries.
        """
        return await self._manager.get_industry_list()
    
    async def get_industry(self, industry_id: int) -> Optional[Dict[str, Any]]:
        """Get industry details.
        
        Args:
            industry_id: Industry ID.
            
        Returns:
            Industry detail dictionary or None.
        """
        return await self._manager.get_industry_detail(industry_id)
    
    async def save_industry(self, data: Dict[str, Any]) -> int:
        """Save (create or update) an industry.
        
        Args:
            data: Industry data.
            
        Returns:
            Industry ID.
        """
        return await self._manager.upsert_industry(data)
    
    # ─── Company API ──────────────────────────────────────────────
    
    async def get_companies(
        self,
        industry_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get companies, optionally filtered by industry.
        
        Args:
            industry_id: Optional industry filter.
            
        Returns:
            List of company dictionaries.
        """
        return await self._manager.get_company_list(industry_id)
    
    async def get_company(self, company_id: int) -> Optional[Dict[str, Any]]:
        """Get company details.
        
        Args:
            company_id: Company ID.
            
        Returns:
            Company detail dictionary or None.
        """
        return await self._manager.get_company_detail(company_id)
    
    async def save_company(self, data: Dict[str, Any]) -> int:
        """Save (create or update) a company.
        
        Args:
            data: Company data.
            
        Returns:
            Company ID.
        """
        return await self._manager.upsert_company(data)
    
    # ─── Search ───────────────────────────────────────────────────
    
    async def search(
        self,
        query: str,
        kb_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Search the knowledge base.
        
        Args:
            query: Search query.
            kb_type: Optional type filter.
            limit: Max results.
            
        Returns:
            List of matching items.
        """
        return await self._manager.search(query, kb_type, limit)
    
    # ─── Initialization ──────────────────────────────────────────
    
    async def initialize(self) -> Dict[str, int]:
        """Initialize preset data.
        
        Returns:
            Counts of imported records.
        """
        return await self._manager.initialize_preset_data()
