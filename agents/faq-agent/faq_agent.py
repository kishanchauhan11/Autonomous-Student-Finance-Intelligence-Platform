import sys
import os

# Append parent dir to sys.path so we can import shared modules if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

class FAQAgent:
    def __init__(self, nv_client):
        self.nv_client = nv_client
        self.name = "FAQ Agent"
        self.system_prompt = (
            "You are the University Finance FAQ Agent, running on nvidia/nvidia-nemotron-nano-9b-v2.\n"
            "Your job is to answer the student's question accurately using ONLY the provided official university policies in the context.\n"
            "Do not make up facts or policies. If the policy is not in the context, say that you cannot find the official policy and offer to escalate to a human Finance Officer.\n"
            "Provide clear, professional, step-by-step guidance. Format numbers, dates, and terms clearly."
        )

    def execute(self, student_id: str, query: str, context: str) -> str:
        user_prompt = f"Student ID: {student_id}\nQuery: {query}\n\nRetrieved University Policies:\n{context}\n\nAnswer:"
        return self.nv_client.call_child_agent(self.name, self.system_prompt, user_prompt)
