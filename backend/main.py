import os
import uvicorn
import random
import datetime
from io import BytesIO
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from nvidia_client import NvidiaClient
from database_mock import DatabaseMock
from agent_orchestrator import AgentOrchestrator

app = FastAPI(
    title="Autonomous Student Finance Intelligence Platform - API",
    description="Enterprise API Gateway representing the backend microservices layer.",
    version="1.0.0"
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Orchestrator
orchestrator = AgentOrchestrator()

# Models
class ChatRequest(BaseModel):
    student_id: str
    message: str
    history: List[Dict[str, str]] = []

class RefundRequestPayload(BaseModel):
    student_id: str
    amount: float
    description: str

class LoanRequestPayload(BaseModel):
    student_id: str
    program: str
    bank: str
    amount: float

class ApprovalActionPayload(BaseModel):
    action: str # APPROVE or REJECT
    officer: str = "Finance Officer"

class PaymentRequestPayload(BaseModel):
    student_id: str
    amount: float
    category: str
    method: str = "Net Banking"

# API Routes
@app.get("/")
def read_root():
    return {
        "status": "ONLINE",
        "platform": "Autonomous Student Finance Intelligence Platform",
        "orchestrator": "DeepSeek v4 Pro",
        "agent_runtime": "LangGraph + CrewAI"
    }

@app.get("/api/v1/exams/workflow-state")
def get_exams_workflow_state():
    return {
        "status": "COMPLETED",
        "workflow_id": "WF-EXAM-9812",
        "timestamp": "2026-05-19T17:31:00Z"
    }

@app.get("/api/student/{student_id}")
def get_student_data(student_id: str):
    student = DatabaseMock.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    balance_info = DatabaseMock.get_student_balance(student_id)
    return {
        "student": student,
        "ledger": balance_info
    }

@app.get("/api/transactions/{student_id}")
def get_student_transactions(student_id: str):
    return DatabaseMock.get_transactions(student_id)

@app.post("/api/transactions/pay")
def pay_transaction(payload: PaymentRequestPayload):
    student = DatabaseMock.get_student(payload.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    txn_id = f"TXN-{random.randint(10000, 99999)}"
    today_str = datetime.date.today().strftime("%d %b %Y")
    
    new_txn = {
        "txn_id": txn_id,
        "student_id": payload.student_id,
        "date": today_str,
        "category": payload.category,
        "amount": payload.amount,
        "method": payload.method,
        "status": "APPROVED"
    }
    
    # Save transaction and update student balance
    DatabaseMock.add_transaction(new_txn)
    DatabaseMock.update_student_paid_amount(payload.student_id, payload.amount)
    
    return {
        "success": True,
        "transaction": new_txn,
        "message": f"Payment of {student.get('currency', 'INR')} {payload.amount:.2f} processed successfully."
    }

@app.get("/api/refunds/{student_id}")
def get_student_refunds(student_id: str):
    return DatabaseMock.get_refunds(student_id)

@app.post("/api/refunds/request")
def create_refund(payload: RefundRequestPayload):
    refund = DatabaseMock.create_refund_request(
        payload.student_id,
        payload.amount,
        payload.description
    )
    return refund

@app.get("/api/loans/{student_id}")
def get_loan_letters(student_id: str):
    return DatabaseMock.get_loan_letters(student_id)

@app.post("/api/loans/request")
def create_loan_letter(payload: LoanRequestPayload):
    letter = DatabaseMock.create_loan_letter(
        payload.student_id,
        payload.program,
        payload.bank,
        payload.amount
    )
    return letter

@app.get("/downloads/loan-demand-{student_id}.pdf")
def download_loan_demand_letter(student_id: str):
    student = DatabaseMock.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
        
    balance_info = DatabaseMock.get_student_balance(student_id)
    
    # Create PDF in memory
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Draw header
    p.setFont("Helvetica-Bold", 18)
    p.drawString(100, height - 80, "FinVault University Finance Department")
    
    p.setFont("Helvetica", 10)
    p.drawString(100, height - 100, "Official Certified Tuition Fee Demand Letter")
    p.drawString(100, height - 115, f"Date: {datetime.date.today().strftime('%d %B %Y')}")
    
    p.setStrokeColorRGB(0, 0, 0)
    p.setLineWidth(1)
    p.line(100, height - 130, width - 100, height - 130)
    
    # Student details
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, height - 160, "Student details:")
    p.setFont("Helvetica", 11)
    p.drawString(120, height - 180, f"Name: {student['name']}")
    p.drawString(120, height - 195, f"Student ID: {student['id']}")
    p.drawString(120, height - 210, f"Program: {student['program']}")
    p.drawString(120, height - 225, f"Current Semester: Semester {student['semester']}")
    p.drawString(120, height - 240, f"Email: {student['email']}")
    
    # Financial Statement
    p.setFont("Helvetica-Bold", 12)
    p.drawString(100, height - 275, "Fee Structure & Outstanding Balance:")
    
    p.setFont("Helvetica", 11)
    currency = student.get('currency', 'INR')
    p.drawString(120, height - 295, f"Billed Tuition Fees: {currency} {balance_info['billed']:.2f}")
    p.drawString(120, height - 310, f"Scholarship/Waiver: {currency} {balance_info['scholarship']:.2f}")
    p.drawString(120, height - 325, f"Fees Paid: {currency} {balance_info['paid']:.2f}")
    p.drawString(120, height - 340, f"Overdue Late Fees: {currency} {balance_info['late_fees']:.2f}")
    
    p.setFont("Helvetica-Bold", 11)
    p.drawString(120, height - 365, f"Net Outstanding Balance Due: {currency} {balance_info['balance']:.2f}")
    
    # Certification text
    p.setFont("Helvetica-Oblique", 10)
    p.drawString(100, height - 410, "This document is digitally signed and serves as an official certification")
    p.drawString(100, height - 425, "for bank educational loan disbursement processes.")
    
    p.setStrokeColorRGB(0.5, 0.5, 0.5)
    p.line(100, height - 445, width - 100, height - 445)
    
    # Signature
    p.setFont("Helvetica-Bold", 11)
    p.drawString(100, height - 480, "Registrar (Finance & Accounts)")
    p.drawString(100, height - 495, "FinVault Institute of Technology")
    
    # Add a mock digital signature stamp
    p.setStrokeColorRGB(0.1, 0.5, 0.1)
    p.rect(width - 220, height - 510, 120, 50)
    p.setFillColorRGB(0.1, 0.5, 0.1)
    p.setFont("Helvetica-Bold", 9)
    p.drawString(width - 210, height - 480, "DIGITALLY SIGNED")
    p.setFont("Helvetica", 8)
    p.drawString(width - 210, height - 495, "VERIFIED COMPLIANT")
    p.drawString(width - 210, height - 505, f"ID: {student_id}-AUTH")
    
    # Save the page
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="application/pdf", headers={
        "Content-Disposition": f"inline; filename=loan-demand-{student_id}.pdf"
    })

