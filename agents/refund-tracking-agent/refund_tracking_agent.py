import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.database_mock import DatabaseMock

class RefundTrackingAgent:
    def __init__(self, nv_client):
        self.nv_client = nv_client
        self.name = "Refund Tracking Agent"
        self.system_prompt = (
            "You are the Refund Tracking Agent, running on nvidia/nvidia-nemotron-nano-9b-v2.\n"
            "Your job is to check pending refund requests, explain the current processing stage (SUBMITTED, VERIFICATION, APPROVAL, PROCESSING, CREDITED), and highlight standard timelines.\n"
            "If the student wants to file a refund, or if there is a delay > 15 days, explain that they can submit a request and how the automatic escalation system will handle it.\n"
            "If they ask to file a refund, you must state that you will initiate the refund workflow."
        )

    def execute(self, student_id: str, query: str) -> str:
        refunds = DatabaseMock.get_refunds(student_id)
        refunds_str = ""
        if refunds:
            for r in refunds:
                history_str = " -> ".join([f"{h['status']} ({h['date']})" for h in r["history"]])
                refunds_str += (
                    f"- Request ID: {r['request_id']}\n"
                    f"  Description: {r['description']}\n"
                    f"  Amount: ₹ {r['amount']:,.2f}\n"
                    f"  Current Stage: {r['stage']}\n"
                    f"  Workflow History: {history_str}\n"
                    f"  Expected processing SLA: {r['eta_days']} days\n"
                )
        else:
            refunds_str = "No active refund requests found."
            
        user_prompt = (
            f"Student ID: {student_id}\n"
            f"Active Refunds in System:\n{refunds_str}\n\n"
            f"Student Query: {query}\n\n"
            f"Explain the refund status, steps, and options clearly."
        )
        return self.nv_client.call_child_agent(self.name, self.system_prompt, user_prompt)
