# nvidia_embeddings.py - Connects to NVIDIA NIM embedding services
from typing import List

class NvidiaEmbeddingService:
    def __init__(self, nv_client):
        self.nv_client = nv_client

    def generate_embeddings(self, texts: List[str], input_type: str = "passage") -> List[List[float]]:
        return self.nv_client.generate_embeddings(texts, input_type=input_type)