@app.get("/api/exceptions")
def get_reconciliation_exceptions():
    return DatabaseMock.get_exceptions()

@app.post("/api/reconcile/run/{student_id}")
def run_reconciliation(student_id: str):
    # Simulate reconciliation trigger
    exceptions = DatabaseMock.get_exceptions()
    my_exc = [e for e in exceptions if e["student_id"] == student_id and e["status"] == "UNMATCHED"]
    
    if not my_exc:
        return {"reconciled": False, "message": "No unmatched transactions found for sync"}
        
    exc = my_exc[0]
    
    # Add transaction
    new_txn = {
        "txn_id": exc["txn_id"],
        "student_id": student_id,
        "date": "19 May 2026",
        "category": "Tuition Fee Sem 7 (Reconciled)",
        "amount": exc["expected"],
        "method": exc["source"],
        "status": "APPROVED"
    }
    DatabaseMock.add_transaction(new_txn)
    
    # Update student record
    student = DatabaseMock.get_student(student_id)
    if student:
        student["paid_amount"] += exc["expected"]
        
    # Mark resolved
    exc["status"] = "RECONCILED"
    
    return {
        "reconciled": True,
        "transaction_id": exc["txn_id"],
        "amount": exc["expected"],
        "message": f"Successfully synchronized transaction {exc['txn_id']} with the ERP."
    }

@app.get("/api/approvals")
def get_pending_approvals():
    return DatabaseMock.get_approvals()

@app.post("/api/approvals/{approval_id}/action")
def take_approval_action(approval_id: str, payload: ApprovalActionPayload):
    success = DatabaseMock.process_approval(approval_id, payload.action, payload.officer)
    if not success:
        raise HTTPException(status_code=404, detail="Approval task not found or already processed")
    return {"success": True, "message": f"Task {approval_id} has been {payload.action}ed."}

class OfficerChatRequest(BaseModel):
    officer_id: str
    message: str
    history: List[Dict[str, str]] = []

@app.post("/api/officer/chat")
def officer_chat(payload: OfficerChatRequest):
    """Finance Officer AI Intelligence endpoint — admin-scoped queries."""
    result = orchestrator.process_officer_query(
        officer_id=payload.officer_id,
        query=payload.message,
        history=payload.history
    )
    return result

@app.post("/api/chat")
def chat_with_agent(payload: ChatRequest):
    # Run orchestrator DAG workflow
    result = orchestrator.process_query(
        student_id=payload.student_id,
        query=payload.message,
        history=payload.history
    )
    return result

@app.get("/api/kafka/events")
def get_kafka_events():
    """Exposes real-time event logs for the dashboard telemetry visualizer"""
    return DatabaseMock.get_kafka_events()

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    
    # Read port from env, default to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
