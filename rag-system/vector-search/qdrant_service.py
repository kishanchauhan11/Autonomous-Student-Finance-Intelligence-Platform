# qdrant_service.py - Manage connection to Qdrant vector database
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Any

class QdrantService:
    def __init__(self, collection_name: str = "university_finance", vector_dim: int = 2048):
        self.client = QdrantClient(":memory:")
        self.collection_name = collection_name
        self.vector_dim = vector_dim
        self.ensure_collection()

    def ensure_collection(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_dim, distance=Distance.COSINE)
            )

    def upsert_points(self, points: List[PointStruct]):
        self.client.upsert(
            collection_name=self.collection_name,
            wait=True,
            points=points
        )

    def query_collection(self, vector: List[float], limit: int = 8):
        return self.client.query_points(
            collection_name=self.collection_name,
            query=vector,
            limit=limit
        )
