import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.database_mock import DatabaseMock

class PaymentGuidanceAgent:
    def __init__(self, nv_client):
        self.nv_client = nv_client
        self.name = "Payment Guidance Agent"
        self.system_prompt = (
            "You are the Student Payment Guidance Agent, running on nvidia/nvidia-nemotron-nano-9b-v2.\n"
            "Your job is to explain the student's current account balance, billed amount, scholarship waivers, and any pending late fees.\n"
            "Walk them through the calculation step-by-step: Billed Amount - Scholarship Waiver + Late Fees = Total Payable.\n"
            "Be professional and trustworthy. Use IBM Plex Mono format for all monetary values (e.g. ₹ 45,000.00)."
        )

    def execute(self, student_id: str, query: str) -> str:
        balance_info = DatabaseMock.get_student_balance(student_id)
        student = DatabaseMock.get_student(student_id)
        
        if not student:
            return f"Error: Student ID {student_id} not found in the ERP database."
            
        user_prompt = (
            f"Student Info:\n"
            f"- Name: {student['name']}\n"
            f"- ID: {student['id']}\n"
            f"- Program: {student['program']}\n"
            f"- Semester: {student['semester']}\n"
            f"Ledger Values:\n"
            f"- Billed Tuition Fee: ₹ {balance_info['billed']:,.2f}\n"
            f"- Scholarship Waiver Applied: ₹ {balance_info['scholarship']:,.2f}\n"
            f"- Late Fees Outstanding: ₹ {balance_info['late_fees']:,.2f}\n"
            f"- Net Balance Due: ₹ {balance_info['balance']:,.2f}\n\n"
            f"Student Query: {query}\n\n"
            f"Provide a clear, detailed breakdown and steps on how to pay."
        )
        return self.nv_client.call_child_agent(self.name, self.system_prompt, user_prompt)
