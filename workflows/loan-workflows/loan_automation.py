# loan_automation.py - Certifies estimates for bank education loans
import datetime
from typing import Dict, Any

class LoanAutomationManager:
    @staticmethod
    def create_loan_letter_record(letter_id: str, student_id: str, program: str, bank: str, amount: float) -> Dict[str, Any]:
        today_str = datetime.date.today().strftime("%d %b %Y")
        return {
            "letter_id": letter_id,
            "student_id": student_id,
            "program": program,
            "amount": amount,
            "bank": bank,
            "status": "APPROVED",
            "generated_on": today_str,
            "download_url": f"/downloads/loan-demand-{student_id}.pdf"
        }
