import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.database_mock import DatabaseMock

class EscalationAgent:
    def __init__(self, nv_client):
        self.nv_client = nv_client
        self.name = "Escalation & Ticketing Agent"
        self.system_prompt = (
            "You are the Escalation Agent, running on nvidia/nvidia-nemotron-nano-9b-v2.\n"
            "Your job is to handle unresolved issues, assign priorities, and log support tickets for the accounts officers.\n"
            "Explain that you are creating a high-priority ticket in the Approval/Escalation queue and notifying the Finance Officer.\n"
            "Reassure the student that a human will contact them within 24 hours."
        )

    def execute(self, student_id: str, query: str) -> str:
        approvals = DatabaseMock.get_approvals()
        my_approvals = [a for a in approvals if a["student_id"] == student_id]
        
        app_str = ""
        if my_approvals:
            for a in my_approvals:
                app_str += f"- Ticket ID: {a['approval_id']} | Type: {a['type']} | Priority: {a['priority']} | Status: {a['status']} | Age: {a['age_hours']} hours\n"
        else:
            app_str = "No pending escalation tickets."
            
        user_prompt = (
            f"Student ID: {student_id}\n"
            f"Pending Escalations/Approvals Queue:\n{app_str}\n\n"
            f"Student Query: {query}\n\n"
            f"Confirm the ticket registration, priority, and assignees."
        )
        return self.nv_client.call_child_agent(self.name, self.system_prompt, user_prompt)
