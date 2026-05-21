import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.database_mock import DatabaseMock

class ReconciliationAgent:
    def __init__(self, nv_client):
        self.nv_client = nv_client
        self.name = "Payment Reconciliation Agent"
        self.system_prompt = (
            "You are the Payment Reconciliation Agent, running on nvidia/nvidia-nemotron-nano-9b-v2.\n"
            "Your job is to resolve database synchronization issues where a student paid but the dashboard did not update.\n"
            "Review transaction gateway logs and ERP records, check for delta values, and outline reconciliation status.\n"
            "Advise the student to upload their payment receipt, and check if there are unmatched exceptions in the system."
        )

    def execute(self, student_id: str, query: str) -> str:
        exceptions = DatabaseMock.get_exceptions()
        my_exceptions = [e for e in exceptions if e["student_id"] == student_id]
        
        exc_str = ""
        if my_exceptions:
            for exc in my_exceptions:
                exc_str += (
                    f"- Exception ID: {exc['exception_id']}\n"
                    f"  Gateway Txn ID: {exc['txn_id']}\n"
                    f"  Expected: ₹ {exc['expected']:,.2f}\n"
                    f"  Received: ₹ {exc['received']:,.2f}\n"
                    f"  Delta: ₹ {exc['delta']:,.2f}\n"
                    f"  Gateway Source: {exc['source']}\n"
                    f"  Status: {exc['status']}\n"
                )
        else:
            exc_str = "No pending synchronization exceptions found for this student."
            
        user_prompt = (
            f"Student ID: {student_id}\n"
            f"Reconciliation Exceptions in Log:\n{exc_str}\n\n"
            f"Student Query: {query}\n\n"
            f"Provide explanation of what reconciliation sync exceptions are, check for exceptions, and tell them what files to upload."
        )
        return self.nv_client.call_child_agent(self.name, self.system_prompt, user_prompt)
