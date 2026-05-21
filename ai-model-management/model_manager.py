import os
import json
from typing import Dict, Any, Optional

class ModelManager:
    _instance = None
    _catalog = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ModelManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if self._catalog is None:
            self._load_catalog()

    def _load_catalog(self):
        catalog_path = os.path.join(os.path.dirname(__file__), "model_catalog.json")
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                self._catalog = json.load(f)
        except Exception as e:
            print(f"Warning: Failed to load model_catalog.json: {e}. Using fallback default configuration.")
            self._catalog = self._get_fallback_catalog()

    def _get_fallback_catalog(self) -> Dict[str, Any]:
        return {
            "api_url": "https://integrate.api.nvidia.com/v1",
            "rerank_url": "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-nemotron-rerank-1b-v2/reranking",
            "models": {
                "safety": {"model_name": "meta/llama-guard-4-12b", "temperature": 0.1, "max_tokens": 10, "timeout": 10},
                "reasoning": {"model_name": "nvidia/nemotron-content-safety-reasoning-4b", "temperature": 0.2, "max_tokens": 512, "timeout": 15},
                "orchestrator_primary": {"model_name": "deepseek-ai/deepseek-v4-pro", "temperature": 0.7, "max_tokens": 2048, "timeout": 25},
                "orchestrator_fallback": {"model_name": "meta/llama-3.1-8b-instruct", "temperature": 0.5, "max_tokens": 1024, "timeout": 15},
                "child_agent_primary": {"model_name": "nvidia/nvidia-nemotron-nano-9b-v2", "temperature": 0.2, "max_tokens": 1024, "timeout": 20},
                "child_agent_fallback": {"model_name": "deepseek-ai/deepseek-v4-flash", "temperature": 0.2, "max_tokens": 1024, "timeout": 15},
                "reranker": {"model_name": "nvidia/llama-nemotron-rerank-1b-v2", "timeout": 15},
                "embeddings": {"model_name": "nvidia/llama-nemotron-embed-1b-v2", "timeout": 15}
            }
        }

    def get_api_url(self) -> str:
        return self._catalog.get("api_url", "https://integrate.api.nvidia.com/v1")

    def get_rerank_url(self) -> str:
        return self._catalog.get("rerank_url", "https://ai.api.nvidia.com/v1/retrieval/nvidia/llama-nemotron-rerank-1b-v2/reranking")

    def get_model_config(self, model_key: str) -> Dict[str, Any]:
        models = self._catalog.get("models", {})
        if model_key in models:
            return models[model_key]
        fallback = self._get_fallback_catalog().get("models", {})
        return fallback.get(model_key, {})

    def get_model_name(self, model_key: str) -> str:
        return self.get_model_config(model_key).get("model_name", "")

    def get_timeout(self, model_key: str) -> int:
        return self.get_model_config(model_key).get("timeout", 15)

    def get_temperature(self, model_key: str) -> float:
        return self.get_model_config(model_key).get("temperature", 0.5)

    def get_max_tokens(self, model_key: str) -> int:
        return self.get_model_config(model_key).get("max_tokens", 1024)
