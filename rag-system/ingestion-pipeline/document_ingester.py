# document_ingester.py - Parses JSON policies and populates Qdrant
import os
import json
from qdrant_client.models import PointStruct
from typing import List, Dict, Any

class DocumentIngester:
    def __init__(self, qdrant_service, embedding_service, default_policies: List[Dict[str, Any]]):
        self.qdrant = qdrant_service
        self.embedding_service = embedding_service
        self.default_policies = default_policies

    def ingest(self, json_path: str = None) -> List[Dict[str, Any]]:
        policies = self.default_policies
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    policies = json.load(f)
                print("Loaded university policies from externalized knowledge-base file.")
            except Exception as e:
                print(f"Error loading university_policies.json: {e}. Falling back to default list.")
        
        texts = [doc["text"] for doc in policies]
        embeddings = self.embedding_service.generate_embeddings(texts, input_type="passage")
        
        points = []
        for idx, (doc, emb) in enumerate(zip(policies, embeddings)):
            points.append(PointStruct(
                id=idx,
                vector=emb,
                payload={
                    "doc_id": doc["id"],
                    "category": doc["category"],
                    "title": doc["title"],
                    "text": doc["text"]
                }
            ))
            
        self.qdrant.upsert_points(points)
        return policies
