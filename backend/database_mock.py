import datetime
import json
import os
import sys
from typing import List, Dict, Any, Optional

# Mock database tables representing MSSQL
STUDENTS = {
    "STU-2021-4892": {
        "id": "STU-2021-4892",
        "name": "Arjun Shah",
        "program": "B.Tech CSE",
        "semester": 7,
        "email": "arjun.shah@university.edu",
        "phone": "+91 98765 43210",
        "billed_amount": 195000.00,
        "scholarship_amount": 30000.00,
        "paid_amount": 150000.00,
        "late_fees": 0.00,
        "currency": "INR"
    },
    "STU-2022-1082": {
        "id": "STU-2022-1082",
        "name": "Sarah Connor",
        "program": "M.Sc Data Science",
        "semester": 3,
        "email": "sarah.c@university.edu",
        "phone": "+1 555-0199",
        "billed_amount": 250000.00,
        "scholarship_amount": 0.00,
        "paid_amount": 200000.00,
        "late_fees": 1500.00, # Overdue
        "currency": "USD"
    }
}

TRANSACTIONS = [
    {
        "txn_id": "TXN-10023",
        "student_id": "STU-2021-4892",
        "date": "12 May 2026",
        "category": "Tuition Fee Sem 7",
        "amount": 150000.00,
        "method": "Net Banking",
        "status": "APPROVED"
    },
    {
        "txn_id": "TXN-10008",
        "student_id": "STU-2021-4892",
        "date": "10 Jan 2026",
        "category": "Tuition Fee Sem 6",
        "amount": 180000.00,
        "method": "Credit Card",
        "status": "APPROVED"
    },
    {
        "txn_id": "TXN-20091",
        "student_id": "STU-2022-1082",
        "date": "05 May 2026",
        "category": "Tuition Fee Sem 3",
        "amount": 200000.00,
        "method": "SWIFT Transfer",
        "status": "APPROVED"
    }
]

REFUNDS = [
    {
        "request_id": "REF-2026-0901",
        "student_id": "STU-2021-4892",
        "description": "Double Payment Refund",
        "submitted_date": "14 May 2026",
        "amount": 150000.00, # High-value
        "stage": "VERIFICATION", # SUBMITTED -> VERIFICATION -> APPROVAL -> PROCESSING -> CREDITED
        "eta_days": 10,
        "history": [
            {"status": "SUBMITTED", "date": "14 May 2026", "by": "Student"},
            {"status": "VERIFICATION", "date": "15 May 2026", "by": "System Agent"}
        ]
    }
]

LOAN_LETTERS = [
    {
        "letter_id": "LOAN-2026-05",
        "student_id": "STU-2021-4892",
        "program": "B.Tech CSE",
        "amount": 195000.00,
        "bank": "State Bank of India",
        "status": "APPROVED",
        "generated_on": "10 May 2026",
        "download_url": "/downloads/loan-demand-STU-2021-4892.pdf"
    }
]

RECONCILIATION_EXCEPTIONS = [
    {
        "exception_id": "EXC-8812",
        "txn_id": "TXN-99882",
        "student_id": "STU-2021-4892",
        "expected": 45000.00,
        "received": 0.00,
        "delta": -45000.00,
        "source": "Razorpay Gateway",
        "status": "UNMATCHED",
        "created_date": "18 May 2026"
    }
]

HUMAN_APPROVAL_QUEUE = [
    {
        "approval_id": "APP-9011",
        "type": "Refund Approval (High Value)",
        "student_id": "STU-2021-4892",
        "amount": 150000.00,
        "priority": "HIGH",
        "age_hours": 12,
        "details": "Refund request for double tuition payment sem 7.",
        "status": "PENDING"
    }
]

# Redis session cache mock
REDIS_CACHE = {}

# Kafka events mock log (for explanation & tracking)
KAFKA_EVENTS = []

# Append root dir to sys.path to resolve database import
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if root_dir not in sys.path:
    sys.path.append(root_dir)
