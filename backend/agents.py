import sys
import os

# Get absolute path to the project root directory
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Add each agent subfolder to sys.path to allow clean imports from hyphenated directory paths
sys.path.append(os.path.join(root_dir, "agents", "faq-agent"))
sys.path.append(os.path.join(root_dir, "agents", "payment-guidance-agent"))
sys.path.append(os.path.join(root_dir, "agents", "refund-tracking-agent"))
sys.path.append(os.path.join(root_dir, "agents", "loan-demand-letter-agent"))
sys.path.append(os.path.join(root_dir, "agents", "international-finance-agent"))
sys.path.append(os.path.join(root_dir, "agents", "reconciliation-agent"))
sys.path.append(os.path.join(root_dir, "agents", "escalation-agent"))
sys.path.append(os.path.join(root_dir, "agents", "notification-agent"))
sys.path.append(os.path.join(root_dir, "agents", "root-orchestrator-agent"))

# Import child agents from their modular files
from faq_agent import FAQAgent
from payment_guidance_agent import PaymentGuidanceAgent
from refund_tracking_agent import RefundTrackingAgent
from loan_demand_letter_agent import LoanDemandLetterAgent
from international_finance_agent import InternationalFinanceAgent
from reconciliation_agent import ReconciliationAgent
from escalation_agent import EscalationAgent
from notification_agent import NotificationAgent
from root_orchestrator import RootOrchestratorAgent
