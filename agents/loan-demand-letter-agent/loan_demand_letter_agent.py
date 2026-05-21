import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.database_mock import DatabaseMock

class LoanDemandLetterAgent:
    def __init__(self, nv_client):
        self.nv_client = nv_client
        self.name = "Loan Demand Letter Agent"
        self.system_prompt = (
            "You are the Loan Demand Letter Automation Agent, running on nvidia/nvidia-nemotron-nano-9b-v2.\n"
            "Your job is to assist students in generating official fee demand letters for bank education loans.\n"
            "Explain the three formats available: Current Semester, Next Semester, or Full Academic Year.\n"
            "Confirm that the letters are digitally signed by the Registrar, contain a secure QR verification hash, and list the exact fees billed in the ERP.\n"
            "Instruct the student clearly on how to generate and download their letter from the portal."
        )

    def execute(self, student_id: str, query: str) -> str:
        student = DatabaseMock.get_student(student_id)
        letters = DatabaseMock.get_loan_letters(student_id)
        
        letters_str = ""
        if letters:
            for l in letters:
                letters_str += f"- ID: {l['letter_id']} | Bank: {l['bank']} | Amount: ₹ {l['amount']:,.2f} | Status: {l['status']} | Date: {l['generated_on']}\n"
        else:
            letters_str = "No loan letters previously generated."
            
        if not student:
            return f"Error: Student ID {student_id} not found."
            
        user_prompt = (
            f"Student Info:\n"
            f"- Name: {student['name']}\n"
            f"- ID: {student['id']}\n"
            f"- Program: {student['program']}\n"
            f"- Semester: {student['semester']}\n"
            f"Existing Letters:\n{letters_str}\n\n"
            f"Student Query: {query}\n\n"
            f"Provide information about how to get the loan demand letter, list any existing ones, and outline the template options."
        )
        return self.nv_client.call_child_agent(self.name, self.system_prompt, user_prompt)
