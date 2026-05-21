import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

class RootOrchestratorAgent:
    def __init__(self, nv_client):
        self.nv_client = nv_client
        self.name = "Root Orchestrator Agent (DeepSeek v4 Pro)"
        
    def classify_intent(self, messages: list) -> str:
        """
        Calls DeepSeek v4 Pro on NVIDIA NIM to classify user query intent.
        """
        return self.nv_client.call_root_orchestrator(messages)

    def compile_response(self, messages: list) -> str:
        """
        Compiles the final customer-facing response including citations and verification codes.
        """
        return self.nv_client.call_root_orchestrator(messages)
