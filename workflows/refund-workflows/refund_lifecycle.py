# refund_lifecycle.py - Manages refund stage transitions and SLAs
import datetime
from typing import Dict, Any, List

class RefundLifecycleManager:
    @staticmethod
    def initialize_refund(request_id: str, student_id: str, amount: float, description: str) -> Dict[str, Any]:
        today_str = datetime.date.today().strftime("%d %b %Y")
        return {
            "request_id": request_id,
            "student_id": student_id,
            "description": description,
            "submitted_date": today_str,
            "amount": amount,
            "stage": "SUBMITTED",
            "eta_days": 15,
            "history": [{"status": "SUBMITTED", "date": today_str, "by": "Student"}]
        }
