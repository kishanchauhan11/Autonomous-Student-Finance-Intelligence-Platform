# semantic_retriever.py - Orchestrates semantic retrieval and reranking
from typing import List, Dict, Any

class SemanticRetriever:
    def __init__(self, qdrant_service, embedding_service, reranker_service):
        self.qdrant = qdrant_service
        self.embedding_service = embedding_service
        self.reranker = reranker_service

    def retrieve(self, query: str, top_k: int = 4) -> str:
        # 1. Embed query (requires 'query' input type)
        query_emb = self.embedding_service.generate_embeddings([query], input_type="query")[0]
        
        # 2. Vector search in Qdrant collection
        search_results = self.qdrant.query_collection(query_emb, limit=top_k * 2)
        if not search_results or not search_results.points:
            return "No relevant university policy documents found."
            
        passages = [res.payload["text"] for res in search_results.points]
        
        # 3. Rerank
        print(f"Reranking {len(passages)} passages for query: '{query}'")
        reranked_results = self.reranker.rerank(query, passages)
        
        # 4. Formulate final context from top-k reranked passages
        top_passages = [item["text"] for item in reranked_results[:top_k]]
        return "\n\n".join(top_passages)