sys.path.insert(0, os.path.join(root_dir, "event-driven-system", "producers"))

try:
    from database.MSSQL.db_connection import DBConnection
except ImportError:
    class DBConnection:
        @staticmethod
        def is_mssql_active(): return False

try:
    from kafka_producer import FinVaultKafkaProducer  # type: ignore
    producer_instance = FinVaultKafkaProducer(KAFKA_EVENTS)
except ImportError:
    producer_instance = None

# Set up workflows path inserts
sys.path.insert(0, os.path.abspath(os.path.join(root_dir, "workflows", "refund-workflows")))
sys.path.insert(0, os.path.abspath(os.path.join(root_dir, "workflows", "loan-workflows")))
sys.path.insert(0, os.path.abspath(os.path.join(root_dir, "workflows", "payment-workflows")))
sys.path.insert(0, os.path.abspath(os.path.join(root_dir, "workflows", "escalation-workflows")))
sys.path.insert(0, os.path.abspath(os.path.join(root_dir, "workflows", "approval-workflows")))

from refund_lifecycle import RefundLifecycleManager  # type: ignore
from loan_automation import LoanAutomationManager  # type: ignore
from payment_reconciliation import PaymentReconciliationManager  # type: ignore
from escalation_ticket import EscalationManager  # type: ignore
from human_approval import HumanApprovalManager  # type: ignore

def clean_row(row: Dict[str, Any]) -> Dict[str, Any]:
    if not row:
        return row
    res = {}
    for k, v in row.items():
        if type(v).__name__ == 'Decimal':
            res[k] = float(v)
        else:
            res[k] = v
    return res

