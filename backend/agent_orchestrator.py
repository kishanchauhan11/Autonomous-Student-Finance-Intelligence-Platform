import os
import json
import re
import sys
from typing import Dict, Any, List, Tuple

# Set up python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai-orchestration")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nvidia_client import NvidiaClient
from rag_engine import RagEngine
from workflow_engine import WorkflowEngine  # type: ignore

class AgentOrchestrator:
    def __init__(self):
        self.nv_client = NvidiaClient()
        self.rag = RagEngine(self.nv_client)
        self.workflow_engine = WorkflowEngine(self.nv_client, self.rag)

    def classify_intent(self, query: str, history: List[Dict[str, str]] = []) -> Tuple[str, str]:
        """
        Delegates classification to the WorkflowEngine in ai-orchestration.
        """
        return self.workflow_engine.classify_intent(query, history)

    def process_query(self, student_id: str, query: str, history: List[Dict[str, str]] = []) -> Dict[str, Any]:
        """
        Delegates execution to the WorkflowEngine in ai-orchestration.
        """
        return self.workflow_engine.run(student_id, query, history)

    def process_officer_query(self, officer_id: str, query: str, history: List[Dict[str, str]] = []) -> Dict[str, Any]:
        """
        Delegates Finance Officer queries to the WorkflowEngine officer handler.
        """
        return self.workflow_engine.run_officer_query(officer_id, query, history)

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    
    orchestrator = AgentOrchestrator()
    res = orchestrator.process_query("STU-2021-4892", "How do I pay my fees? Can I use international wire?")
    print("\n================ FINAL RESPONSE ================")
    print(res["response"])
