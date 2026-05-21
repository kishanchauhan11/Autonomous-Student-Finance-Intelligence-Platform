# nvidia_reranker.py - Connects to NVIDIA NIM reranking services
from typing import List, Dict, Any

class NvidiaRerankerService:
    def __init__(self, nv_client):
        self.nv_client = nv_client

    def rerank(self, query: str, passages: List[str]) -> List[Dict[str, Any]]:
        return self.nv_client.rerank_passages(query, passages)
