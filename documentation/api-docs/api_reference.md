# api_reference.md - FinVault API Gateway Reference

This document covers all the RESTful endpoints hosted by the FastAPI backend server (`http://localhost:8000`).

---

## 1. Student & Ledger Endpoints

### Get Student Profile
* **Route**: `GET /api/student/{student_id}`
* **Description**: Returns demographic details and ledger balances (billed, paid, scholarship, late fees, currency) for a student.
* **Response**:
```json
{
  "student": {
    "id": "STU-2021-4892",
    "name": "Arjun Shah",
    "program": "B.Tech Computer Science",
    "semester": 7,
    "email": "arjun.shah@university.edu",
    "phone": "+91 98765 43210",
    "currency": "INR"
  },
  "ledger": {
    "billed": 150000.0,
    "scholarship": 25000.0,
    "paid": 150000.0,
    "late_fees": 0.0,
    "balance": 0.0
  }
}
```

### Get Transactions
* **Route**: `GET /api/transactions/{student_id}`
* **Description**: Retrieves historical transaction records.
* **Response**:
```json
[
  {
    "txn_id": "TXN-10928",
    "student_id": "STU-2021-4892",
    "date": "12 May 2026",
    "category": "Tuition Fee Sem 7",
    "amount": 125000.0,
    "method": "Net Banking",
    "status": "APPROVED"
  }
]
```

### Process Payment
* **Route**: `POST /api/transactions/pay`
* **Description**: Submits a direct student fee payment and updates their mock database paid total.
* **Request Payload**:
```json
{
  "student_id": "STU-2021-4892",
  "amount": 10000.00,
  "category": "Tuition Fee Sem 7",
  "method": "Net Banking"
}
```
* **Response**:
```json
{
  "success": true,
  "transaction": {
    "txn_id": "TXN-84512",
    "student_id": "STU-2021-4892",
    "date": "21 May 2026",
    "category": "Tuition Fee Sem 7",
    "amount": 10000.0,
    "method": "Net Banking",
    "status": "APPROVED"
  },
  "message": "Payment of INR 10000.00 processed successfully."
}
```

---

## 2. Refund Tracker Endpoints

### Get Refunds
* **Route**: `GET /api/refunds/{student_id}`
* **Description**: Lists all refund requests initiated by the student.
* **Response**:
```json
[
  {
    "request_id": "REF-8902",
    "student_id": "STU-2021-4892",
    "description": "Double Payment Refund Request",
    "amount": 150000.0,
    "submitted_date": "16 May 2026",
    "stage": "VERIFICATION",
    "eta_days": 12
  }
]
```

### Create Refund Request
* **Route**: `POST /api/refunds/request`
* **Description**: Submits a new refund request.
* **Request Payload**:
```json
{
  "student_id": "STU-2021-4892",
  "amount": 45000.0,
  "description": "Hostel fee waiver refund"
}
```
* **Response**:
```json
{
  "request_id": "REF-9143",
  "student_id": "STU-2021-4892",
  "description": "Hostel fee waiver refund",
  "amount": 45000.0,
  "submitted_date": "21 May 2026",
  "stage": "SUBMITTED",
  "eta_days": 15
}
```

---

## 3. Education Loan Letter Endpoints

### Get Loan Letters
* **Route**: `GET /api/loans/{student_id}`
* **Description**: Returns a student's generated loan letters.
* **Response**:
```json
[
  {
    "letter_id": "LND-0912",
    "student_id": "STU-2021-4892",
    "program": "B.Tech CSE",
    "bank": "HDFC BANK",
    "amount": 150000.0,
    "status": "ISSUED",
    "download_url": "/downloads/loan-demand-STU-2021-4892.pdf"
  }
]
```

### Request Loan Letter
* **Route**: `POST /api/loans/request`
* **Description**: Logs a request for a dynamic demand letter.
* **Request Payload**:
```json
{
  "student_id": "STU-2021-4892",
  "program": "B.Tech CSE",
  "bank": "HDFC BANK",
  "amount": 150000.0
}
```
* **Response**: Returns the newly logged loan letter object.

### Download Loan Letter PDF
* **Route**: `GET /downloads/loan-demand-{student_id}.pdf`
* **Description**: Dynamically constructs and downloads a certified educational loan demand letter in PDF format.
* **Response**: Binary stream (`application/pdf`) with `Content-Disposition: inline; filename=loan-demand-{student_id}.pdf`.

---

## 4. Admin Portal Endpoints

### Get Reconciliation Exceptions
* **Route**: `GET /api/exceptions`
* **Description**: Lists transaction reconciliation exceptions (gateway vs. bank ledger mismatches).
* **Response**:
```json
[
  {
    "txn_id": "TXN-RP-9812",
    "student_id": "STU-2021-4892",
    "source": "Razorpay API",
    "expected": 150000.0,
    "received": 0.0,
    "delta": -150000.0,
    "status": "UNMATCHED"
  }
]
```

### Run Reconciliation Sync
* **Route**: `POST /api/reconcile/run/{student_id}`
* **Description**: Scans unmatched exceptions for a student and synchronizes them to the ERP, resolving the billing discrepancy.
* **Response**:
```json
{
  "reconciled": true,
  "amount": 150000.0,
  "txn_id": "TXN-RP-9812",
  "message": "Reconciled mismatch successfully"
}
```

### Get Approvals Queue
* **Route**: `GET /api/approvals`
* **Description**: Fetches items awaiting manual review or Director authorization (e.g. refund requests > 100,000 INR).
* **Response**:
```json
[
  {
    "approval_id": "APP-09012",
    "type": "Refund Approval (High Value)",
    "student_id": "STU-2021-4892",
    "amount": 150000.0,
    "priority": "HIGH",
    "age_hours": 4,
    "details": "Refund request REF-8902 exceeds high value threshold.",
    "status": "PENDING"
  }
]
```

### Process Approval Action
* **Route**: `POST /api/approvals/action/{approval_id}`
* **Description**: Executes approval action (APPROVE/REJECT) on a queue item.
* **Request Payload**:
```json
{
  "action": "APPROVE",
  "officer": "Sarah Jenkins"
}
```
* **Response**: Returns status updates.

---

## 5. Audit & AI Chat Endpoints

### Get Audit Logs
* **Route**: `GET /api/audit-logs`
* **Description**: Retreives simulated Kafka telemetry log records.
* **Response**:
```json
[
  {
    "event_id": "EVT-84512-KAFKA",
    "topic": "payment-reconciled",
    "timestamp": "2026-05-21 03:52:16",
    "payload": { ... }
  }
]
```

### Chat with AI Orchestrator
* **Route**: `POST /api/chat`
* **Description**: Processes user finance query through the multi-agent DAG.
* **Request Payload**:
```json
{
  "student_id": "STU-2021-4892",
  "message": "How much is my tuition fee?",
  "history": []
}
```
* **Response**:
```json
{
  "safe": true,
  "agent": "Root Finance Orchestrator",
  "intent": "PAYMENT",
  "context": "...",
  "response": "Your total tuition fee is ...",
  "human_approval_required": false,
  "approval_details": null
}
```
