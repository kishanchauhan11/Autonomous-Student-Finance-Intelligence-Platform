# nim_config.py - NVIDIA NIM On-Premise GPU Inference Configuration for FinVault
# Manages NVIDIA NIM container deployments for self-hosted LLM inference on GPU nodes.

import os
from typing import Dict, Any, List

# ── NIM Model Registry ─────────────────────────────────────────────────────
NIM_MODELS: Dict[str, Dict[str, Any]] = {
    "deepseek-v3-0324": {
        "nim_image": "nvcr.io/nim/deepseek-ai/deepseek-v3-0324:latest",
        "role": "Root Orchestrator & Intent Classifier",
        "min_gpu_vram_gb": 80,
        "recommended_gpu": "NVIDIA H100 SXM 80GB",
        "quantization": "FP8",
        "max_batch_size": 32,
        "max_context_tokens": 128000,
        "api_endpoint": "/v1/chat/completions",
        "environment_vars": {
            "NIM_MODEL_NAME": "deepseek-ai/deepseek-v3-0324",
            "NIM_MAX_MODEL_LEN": "32768",
            "NIM_TENSOR_PARALLEL_SIZE": "4",
            "NIM_GPU_MEMORY_UTILIZATION": "0.90",
        }
    },
    "llama-guard-4-12b": {
        "nim_image": "nvcr.io/nim/meta/llama-guard-4-12b:latest",
        "role": "Safety Guardrail (Input/Output Filtering)",
        "min_gpu_vram_gb": 24,
        "recommended_gpu": "NVIDIA A10G 24GB",
        "quantization": "FP16",
        "max_batch_size": 64,
        "api_endpoint": "/v1/chat/completions",
        "environment_vars": {
            "NIM_MODEL_NAME": "meta/llama-guard-4-12b",
            "NIM_MAX_MODEL_LEN": "8192",
            "NIM_TENSOR_PARALLEL_SIZE": "1",
        }
    },
    "nv-embedqa-e5-v5": {
        "nim_image": "nvcr.io/nim/nvidia/nv-embedqa-e5-v5:latest",
        "role": "RAG Embedding Generation",
        "min_gpu_vram_gb": 8,
        "recommended_gpu": "NVIDIA L4 24GB",
        "api_endpoint": "/v1/embeddings",
        "environment_vars": {
            "NIM_MODEL_NAME": "nvidia/nv-embedqa-e5-v5",
        }
    },
    "nv-rerankqa-mistral-4b": {
        "nim_image": "nvcr.io/nim/nvidia/nv-rerankqa-mistral-4b-v3:latest",
        "role": "RAG Passage Reranking",
        "min_gpu_vram_gb": 8,
        "recommended_gpu": "NVIDIA L4 24GB",
        "api_endpoint": "/v1/ranking",
        "environment_vars": {
            "NIM_MODEL_NAME": "nvidia/nv-rerankqa-mistral-4b-v3",
        }
    }
}

# ── Docker Compose snippet for local GPU NIM deployment ───────────────────
NIM_DOCKER_COMPOSE_SNIPPET = """
# Add to docker-compose.yml for on-premise GPU inference
# Requires: NVIDIA Container Toolkit, Docker >= 24.0, NGC API Key

services:
  nim-deepseek-orchestrator:
    image: nvcr.io/nim/deepseek-ai/deepseek-v3-0324:latest
    container_name: finvault-nim-orchestrator
    environment:
      - NGC_API_KEY=${NGC_API_KEY}
      - NIM_MODEL_NAME=deepseek-ai/deepseek-v3-0324
      - NIM_MAX_MODEL_LEN=32768
      - NIM_TENSOR_PARALLEL_SIZE=4
    ports:
      - "8001:8000"
    volumes:
      - nim-cache:/opt/nim/.cache
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 4
              capabilities: [gpu]
    restart: unless-stopped

  nim-llama-guard:
    image: nvcr.io/nim/meta/llama-guard-4-12b:latest
    container_name: finvault-nim-guard
    environment:
      - NGC_API_KEY=${NGC_API_KEY}
      - NIM_MODEL_NAME=meta/llama-guard-4-12b
    ports:
      - "8002:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

  nim-embeddings:
    image: nvcr.io/nim/nvidia/nv-embedqa-e5-v5:latest
    container_name: finvault-nim-embeddings
    environment:
      - NGC_API_KEY=${NGC_API_KEY}
    ports:
      - "8003:8000"
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped

volumes:
  nim-cache:
    driver: local
"""

class NIMConfigManager:
    """Manages NVIDIA NIM GPU inference configuration and health checking."""

    @staticmethod
    def get_model_config(model_name: str) -> Dict[str, Any]:
        return NIM_MODELS.get(model_name, {})

    @staticmethod
    def list_models() -> List[str]:
        return list(NIM_MODELS.keys())

    @staticmethod
    def get_gpu_requirements() -> Dict[str, Any]:
        """Returns total GPU VRAM requirement for all NIM services."""
        total_vram = sum(m.get("min_gpu_vram_gb", 0) for m in NIM_MODELS.values())
        return {
            "total_min_vram_gb": total_vram,
            "recommended_setup": "4x NVIDIA H100 80GB SXM + 2x NVIDIA L4 24GB",
            "models": {k: v["min_gpu_vram_gb"] for k, v in NIM_MODELS.items() if "min_gpu_vram_gb" in v},
            "cloud_alternative": "Use NVIDIA Cloud API (integrate.api.nvidia.com) for zero GPU overhead"
        }

    @staticmethod
    def get_docker_compose_snippet() -> str:
        return NIM_DOCKER_COMPOSE_SNIPPET

    @staticmethod
    def get_nim_env_config(model_name: str, ngc_api_key: str = "") -> Dict[str, str]:
        """Returns environment variables dict for launching a NIM container."""
        model = NIM_MODELS.get(model_name, {})
        env = {"NGC_API_KEY": ngc_api_key or os.getenv("NGC_API_KEY", "")}
        env.update(model.get("environment_vars", {}))
        return env


if __name__ == "__main__":
    print("=== FinVault NVIDIA NIM Configuration ===")
    reqs = NIMConfigManager.get_gpu_requirements()
    print(f"Total GPU VRAM Required: {reqs['total_min_vram_gb']} GB")
    print(f"Recommended Setup: {reqs['recommended_setup']}")
    print(f"Models configured: {', '.join(NIMConfigManager.list_models())}")
    print("\nDocker Compose GPU inference snippet:")
    print(NIMConfigManager.get_docker_compose_snippet())
