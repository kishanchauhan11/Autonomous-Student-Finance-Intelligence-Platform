import os
import json
import sys
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from nvidia_client import NvidiaClient
from typing import List, Dict, Any

# Adjust paths to import rag-system modules
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(root_dir, "rag-system", "embeddings"))
sys.path.insert(0, os.path.join(root_dir, "rag-system", "vector-search"))
sys.path.insert(0, os.path.join(root_dir, "rag-system", "reranking"))
sys.path.insert(0, os.path.join(root_dir, "rag-system", "ingestion-pipeline"))
sys.path.insert(0, os.path.join(root_dir, "rag-system", "retrieval-pipeline"))

from nvidia_embeddings import NvidiaEmbeddingService  # type: ignore
from qdrant_service import QdrantService  # type: ignore
from nvidia_reranker import NvidiaRerankerService  # type: ignore
from document_ingester import DocumentIngester  # type: ignore
from semantic_retriever import SemanticRetriever  # type: ignore

# University Policy Documents
UNIVERSITY_POLICIES = [
    {
        "id": "faq-1",
        "category": "fees",
        "title": "Tuition Fee Payment Methods",
        "text": "Students can pay their tuition fees using three official methods: online via the Student Portal (Credit Card, Net Banking, UPI), via bank transfer (NEFT/RTGS), or through foreign currency SWIFT transfers for international students. Cash payments are not accepted at the accounts office. All online payments through the portal are processed via Razorpay or Stripe gateways and sync with the ERP within 15 minutes."
    },
    {
        "id": "faq-2",
        "category": "fees",
        "title": "Late Fees and Penalties",
        "text": "The deadline for semester tuition fees is the 10th day after classes commence. A grace period of 5 days is allowed. Payments received after the 15th day are subject to a late fee of ₹500 per day. If fees remain unpaid 30 days past the due date, library access and student portal services will be temporarily suspended, and the account will be escalated for manual review by the Finance Officer."
    },
    {
        "id": "refund-1",
        "category": "refunds",
        "title": "Refund Policy and Eligibility",
        "text": "Refund requests are subject to the following rules: 100% refund is eligible if a student withdraws from the course before the semester commencement date. 80% refund is eligible within the first week of classes. 50% refund is eligible between 8 and 15 days of classes. No refunds are granted after 15 days. All refunds must be approved by the Finance Officer. High-value refunds exceeding ₹1,00,000 require secondary approval from the Director of Student Finance."
    },
    {
        "id": "refund-2",
        "category": "refunds",
        "title": "Refund Processing Stages",
        "text": "Once submitted, refunds pass through five sequential stages: 1. Submitted (Initial request logged), 2. Verification (Documents checked by Accounts), 3. Accounts Approval (Approved by Finance Officer), 4. Finance Processing (ERP sync and payment queueing), and 5. Payment Released (Credited to student's verified bank account). The standard SLA for refund processing is 10 to 15 working days. If a refund is delayed more than 15 days, it triggers automatic escalation to a high-priority ticket."
    },
    {
        "id": "loan-1",
        "category": "loans",
        "title": "Loan Demand Letters and Estimates",
        "text": "Students requesting a Loan Demand Letter for bank education loans can choose three formats: Current Semester, Next Semester, or Full Academic Year. The letter is generated using official ERP financial details and includes a complete breakdown of tuition fees, lab fees, library charges, and hostel accommodation (if applicable). It features a secure digital signature from the Registrar and a QR code verification link. Letters are generated dynamically as PDFs and are valid for 90 days from issuance."
    },
    {
        "id": "intl-1",
        "category": "international",
        "title": "International Students SWIFT Transfer Guidelines",
        "text": "International students must pay fees in foreign currency equivalent to the Indian Rupee (INR) amount billed. Recommended channels are Flywire, Western Union Business Solutions, or direct SWIFT bank transfer. For direct SWIFT transfers, use the following bank credentials: Bank Name: Institutional Trust Bank, Branch: University Campus, SWIFT Code: ITB1NDIA33B, Account Number: 9876543210. Always quote the Student ID (e.g. STU-2021-4892) in the transaction reference field to ensure automatic reconciliation. A 2.5% forex processing fee is applicable on international payments."
    },
    {
        "id": "reconcile-1",
        "category": "reconciliation",
        "title": "Payment Sync and Reconciliation Issues",
        "text": "If a payment is successfully debited from the student's bank account but does not reflect on the Student Dashboard, it is designated as a synchronization exception. This occurs due to webhooks failing between the gateway and ERP. The student must upload their payment receipt or bank transaction statement. The Reconciliation Agent validates the transaction ID against gateway reports, updates the ERP, and updates the student dashboard. Automatic reconciliations are run daily at 23:59 PM."
    },
    {
        "id": "scholarship-1",
        "category": "scholarships",
        "title": "Scholarship Fee Adjustments",
        "text": "Merit scholarships (up to 50% waiver), sports scholarships (up to 30% waiver), and financial aid waivers (based on family income) are applied directly to the student ledger before the fee invoice is generated. Any mid-semester scholarship modifications or overrides must be processed by the Accounts Office. Scholarship adjustments reduce the total payable amount but do not refund past semesters unless explicitly approved by the Director of Student Finance."
    }
]

class RagEngine:
    def __init__(self, nv_client: NvidiaClient):
        self.nv_client = nv_client
        # Instantiate modular RAG services
        self.qdrant_service = QdrantService(collection_name="university_finance", vector_dim=2048)
        self.embedding_service = NvidiaEmbeddingService(nv_client)
        self.reranker_service = NvidiaRerankerService(nv_client)
        self.ingester = DocumentIngester(self.qdrant_service, self.embedding_service, UNIVERSITY_POLICIES)
        self.retriever = SemanticRetriever(self.qdrant_service, self.embedding_service, self.reranker_service)
        
        self.ingest_documents()

    def ingest_documents(self):
        json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "rag-system", "knowledge-base", "university_policies.json"))
        self.ingester.ingest(json_path)

    def retrieve_context(self, query: str, top_k: int = 4) -> str:
        return self.retriever.retrieve(query, top_k=top_k)

if __name__ == "__main__":
    nv_client = NvidiaClient()
    rag = RagEngine(nv_client)
    
    # Test retrieval
    test_query = "What happens if my refund is delayed?"
    context = rag.retrieve_context(test_query, top_k=2)
    print("\n--- Retrieved Context ---")
    print(context)
