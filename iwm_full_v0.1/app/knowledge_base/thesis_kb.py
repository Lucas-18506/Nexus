"""Thesis knowledge base for investment thesis management."""

from datetime import datetime
from typing import Dict, Any, List, Optional


class ThesisKnowledgeBase:
    """In-memory knowledge base for managing investment theses and evidence.
    
    Provides CRUD operations for theses and evidence tracking.
    In production, this would be backed by a database.
    """
    
    def __init__(self) -> None:
        self._theses: Dict[int, Dict[str, Any]] = {}
        self._evidences: Dict[int, List[Dict[str, Any]]] = {}
        self._next_thesis_id: int = 1
        self._next_evidence_id: int = 1
    
    def create_thesis(
        self,
        title: str,
        description: str,
        confidence: float,
        related_industry: str,
        related_tickers: List[str],
    ) -> int:
        """Create a new investment thesis.
        
        Args:
            title: Thesis title.
            description: Detailed description of the thesis.
            confidence: Confidence level (0.0 - 1.0).
            related_industry: Related industry name.
            related_tickers: List of related ticker symbols.
            
        Returns:
            ID of the created thesis.
        """
        thesis_id = self._next_thesis_id
        self._next_thesis_id += 1
        
        self._theses[thesis_id] = {
            "id": thesis_id,
            "title": title,
            "description": description,
            "confidence": max(0.0, min(1.0, confidence)),
            "related_industry": related_industry,
            "related_tickers": list(related_tickers),
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        self._evidences[thesis_id] = []
        return thesis_id
    
    def add_evidence(
        self,
        thesis_id: int,
        evidence_type: str,
        content: str,
        source: str,
    ) -> int:
        """Add evidence to a thesis.
        
        Args:
            thesis_id: ID of the thesis to add evidence to.
            evidence_type: Type of evidence (supporting/refuting/neutral).
            content: Evidence content/description.
            source: Source of the evidence.
            
        Returns:
            ID of the created evidence.
            
        Raises:
            KeyError: If thesis_id does not exist.
        """
        if thesis_id not in self._theses:
            raise KeyError(f"Thesis with ID {thesis_id} not found")
        
        evidence_id = self._next_evidence_id
        self._next_evidence_id += 1
        
        evidence = {
            "id": evidence_id,
            "thesis_id": thesis_id,
            "evidence_type": evidence_type,
            "content": content,
            "source": source,
            "created_at": datetime.utcnow().isoformat(),
        }
        
        self._evidences[thesis_id].append(evidence)
        self._theses[thesis_id]["updated_at"] = datetime.utcnow().isoformat()
        return evidence_id
    
    def get_thesis_with_evidence(self, thesis_id: int) -> Dict[str, Any]:
        """Get a thesis with all its associated evidence.
        
        Args:
            thesis_id: ID of the thesis.
            
        Returns:
            Dictionary containing thesis data and evidence list.
            
        Raises:
            KeyError: If thesis_id does not exist.
        """
        if thesis_id not in self._theses:
            raise KeyError(f"Thesis with ID {thesis_id} not found")
        
        thesis = dict(self._theses[thesis_id])
        thesis["evidences"] = list(self._evidences.get(thesis_id, []))
        return thesis
    
    def update_thesis_status(self, thesis_id: int, status: str) -> bool:
        """Update the status of a thesis.
        
        Args:
            thesis_id: ID of the thesis.
            status: New status (active/confirmed/invalidated/pending).
            
        Returns:
            True if successful, False if thesis not found.
        """
        if thesis_id not in self._theses:
            return False
        
        valid_statuses = ["active", "confirmed", "invalidated", "pending"]
        if status not in valid_statuses:
            raise ValueError(f"Invalid status: {status}. Must be one of {valid_statuses}")
        
        self._theses[thesis_id]["status"] = status
        self._theses[thesis_id]["updated_at"] = datetime.utcnow().isoformat()
        return True
    
    def get_all_theses(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all theses, optionally filtered by status.
        
        Args:
            status: Optional status filter.
            
        Returns:
            List of thesis dictionaries.
        """
        theses = list(self._theses.values())
        if status:
            theses = [t for t in theses if t["status"] == status]
        return sorted(theses, key=lambda x: x["created_at"], reverse=True)
    
    def update_thesis(
        self,
        thesis_id: int,
        **updates: Any,
    ) -> bool:
        """Update thesis fields.
        
        Args:
            thesis_id: ID of the thesis.
            **updates: Fields to update.
            
        Returns:
            True if successful, False if thesis not found.
        """
        if thesis_id not in self._theses:
            return False
        
        allowed_fields = ["title", "description", "confidence", "related_industry", "related_tickers"]
        for field, value in updates.items():
            if field in allowed_fields:
                self._theses[thesis_id][field] = value
        
        self._theses[thesis_id]["updated_at"] = datetime.utcnow().isoformat()
        return True
    
    def delete_thesis(self, thesis_id: int) -> bool:
        """Delete a thesis and all its evidence.
        
        Args:
            thesis_id: ID of the thesis to delete.
            
        Returns:
            True if deleted, False if not found.
        """
        if thesis_id not in self._theses:
            return False
        
        del self._theses[thesis_id]
        del self._evidences[thesis_id]
        return True
    
    def get_theses_by_industry(self, industry: str) -> List[Dict[str, Any]]:
        """Get all theses related to a specific industry.
        
        Args:
            industry: Industry name.
            
        Returns:
            List of matching thesis dictionaries.
        """
        return [
            t for t in self._theses.values()
            if t["related_industry"] == industry
        ]
    
    def get_theses_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """Get all theses related to a specific ticker.
        
        Args:
            ticker: Ticker symbol.
            
        Returns:
            List of matching thesis dictionaries.
        """
        return [
            t for t in self._theses.values()
            if ticker in t.get("related_tickers", [])
        ]
