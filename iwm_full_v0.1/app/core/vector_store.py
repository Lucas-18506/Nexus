"""Qdrant vector store client wrapper."""

from typing import Any, Dict, List, Optional

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    PointIdsList,
    PointStruct,
    Range,
    VectorParams,
)

from app.core.config import settings

# Collection names for different document types
COLLECTIONS = [
    "industry_docs",
    "company_docs",
    "event_docs",
    "thesis_docs",
    "macro_docs",
]

DEFAULT_VECTOR_SIZE = 1536  # text-embedding-3-small
DEFAULT_DISTANCE = Distance.COSINE


class VectorStore:
    """Qdrant vector store client wrapper."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """Initialize Qdrant client."""
        self.client = QdrantClient(
            host=host or settings.qdrant_host,
            port=port or settings.qdrant_port,
            api_key=api_key or settings.qdrant_api_key,
        )

    def collection_exists(self, collection_name: str) -> bool:
        """Check if a collection exists in Qdrant."""
        collections = self.client.get_collections().collections
        return any(c.name == collection_name for c in collections)

    def create_collection(
        self,
        collection_name: str,
        vector_size: int = DEFAULT_VECTOR_SIZE,
        distance: Distance = DEFAULT_DISTANCE,
    ) -> None:
        """Create a new collection if it doesn't exist."""
        if not self.collection_exists(collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance,
                ),
            )

    def init_collections(self) -> None:
        """Initialize all default collections."""
        for collection in COLLECTIONS:
            self.create_collection(collection)

    def upsert_documents(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]],
    ) -> None:
        """Upsert documents into a collection.

        Args:
            collection_name: Target collection name.
            documents: List of dicts with keys:
                - id: str or int
                - vector: List[float]
                - payload: Dict[str, Any] (optional)
        """
        if not self.collection_exists(collection_name):
            self.create_collection(collection_name)

        points = []
        for doc in documents:
            point = PointStruct(
                id=doc["id"],
                vector=doc["vector"],
                payload=doc.get("payload", {}),
            )
            points.append(point)

        self.client.upsert(
            collection_name=collection_name,
            points=points,
        )

    def search_similar(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 5,
        score_threshold: Optional[float] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors in a collection.

        Args:
            collection_name: Target collection name.
            query_vector: Query embedding vector.
            limit: Maximum number of results.
            score_threshold: Minimum similarity score.
            filters: Optional metadata filters.

        Returns:
            List of result dicts with keys: id, score, payload.
        """
        search_filter = None
        if filters:
            must_conditions = []
            for key, value in filters.items():
                if isinstance(value, dict) and "range" in value:
                    must_conditions.append(
                        FieldCondition(
                            key=key,
                            range=Range(**value["range"]),
                        )
                    )
                else:
                    must_conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value),
                        )
                    )
            search_filter = Filter(must=must_conditions)

        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=search_filter,
        )

        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload,
            }
            for r in results
        ]

    def delete_document(
        self,
        collection_name: str,
        document_id: str,
    ) -> None:
        """Delete a document from a collection."""
        self.client.delete(
            collection_name=collection_name,
            points_selector=PointIdsList(points=[document_id]),
        )

    def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection."""
        return self.client.get_collection(collection_name).dict()


# Global vector store instance
vector_store = VectorStore()
