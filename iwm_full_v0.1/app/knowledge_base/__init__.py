"""Knowledge base module.

Provides centralized knowledge management for industries, companies,
and investment theses with database persistence and vector search.
"""

from app.knowledge_base.kb_manager import KnowledgeBaseManager
from app.knowledge_base.industry_kb import (
    PRESET_INDUSTRIES,
    get_industry_data,
    get_all_industries,
)
from app.knowledge_base.company_kb import (
    PRESET_COMPANIES,
    get_company_data,
    get_all_companies,
    get_companies_by_industry,
)
from app.knowledge_base.thesis_kb import ThesisKnowledgeBase

__all__ = [
    "KnowledgeBaseManager",
    "ThesisKnowledgeBase",
    "PRESET_INDUSTRIES",
    "PRESET_COMPANIES",
    "get_industry_data",
    "get_all_industries",
    "get_company_data",
    "get_all_companies",
    "get_companies_by_industry",
]