class DatabaseMock:
    @staticmethod
    def get_student(student_id: str) -> Optional[Dict[str, Any]]:
        if DBConnection.is_mssql_active():
            rows = DBConnection.execute_query("SELECT * FROM Students WHERE id = ?", (student_id,))
            return clean_row(rows[0]) if rows else None
        return STUDENTS.get(student_id)

    @staticmethod
    def get_student_balance(student_id: str) -> Dict[str, float]:
        if DBConnection.is_mssql_active():
            student = DatabaseMock.get_student(student_id)
            if not student:
                return {"balance": 0.0, "billed": 0.0, "paid": 0.0, "scholarship": 0.0, "late_fees": 0.0}
            balance = student["billed_amount"] - student["scholarship_amount"] - student["paid_amount"] + student["late_fees"]
            return {
                "balance": max(0.0, float(balance)),
                "billed": float(student["billed_amount"]),
                "paid": float(student["paid_amount"]),
                "scholarship": float(student["scholarship_amount"]),
                "late_fees": float(student["late_fees"])
            }
        
        student = STUDENTS.get(student_id)
        if not student:
            return {"balance": 0.0, "billed": 0.0, "paid": 0.0, "scholarship": 0.0, "late_fees": 0.0}
        balance = student["billed_amount"] - student["scholarship_amount"] - student["paid_amount"] + student["late_fees"]
        return {
            "balance": max(0.0, balance),
            "billed": student["billed_amount"],
            "paid": student["paid_amount"],
            "scholarship": student["scholarship_amount"],
            "late_fees": student["late_fees"]
        }

    @staticmethod
    def get_transactions(student_id: str) -> List[Dict[str, Any]]:
        if DBConnection.is_mssql_active():
            rows = DBConnection.execute_query("SELECT * FROM Transactions WHERE student_id = ?", (student_id,))
            return [clean_row(r) for r in rows]
        return [t for t in TRANSACTIONS if t["student_id"] == student_id]

    @staticmethod
    def add_transaction(txn: Dict[str, Any]):
        processed_txn = PaymentReconciliationManager.process_ledger_payment(
            txn["txn_id"], txn["student_id"], txn["date"], txn["category"], txn["amount"], txn["method"], txn.get("status", "APPROVED")
        )
        if DBConnection.is_mssql_active():
            DBConnection.execute_non_query(
                "INSERT INTO Transactions (txn_id, student_id, date, category, amount, method, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (processed_txn["txn_id"], processed_txn["student_id"], processed_txn["date"], processed_txn["category"], processed_txn["amount"], processed_txn["method"], processed_txn["status"])
            )
        else:
            TRANSACTIONS.append(processed_txn)
        print(f"[AUDIT LOG] Transaction {processed_txn['txn_id']} added for student {processed_txn['student_id']} - Amount: {processed_txn['amount']}")
        DatabaseMock.log_kafka_event("payment-reconciled", processed_txn)

    @staticmethod
    def update_student_paid_amount(student_id: str, amount: float):
        if DBConnection.is_mssql_active():
            DBConnection.execute_non_query(
                "UPDATE Students SET paid_amount = paid_amount + ? WHERE id = ?",
                (amount, student_id)
            )
        else:
            student = STUDENTS.get(student_id)
            if student:
                student["paid_amount"] += amount
                print(f"[AUDIT LOG] Updated student {student_id} paid_amount by +{amount}. New total: {student['paid_amount']}")

    @staticmethod
    def get_refunds(student_id: str) -> List[Dict[str, Any]]:
        if DBConnection.is_mssql_active():
            rows = DBConnection.execute_query("SELECT * FROM Refunds WHERE student_id = ?", (student_id,))
            refunds = []
            for r in rows:
                ref = clean_row(r)
                history_rows = DBConnection.execute_query(
                    "SELECT status, date, action_by as [by] FROM RefundHistory WHERE request_id = ? ORDER BY id ASC",
                    (ref["request_id"],)
                )
                ref["history"] = history_rows
                refunds.append(ref)
            return refunds
        return [r for r in REFUNDS if r["student_id"] == student_id]

    @staticmethod
    def create_refund_request(student_id: str, amount: float, description: str) -> Dict[str, Any]:
        req_id = f"REF-2026-0{len(REFUNDS) + 902}"
        if DBConnection.is_mssql_active():
            total_count = DBConnection.execute_query("SELECT COUNT(*) as cnt FROM Refunds")[0]["cnt"]
            req_id = f"REF-2026-0{total_count + 902}"
            
        new_refund = RefundLifecycleManager.initialize_refund(req_id, student_id, amount, description)
        today_str = new_refund["submitted_date"]
        
        if DBConnection.is_mssql_active():
            DBConnection.execute_non_query(
                "INSERT INTO Refunds (request_id, student_id, description, submitted_date, amount, stage, eta_days) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (req_id, student_id, description, today_str, amount, "SUBMITTED", 15)
            )
            DBConnection.execute_non_query(
                "INSERT INTO RefundHistory (request_id, status, date, action_by) VALUES (?, ?, ?, ?)",
                (req_id, "SUBMITTED", today_str, "Student")
            )
        else:
            REFUNDS.append(new_refund)
            
        DatabaseMock.log_kafka_event("refund-submitted", new_refund)
        
        # High value approval check
        if amount > 100000.00:
            approval_id = f"APP-0{len(HUMAN_APPROVAL_QUEUE) + 9012}"
            if DBConnection.is_mssql_active():
                total_approvals = DBConnection.execute_query("SELECT COUNT(*) as cnt FROM HumanApprovalQueue")[0]["cnt"]
                approval_id = f"APP-0{total_approvals + 9012}"
                
            details_str = f"High value refund request {req_id} requires Director approval."
            new_approval = EscalationManager.initiate_escalation(approval_id, student_id, amount, details_str, "HIGH")
            
            if DBConnection.is_mssql_active():
                DBConnection.execute_non_query(
                    "INSERT INTO HumanApprovalQueue (approval_id, type, student_id, amount, priority, age_hours, details, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (approval_id, "Refund Approval (High Value)", student_id, amount, "HIGH", 0, details_str, "PENDING")
                )
                DBConnection.execute_non_query(
                    "UPDATE Refunds SET stage = 'VERIFICATION' WHERE request_id = ?", (req_id,)
                )
                DBConnection.execute_non_query(
                    "INSERT INTO RefundHistory (request_id, status, date, action_by) VALUES (?, ?, ?, ?)",
                    (req_id, "VERIFICATION", today_str, "System Agent")
                )
            else:
                HUMAN_APPROVAL_QUEUE.append(new_approval)
                new_refund["stage"] = "VERIFICATION"
                new_refund["history"].append({"status": "VERIFICATION", "date": today_str, "by": "System Agent"})
                
            new_refund["stage"] = "VERIFICATION"
            print(f"[AUDIT LOG] High value refund {req_id} triggered Human Approval {approval_id}")
            DatabaseMock.log_kafka_event("approval-required", new_approval)
            
        return new_refund

    @staticmethod
    def get_loan_letters(student_id: str) -> List[Dict[str, Any]]:
        if DBConnection.is_mssql_active():
            rows = DBConnection.execute_query("SELECT * FROM LoanLetters WHERE student_id = ?", (student_id,))
            return [clean_row(r) for r in rows]
        return [l for l in LOAN_LETTERS if l["student_id"] == student_id]

    @staticmethod
    def create_loan_letter(student_id: str, program: str, bank: str, amount: float) -> Dict[str, Any]:
        letter_id = f"LOAN-2026-{len(LOAN_LETTERS) + 6:02d}"
        if DBConnection.is_mssql_active():
            total_letters = DBConnection.execute_query("SELECT COUNT(*) as cnt FROM LoanLetters")[0]["cnt"]
            letter_id = f"LOAN-2026-{(total_letters + 6):02d}"
            
        new_letter = LoanAutomationManager.create_loan_letter_record(letter_id, student_id, program, bank, amount)
        today_str = new_letter["generated_on"]
        
        if DBConnection.is_mssql_active():
            DBConnection.execute_non_query(
                "INSERT INTO LoanLetters (letter_id, student_id, program, amount, bank, status, generated_on, download_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (letter_id, student_id, program, amount, bank, "APPROVED", today_str, new_letter["download_url"])
            )
        else:
            LOAN_LETTERS.append(new_letter)
            
        DatabaseMock.log_kafka_event("loan-letter-generated", new_letter)
        return new_letter

    @staticmethod
    def get_exceptions() -> List[Dict[str, Any]]:
        if DBConnection.is_mssql_active():
            rows = DBConnection.execute_query("SELECT * FROM ReconciliationExceptions")
            return [clean_row(r) for r in rows]
        return RECONCILIATION_EXCEPTIONS

    @staticmethod
    def get_approvals() -> List[Dict[str, Any]]:
        if DBConnection.is_mssql_active():
            rows = DBConnection.execute_query("SELECT * FROM HumanApprovalQueue")
            return [clean_row(r) for r in rows]
        return HUMAN_APPROVAL_QUEUE

    @staticmethod
    def process_approval(approval_id: str, action: str, officer: str = "Finance Officer") -> bool:
        """Approve or Reject a pending request in the queue"""
        today_str = datetime.date.today().strftime("%d %b %Y")
        
        if DBConnection.is_mssql_active():
            rows = DBConnection.execute_query("SELECT * FROM HumanApprovalQueue WHERE approval_id = ? AND status = 'PENDING'", (approval_id,))
            if not rows:
                return False
            app = rows[0]
            
            # Update approval queue
            DBConnection.execute_non_query(
                "UPDATE HumanApprovalQueue SET status = ? WHERE approval_id = ?",
                (action.upper(), approval_id)
            )
            print(f"[AUDIT LOG] Human Approval {approval_id} has been {action}ed by {officer}")
            
            if "Refund" in app["type"]:
                # Fetch matching verification stage refund
                ref_rows = DBConnection.execute_query(
                    "SELECT * FROM Refunds WHERE student_id = ? AND amount = ? AND stage = 'VERIFICATION'",
                    (app["student_id"], app["amount"])
                )
                for ref_db in ref_rows:
                    req_id = ref_db["request_id"]
                    ref = clean_row(ref_db)
                    ref["history"] = [] # Temporarily populate history for manager if needed
                    if action.upper() == "APPROVED":
                        HumanApprovalManager.approve_refund_state(ref, officer)
                        DBConnection.execute_non_query("UPDATE Refunds SET stage = 'PROCESSING' WHERE request_id = ?", (req_id,))
                        DBConnection.execute_non_query(
                            "INSERT INTO RefundHistory (request_id, status, date, action_by) VALUES (?, ?, ?, ?)",
                            (req_id, "APPROVAL", today_str, officer)
                        )
                        DBConnection.execute_non_query(
                            "INSERT INTO RefundHistory (request_id, status, date, action_by) VALUES (?, ?, ?, ?)",
                            (req_id, "PROCESSING", today_str, "ERP Connector")
                        )
                    else:
                        HumanApprovalManager.reject_refund_state(ref, officer)
                        DBConnection.execute_non_query("UPDATE Refunds SET stage = 'REJECTED' WHERE request_id = ?", (req_id,))
                        DBConnection.execute_non_query(
                            "INSERT INTO RefundHistory (request_id, status, date, action_by) VALUES (?, ?, ?, ?)",
                            (req_id, "REJECTED", today_str, officer)
                        )
            return True
            
        else:
            for app in HUMAN_APPROVAL_QUEUE:
                if app["approval_id"] == approval_id and app["status"] == "PENDING":
                    app["status"] = action.upper()
                    print(f"[AUDIT LOG] Human Approval {approval_id} has been {action}ed by {officer}")
                    
                    if "Refund" in app["type"]:
                        for ref in REFUNDS:
                            if ref["student_id"] == app["student_id"] and ref["amount"] == app["amount"] and ref["stage"] == "VERIFICATION":
                                if action.upper() == "APPROVED":
                                    HumanApprovalManager.approve_refund_state(ref, officer)
                                    DatabaseMock.log_kafka_event("refund-approved", ref)
                                else:
                                    HumanApprovalManager.reject_refund_state(ref, officer)
                                    DatabaseMock.log_kafka_event("refund-rejected", ref)
                    return True
            return False

    @staticmethod
    def log_kafka_event(topic: str, data: Dict[str, Any]):
        if producer_instance:
            producer_instance.publish_event(topic, data)
            return
            
        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "topic": topic,
            "payload": data
        }
        if DBConnection.is_mssql_active():
            DBConnection.execute_non_query(
                "INSERT INTO KafkaEvents (topic, payload) VALUES (?, ?)",
                (topic, json.dumps(data))
            )
        else:
            KAFKA_EVENTS.append(event)
        try:
            print(f"[KAFKA EVENT] Published to topic '{topic}': {data}")
        except UnicodeEncodeError:
            import copy
            data_clean = copy.deepcopy(data)
            if isinstance(data_clean, dict):
                for k, v in data_clean.items():
                    if isinstance(v, str):
                        data_clean[k] = v.encode('ascii', errors='replace').decode('ascii')
            print(f"[KAFKA EVENT] Published to topic '{topic}': {data_clean}")

    @staticmethod
    def get_kafka_events() -> List[Dict[str, Any]]:
        if DBConnection.is_mssql_active():
            rows = DBConnection.execute_query("SELECT timestamp, topic, payload FROM KafkaEvents ORDER BY event_id ASC")
            events = []
            for r in rows:
                events.append({
                    "timestamp": r["timestamp"].isoformat() if hasattr(r["timestamp"], 'isoformat') else str(r["timestamp"]),
                    "topic": r["topic"],
                    "payload": json.loads(r["payload"])
                })
            return events
        return KAFKA_EVENTS
