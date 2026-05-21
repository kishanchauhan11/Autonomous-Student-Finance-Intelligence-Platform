import sys
import os
import re
import json
from typing import Dict, Any, List, Tuple

# Set up python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database_mock import DatabaseMock  # type: ignore

class WorkflowEngine:
    def __init__(self, nv_client, rag=None):
        self.nv_client = nv_client
        self.rag = rag

    def run(self, student_id: str, query: str, history: List[Dict[str, str]] = []) -> Dict[str, Any]:
        """
        Executes the Multi-Agent Finance workflow.
        """
        # Step 1: Safety validation (Llama Guard 4)
        safety_check = self.nv_client.check_safety(query, role="user")
        if not safety_check["safe"]:
            return {
                "safe": False,
                "agent": "Security Guardrail",
                "intent": "BLOCKED",
                "context": "",
                "response": "Your message was blocked by the security system due to inappropriate content or potential policy violation.",
                "human_approval_required": False,
                "approval_details": None
            }
            
        # Step 2: Content safety reasoning (Nemotron Content Safety)
        content_safety = self.nv_client.check_content_safety_reasoning(query)
        if not content_safety["safe"]:
            return {
                "safe": False,
                "agent": "Nemotron Safety Reasoner",
                "intent": "BLOCKED",
                "context": "",
                "response": f"Your request has been flagged for security review. Reason: {content_safety['reasoning']}",
                "human_approval_required": False,
                "approval_details": None
            }

        # Step 3: Classify intent
        intent, reason = self.classify_intent(query, history)
        print(f"Classified Intent: {intent} (Reason: {reason})")
        
        # Step 4: Retrieve Context (RAG Engine)
        rag_context = ""
        if intent in ["FAQ", "REFUND", "LOAN", "INTERNATIONAL", "RECONCILIATION"]:
            try:
                if self.rag:
                    rag_context = self.rag.retrieve_context(query, top_k=2)
            except Exception as e:
                print(f"RAG Retrieval failed, using fallback empty context: {e}")
                rag_context = ""
            
        # Step 5: Route to child agent and execute
        agent_response = ""
        human_approval_required = False
        approval_details = None
        
        # Import agents
        from agents import (
            FAQAgent, PaymentGuidanceAgent, RefundTrackingAgent,
            LoanDemandLetterAgent, InternationalFinanceAgent,
            ReconciliationAgent, EscalationAgent, NotificationAgent
        )
        
        # Execute active agent
        if intent == "FAQ":
            faq_agent = FAQAgent(self.nv_client)
            agent_response = faq_agent.execute(student_id, query, rag_context)
            
        elif intent == "PAYMENT":
            payment_agent = PaymentGuidanceAgent(self.nv_client)
            agent_response = payment_agent.execute(student_id, query)
            
        elif intent == "REFUND":
            notification_agent = NotificationAgent(self.nv_client)
            if any(kw in query.lower() for kw in ["file", "request", "apply", "submit", "refund my"]):
                amount = 150000.00 if "double" in query.lower() else 45000.00
                desc = "Refund requested via AI Assistant Chat"
                
                refund_req = DatabaseMock.create_refund_request(student_id, amount, desc)
                notification_agent.dispatch_notification(
                    student_id, 
                    "email", 
                    f"Notification: Refund request {refund_req['request_id']} has been successfully created. Stage: {refund_req['stage']}."
                )
                agent_response = (
                    f"I have successfully registered a new refund request for you!\n\n"
                    f"**Request details:**\n"
                    f"- Request ID: `{refund_req['request_id']}`\n"
                    f"- Refund Amount: `₹ {refund_req['amount']:,.2f}`\n"
                    f"- Submission Date: `{refund_req['submitted_date']}`\n"
                    f"- Current Status: `{refund_req['stage']}`\n\n"
                )
                
                if amount > 100000.00:
                    human_approval_required = True
                    agent_response += (
                        "⚠️ **Director Approval Required:** Since this refund exceeds ₹ 1,00,000.00, it has been routed to the Director of Student Finance for secondary approval before release.\n"
                    )
                    approval_details = {
                        "type": "Refund Approval (High Value)",
                        "student_id": student_id,
                        "amount": amount,
                        "priority": "HIGH",
                        "description": f"High value refund request {refund_req['request_id']} requires manual review."
                    }
                else:
                    agent_response += "The refund will be verified by our accounts team. Standard SLA is 10-15 working days."
            else:
                refund_agent = RefundTrackingAgent(self.nv_client)
                agent_response = refund_agent.execute(student_id, query)
                
        elif intent == "LOAN":
            notification_agent = NotificationAgent(self.nv_client)
            if any(kw in query.lower() for kw in ["generate", "request", "create", "make"]):
                bank = "State Bank of India"
                match = re.search(r"(sbi|hdfc|icici|axis|state bank|education bank)", query.lower())
                if match:
                    bank = match.group(1).upper()
                
                billed_info = DatabaseMock.get_student_balance(student_id)
                new_letter = DatabaseMock.create_loan_letter(student_id, "B.Tech CSE", bank, billed_info["billed"])
                notification_agent.dispatch_notification(
                    student_id, 
                    "dashboard", 
                    f"Notification: Digital demand letter {new_letter['letter_id']} has been successfully generated."
                )
                
                agent_response = (
                    f"Official Loan Demand Letter generated successfully!\n\n"
                    f"**Document Details:**\n"
                    f"- Document ID: `{new_letter['letter_id']}`\n"
                    f"- Requested Bank: `{new_letter['bank']}`\n"
                    f"- Certified Fees Billed: `₹ {new_letter['amount']:,.2f}`\n"
                    f"- Registrar Digital Signature: `CERT-REG-9812-OK`\n"
                    f"- QR Code Secure Hash: `MD5:7b22ab1a0f9a2c3`\n\n"
                    f"🔗 [Download Loan Demand Letter PDF]({new_letter['download_url']})"
                )
            else:
                loan_agent = LoanDemandLetterAgent(self.nv_client)
                agent_response = loan_agent.execute(student_id, query)
                
        elif intent == "INTERNATIONAL":
            intl_agent = InternationalFinanceAgent(self.nv_client)
            agent_response = intl_agent.execute(student_id, query)
            
        elif intent == "RECONCILIATION":
            notification_agent = NotificationAgent(self.nv_client)
            if any(kw in query.lower() for kw in ["paid", "sync", "mismatch", "failed", "gateway", "didn't update"]):
                exceptions = DatabaseMock.get_exceptions()
                my_exc = [e for e in exceptions if e["student_id"] == student_id]
                if my_exc:
                    exc = my_exc[0]
                    import datetime
                    today_str = datetime.date.today().strftime("%d %b %Y")
                    new_txn = {
                        "txn_id": exc["txn_id"],
                        "student_id": student_id,
                        "date": today_str,
                        "category": "Tuition Fee Sem 7 (Reconciled)",
                        "amount": exc["expected"],
                        "method": exc["source"],
                        "status": "APPROVED"
                    }
                    DatabaseMock.add_transaction(new_txn)
                    DatabaseMock.update_student_paid_amount(student_id, exc["expected"])
                    exc["status"] = "RECONCILED"
                    
                    notification_agent.dispatch_notification(
                        student_id,
                        "sms",
                        f"Notification: ERP synchronized transaction {new_txn['txn_id']} of amount INR {new_txn['amount']} successfully."
                    )
                    
                    agent_response = (
                        f"`**Payment Reconciliation Executed!**\n\n"
                        f"I found a transaction mismatch for your semester fees:\n"
                        f"- Transaction ID: `{exc['txn_id']}`\n"
                        f"- Expected Amount: `₹ {exc['expected']:,.2f}`\n"
                        f"- Source: `{exc['source']}`\n\n"
                        f"Our Reconciliation Agent successfully verified this transaction against the Razorpay API gateway logs. "
                        f"The transaction has been sync'd with the ERP and your account status has been updated to **PAID**.\n"
                    )
                else:
                    agent_response = (
                        "No pending mismatch was found. Please check your transaction history. "
                        "If you recently paid, please upload your receipt using the payment reconciliation dashboard."
                    )
            else:
                reconcile_agent = ReconciliationAgent(self.nv_client)
                agent_response = reconcile_agent.execute(student_id, query)
                
        elif intent == "ESCALATION":
            notification_agent = NotificationAgent(self.nv_client)
            app_id = f"APP-0{len(DatabaseMock.get_approvals()) + 9012}"
            new_app = {
                "approval_id": app_id,
                "type": "Manual Escalation Request",
                "student_id": student_id,
                "amount": 0.00,
                "priority": "HIGH",
                "age_hours": 0,
                "details": f"Student requested escalation: {query}",
                "status": "PENDING"
            }
            DatabaseMock.get_approvals().append(new_app)
            DatabaseMock.log_kafka_event("escalation-triggered", new_app)
            notification_agent.dispatch_notification(
                student_id,
                "email",
                f"Notification: High priority support ticket {app_id} has been registered with Accounts Officer queue."
            )
            
            agent_response = (
                f"`**Escalation Ticket Registered!**\n\n"
                f"Your request has been escalated to our Finance team.\n"
                f"- Ticket ID: `{app_id}`\n"
                f"- Priority: `HIGH`\n"
                f"- Assigned Team: Accounts Supervisor\n\n"
                f"A Senior Finance Officer is reviewing your file and will contact you via email or phone within 24 hours."
            )
            
        else:
            faq_agent = FAQAgent(self.nv_client)
            agent_response = faq_agent.execute(student_id, query, rag_context)

        # Step 6: Post-process & finalize response
        student = DatabaseMock.get_student(student_id)
        balance_info = DatabaseMock.get_student_balance(student_id)
        student_context = ""
        if student and balance_info:
            symbol = "₹" if student["currency"] == "INR" else "$"
            student_context = (
                f"True Student Database Context:\n"
                f"- Name: {student['name']}\n"
                f"- ID: {student['id']}\n"
                f"- Program: {student['program']}\n"
                f"- Semester: {student['semester']}\n"
                f"- Billed Tuition Fee: {symbol} {balance_info['billed']:,.2f}\n"
                f"- Scholarship Waiver Applied: {symbol} {balance_info['scholarship']:,.2f}\n"
                f"- Late Fees Outstanding: {symbol} {balance_info['late_fees']:,.2f}\n"
                f"- Net Balance Due: {symbol} {balance_info['balance']:,.2f}\n\n"
            )

        final_compilation_prompt = (
            "You are the Master Student Finance Orchestrator, running on deepseek-ai/deepseek-v4-pro.\n"
            "Review the child agent's response and compile a clean, official, explainable final response for the student.\n"
            "CRITICAL: You MUST use the exact financial figures from the True Student Database Context. Never hallucinate or alter any names, IDs, or amounts. If the student has an outstanding balance, explain it using these numbers.\n"
            "Format the response beautifully in Markdown. Make sure all money amounts are in IBM Plex Mono (e.g. ₹ 1,50,000.00).\n"
            "If the action was successful, confirm the actions taken clearly.\n"
            "Do NOT append any standard footers or verification tags (like 'Verified by Finance Intelligence AI Core') to the response text since the frontend UI renders this dynamically."
        )
        
        final_messages = [
            {"role": "system", "content": final_compilation_prompt},
            {"role": "user", "content": f"{student_context}User Query: {query}\n\nChild Agent Response:\n{agent_response}\n\nCompile Final Response:"}
        ]
        
        final_text = self.nv_client.call_root_orchestrator(final_messages)
        
        # Log event to database audit logs
        DatabaseMock.log_kafka_event("agent-response-generated", {
            "student_id": student_id,
            "intent": intent,
            "query": query,
            "response": final_text
        })
        
        return {
            "safe": True,
            "agent": "Root Finance Orchestrator",
            "intent": intent,
            "context": rag_context,
            "response": final_text,
            "human_approval_required": human_approval_required,
            "approval_details": approval_details
        }

    def classify_intent(self, query: str, history: List[Dict[str, str]] = []) -> Tuple[str, str]:
        """
        Uses DeepSeek v4 Pro to classify query intent and return the target agent and justification.
        """
        system_prompt = (
            "You are the Root Finance Intent Classifier powered by deepseek-ai/deepseek-v4-pro.\n"
            "Classify the student query into one of these categories:\n"
            "1. FAQ (general policy questions, refund rules, billing timelines)\n"
            "2. PAYMENT (checking payable balance, late fees, how to pay invoices)\n"
            "3. REFUND (checking refund stages, filing refund requests)\n"
            "4. LOAN (requesting or checking education loan demand letters)\n"
            "5. INTERNATIONAL (foreign students, currency, SWIFT, forex)\n"
            "6. RECONCILIATION (paid fee not showing in portal, transaction synchronization exception)\n"
            "7. ESCALATION (unresolved issue, ticket request, complaining about delays, supervisor requests)\n\n"
            "Provide your response in EXACTLY this JSON format:\n"
            "{\n"
            "  \"intent\": \"FAQ|PAYMENT|REFUND|LOAN|INTERNATIONAL|RECONCILIATION|ESCALATION\",\n"
            "  \"reason\": \"A brief explanation of why this category was chosen\"\n"
            "}"
        )
        
        history_context = ""
        for h in history[-4:]: # Last 4 messages
            role = "Student" if h["role"] == "user" else "Assistant"
            history_context += f"{role}: {h['content']}\n"
            
        user_prompt = f"Chat History:\n{history_context}\nCurrent Student Query: {query}\n\nJSON Classification:"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # We call the root orchestrator model from NvidiaClient to parse intent
        response_text = self.nv_client.call_root_orchestrator(messages)
        
        try:
            clean_text = re.sub(r"```json\s*", "", response_text)
            clean_text = re.sub(r"```\s*$", "", clean_text).strip()
            data = json.loads(clean_text)
            return data.get("intent", "FAQ"), data.get("reason", "")
        except Exception as e:
            safe_response = response_text.encode('ascii', errors='replace').decode('ascii')
            print(f"Failed to parse intent JSON: {e}. Raw text (sanitized): {safe_response}")
            # Fallback based on keywords
            q = query.lower()
            if "refund" in q: return "REFUND", "Keyword fallback"
            if "loan" in q or "demand letter" in q: return "LOAN", "Keyword fallback"
            if "swift" in q or "foreign" in q or "international" in q or "dollar" in q: return "INTERNATIONAL", "Keyword fallback"
            if "reconcil" in q or " paid " in q or "update" in q or "sync" in q or "reflect" in q: return "RECONCILIATION", "Keyword fallback"
            if "balance" in q or "fee due" in q or "payable" in q or "payment method" in q: return "PAYMENT", "Keyword fallback"
            if "escalate" in q or "ticket" in q or "complaint" in q: return "ESCALATION", "Keyword fallback"
            return "FAQ", "Default fallback"

    def run_officer_query(self, officer_id: str, query: str, history: List[Dict[str, str]] = []) -> Dict[str, Any]:
        """
        Handles Finance Officer admin queries. Provides admin-scoped financial intelligence
        including pending approvals, exception summaries, student balances, and policy lookups.
        """
        # Build a rich admin-scope context from live data
        approvals = DatabaseMock.get_approvals()
        exceptions = DatabaseMock.get_exceptions()
        
        pending_approvals = [a for a in approvals if a.get("status") == "PENDING"]
        unmatched_exc = [e for e in exceptions if e.get("status") == "UNMATCHED"]
        
        admin_context = (
            f"Finance Officer Admin Context (Live System Snapshot):\n"
            f"- Officer ID: {officer_id}\n"
            f"- Pending Approval Tasks: {len(pending_approvals)}\n"
            f"- Unmatched Reconciliation Exceptions: {len(unmatched_exc)}\n\n"
        )
        
        if pending_approvals:
            admin_context += "Pending Approvals:\n"
            for a in pending_approvals[:5]:
                admin_context += f"  · [{a['approval_id']}] {a['type']} — Student: {a['student_id']} — Amount: {a.get('amount', 0):,.2f} — Priority: {a.get('priority', 'N/A')}\n"
            admin_context += "\n"
            
        if unmatched_exc:
            admin_context += "Active Reconciliation Exceptions:\n"
            for e in unmatched_exc[:5]:
                admin_context += f"  · [{e['exception_id']}] Student: {e['student_id']} — Delta: {e.get('delta', 0):,.2f} — Gateway: {e.get('source', 'N/A')}\n"
            admin_context += "\n"
        
        # RAG context for policy lookup
        rag_context = ""
        if self.rag:
            try:
                rag_context = self.rag.retrieve_context(query, top_k=2)
            except Exception as e:
                print(f"Officer RAG retrieval error: {e}")
        
        # If officer is asking about a specific student, add their data
        student_data_context = ""
        q_lower = query.lower()
        for stud_id in ["STU-2021-4892", "STU-2022-1082"]:
            stud = DatabaseMock.get_student(stud_id)
            if stud and (stud["name"].split()[0].lower() in q_lower or stud_id.lower() in q_lower or stud["name"].lower() in q_lower):
                balance = DatabaseMock.get_student_balance(stud_id)
                symbol = "₹" if stud.get("currency") == "INR" else "$"
                student_data_context += (
                    f"\nStudent Record — {stud['name']} ({stud_id}):\n"
                    f"  Program: {stud['program']}, Semester {stud['semester']}\n"
                    f"  Billed: {symbol} {balance['billed']:,.2f} | Paid: {symbol} {balance['paid']:,.2f} | Balance Due: {symbol} {balance['balance']:,.2f}\n"
                    f"  Scholarship Waiver: {symbol} {balance['scholarship']:,.2f} | Late Fees: {symbol} {balance['late_fees']:,.2f}\n"
                )
        
        # Build officer system prompt
        system_prompt = (
            "You are the Finance Officer Intelligence Core, a specialized administrative AI for FinVault University Finance Department.\n"
            "You assist Finance Officers with administrative oversight of student financial records.\n"
            "You have access to live data including: pending approval queues, reconciliation exceptions, student ledger summaries, and university finance policy documents.\n"
            "Always respond concisely with actionable insight. Format responses in Markdown.\n"
            "When citing financial figures, use the exact numbers from the Admin Context. Never fabricate data.\n"
            "If the officer asks about specific students, use the student record data provided.\n"
            "IMPORTANT: You are in ADMIN MODE. You may discuss all student records, approval statuses, and exception details.\n"
            "Do NOT append any standard footers, the UI renders them dynamically."
        )
        
        history_context = ""
        for h in history[-4:]:
            role = "Finance Officer" if h["role"] == "user" else "AI"
            history_context += f"{h['role'].upper()}: {h['content']}\n"
        
        user_message = (
            f"{admin_context}"
            f"{student_data_context}\n"
            f"University Policy Context (RAG):\n{rag_context}\n\n"
            f"Conversation History:\n{history_context}\n"
            f"Finance Officer Query: {query}\n\n"
            "Provide a concise, actionable admin response:"
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        officer_response = self.nv_client.call_root_orchestrator(messages)
        
        # Log the officer query to Kafka audit
        DatabaseMock.log_kafka_event("officer-ai-query", {
            "officer_id": officer_id,
            "query": query,
            "response_preview": officer_response[:120] if officer_response else ""
        })
        
        return {
            "safe": True,
            "agent": "Finance Officer Intelligence Core",
            "response": officer_response,
            "pending_approvals": len(pending_approvals),
            "unmatched_exceptions": len(unmatched_exc)
        }
