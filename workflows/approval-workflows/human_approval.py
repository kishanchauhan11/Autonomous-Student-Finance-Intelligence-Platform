# human_approval.py - Manages dual-authorization and administrative signoff states
import datetime
from typing import Dict, Any, List

class HumanApprovalManager:
    @staticmethod
    def approve_refund_state(refund_record: Dict[str, Any], officer: str) -> Dict[str, Any]:
        today_str = datetime.date.today().strftime("%d %b %Y")
        refund_record["stage"] = "PROCESSING"
        refund_record["history"].append({"status": "APPROVAL", "date": today_str, "by": officer})
        refund_record["history"].append({"status": "PROCESSING", "date": today_str, "by": "ERP Connector"})
        return refund_record

    @staticmethod
    def reject_refund_state(refund_record: Dict[str, Any], officer: str) -> Dict[str, Any]:
        today_str = datetime.date.today().strftime("%d %b %Y")
        refund_record["stage"] = "REJECTED"
        refund_record["history"].append({"status": "REJECTED", "date": today_str, "by": officer})
        return refund_record
