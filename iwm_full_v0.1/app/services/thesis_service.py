"""Thesis service for CRUD and evidence management."""

from datetime import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import select, desc, update
from sqlalchemy.ext.asyncio import AsyncSession


class ThesisService:
    """Service for thesis CRUD operations and evidence management."""
    
    def __init__(self, db_session: AsyncSession) -> None:
        self._db = db_session
    
    async def create_thesis(
        self, title: str, description: str = "", confidence: float = 0.5,
        related_industry: str = "", related_tickers: Optional[List[str]] = None,
    ) -> int:
        from app.models.thesis import Thesis
        try:
            thesis = Thesis(
                title=title, description=description,
                confidence=max(0.0, min(1.0, confidence)),
                related_industry=related_industry,
                related_tickers=related_tickers or [], status="active",
            )
            self._db.add(thesis)
            await self._db.flush()
            thesis_id = thesis.id
            await self._db.commit()
            return thesis_id
        except Exception as e:
            await self._db.rollback()
            print(f"Error creating thesis: {e}")
            raise
    
    async def get_thesis(self, thesis_id: int) -> Optional[Dict[str, Any]]:
        from app.models.thesis import Thesis, ThesisEvidence
        try:
            result = await self._db.execute(select(Thesis).where(Thesis.id == thesis_id))
            thesis = result.scalar_one_or_none()
            if not thesis:
                return None
            
            evidence_result = await self._db.execute(
                select(ThesisEvidence).where(ThesisEvidence.thesis_id == thesis_id)
                .order_by(desc(ThesisEvidence.created_at))
            )
            evidences = evidence_result.scalars().all()
            
            return {
                "id": thesis.id, "title": thesis.title, "description": thesis.description,
                "confidence": float(thesis.confidence) if thesis.confidence is not None else None,
                "related_industry": thesis.related_industry,
                "related_tickers": thesis.related_tickers,
                "status": thesis.status,
                "created_at": thesis.created_at.isoformat() if thesis.created_at else None,
                "updated_at": thesis.updated_at.isoformat() if thesis.updated_at else None,
                "evidences": [
                    {"id": ev.id, "evidence_type": ev.evidence_type, "content": ev.content,
                     "source": ev.source, "confidence": float(ev.confidence) if ev.confidence is not None else None,
                     "created_at": ev.created_at.isoformat() if ev.created_at else None}
                    for ev in evidences
                ],
            }
        except Exception as e:
            print(f"Error getting thesis {thesis_id}: {e}")
            return None
    
    async def update_thesis(self, thesis_id: int, **updates: Any) -> bool:
        from app.models.thesis import Thesis
        try:
            allowed = {"title", "description", "confidence", "related_industry", "related_tickers", "status"}
            update_data = {k: v for k, v in updates.items() if k in allowed}
            if update_data:
                update_data["updated_at"] = datetime.utcnow()
                await self._db.execute(update(Thesis).where(Thesis.id == thesis_id).values(**update_data))
                await self._db.commit()
            return True
        except Exception as e:
            await self._db.rollback()
            print(f"Error updating thesis {thesis_id}: {e}")
            return False
    
    async def delete_thesis(self, thesis_id: int) -> bool:
        from app.models.thesis import Thesis
        try:
            result = await self._db.execute(select(Thesis).where(Thesis.id == thesis_id))
            thesis = result.scalar_one_or_none()
            if thesis:
                await self._db.delete(thesis)
                await self._db.commit()
                return True
            return False
        except Exception as e:
            await self._db.rollback()
            print(f"Error deleting thesis {thesis_id}: {e}")
            return False
    
    async def list_theses(self, status: Optional[str] = None, industry: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        from sqlalchemy import and_
        from app.models.thesis import Thesis
        try:
            query = select(Thesis).order_by(desc(Thesis.created_at))
            conditions = []
            if status:
                conditions.append(Thesis.status == status)
            if industry:
                conditions.append(Thesis.related_industry == industry)
            if conditions:
                query = query.where(and_(*conditions))
            query = query.limit(limit)
            result = await self._db.execute(query)
            return [
                {"id": row.id, "title": row.title,
                 "confidence": float(row.confidence) if row.confidence is not None else None,
                 "related_industry": row.related_industry, "related_tickers": row.related_tickers,
                 "status": row.status, "created_at": row.created_at.isoformat() if row.created_at else None}
                for row in result.scalars().all()
            ]
        except Exception as e:
            print(f"Error listing theses: {e}")
            return []
    
    async def add_evidence(self, thesis_id: int, evidence_type: str, content: str,
                           source: str = "", confidence: float = 0.5) -> int:
        from app.models.thesis import Thesis, ThesisEvidence
        try:
            evidence = ThesisEvidence(
                thesis_id=thesis_id, evidence_type=evidence_type,
                content=content, source=source, confidence=confidence,
            )
            self._db.add(evidence)
            await self._db.execute(
                update(Thesis).where(Thesis.id == thesis_id).values(updated_at=datetime.utcnow())
            )
            await self._db.flush()
            evidence_id = evidence.id
            await self._db.commit()
            return evidence_id
        except Exception as e:
            await self._db.rollback()
            print(f"Error adding evidence: {e}")
            raise
    
    async def get_evidence(self, evidence_id: int) -> Optional[Dict[str, Any]]:
        from app.models.thesis import ThesisEvidence
        try:
            result = await self._db.execute(select(ThesisEvidence).where(ThesisEvidence.id == evidence_id))
            row = result.scalar_one_or_none()
            if row:
                return {"id": row.id, "thesis_id": row.thesis_id, "evidence_type": row.evidence_type,
                        "content": row.content, "source": row.source,
                        "confidence": float(row.confidence) if row.confidence is not None else None,
                        "created_at": row.created_at.isoformat() if row.created_at else None}
        except Exception as e:
            print(f"Error getting evidence {evidence_id}: {e}")
        return None
    
    async def delete_evidence(self, evidence_id: int) -> bool:
        from app.models.thesis import ThesisEvidence
        try:
            result = await self._db.execute(select(ThesisEvidence).where(ThesisEvidence.id == evidence_id))
            evidence = result.scalar_one_or_none()
            if evidence:
                await self._db.delete(evidence)
                await self._db.commit()
                return True
            return False
        except Exception as e:
            await self._db.rollback()
            print(f"Error deleting evidence {evidence_id}: {e}")
            return False
