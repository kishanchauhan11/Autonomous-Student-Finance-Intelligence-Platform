# escalation_ticket.py - Manages manual and automated escalation ticket generation
from typing import Dict, Any

class EscalationManager:
    @staticmethod
    def initiate_escalation(approval_id: str, student_id: str, amount: float, details: str, priority: str = "HIGH") -> Dict[str, Any]:
        return {
            "approval_id": approval_id,
            "type": "Refund Approval (High Value)",
            "student_id": student_id,
            "amount": amount,
            "priority": priority,
            "age_hours": 0,
            "details": details,
            "status": "PENDING"
        }
