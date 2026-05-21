import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.database_mock import DatabaseMock

class InternationalFinanceAgent:
    def __init__(self, nv_client):
        self.nv_client = nv_client
        self.name = "International Student Finance Agent"
        self.system_prompt = (
            "You are the International Student Finance Agent, running on nvidia/nvidia-nemotron-nano-9b-v2.\n"
            "Your job is to guide international students on currency exchange, SWIFT details, Western Union/Flywire portals, and forex processing fees (2.5%).\n"
            "Provide the exact SWIFT code (ITB1NDIA33B) and bank details if requested. Remind them to include their Student ID in the reference field.\n"
            "Perform country detection if they mention where they are from, and provide relevant currency rates if applicable."
        )

    def execute(self, student_id: str, query: str) -> str:
        student = DatabaseMock.get_student(student_id)
        balance_info = DatabaseMock.get_student_balance(student_id)
        
        user_prompt = (
            f"Student ID: {student_id}\n"
            f"Primary Currency in ERP: {student['currency'] if student else 'INR'}\n"
            f"Billed Tuition Fee: ₹ {balance_info['balance']:,.2f} INR\n\n"
            f"Student Query: {query}\n\n"
            f"Address their international transfer queries, list SWIFT details if needed, and explain exchange fee rules."
        )
        return self.nv_client.call_child_agent(self.name, self.system_prompt, user_prompt)
