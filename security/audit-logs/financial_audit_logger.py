# financial_audit_logger.py - Immutable Financial Audit Log Service for FinVault
# Logs every financial action with tamper-evident HMAC signatures for regulatory compliance.

import datetime
import hashlib
import hmac
import json
import os
from typing import Dict, Any, List

# Append-only in-memory audit log (in production: append to WORM storage / Elasticsearch)
_AUDIT_LOG: List[Dict[str, Any]] = []
_HMAC_KEY = os.getenv("FINVAULT_AUDIT_HMAC_KEY", "finvault-audit-key-2026").encode()

def _sign_entry(entry: Dict[str, Any]) -> str:
    """Generates tamper-evident HMAC-SHA256 digest for an audit entry."""
    payload = json.dumps(entry, sort_keys=True, default=str)
    return hmac.new(_HMAC_KEY, payload.encode(), hashlib.sha256).hexdigest()

class FinancialAuditLogger:
    """
    Immutable audit logging for all financial events in FinVault.
    Compliant with:
    - PCI-DSS Requirement 10 (Audit Trail)
    - ISO 27001 A.12.4 (Logging & Monitoring)
    - RBI IT Framework for Banks (India)
    """

    @staticmethod
    def log(
        event_type: str,
        actor_id: str,
        actor_role: str,
        target_id: str,
        action: str,
        amount: float = 0.0,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Records an immutable audit entry.
        
        Args:
            event_type: Category (PAYMENT, REFUND, APPROVAL, LOGIN, ESCALATION, AI_QUERY)
            actor_id:   Who performed the action (student ID or officer ID)
            actor_role: Role of the actor (student | finance_officer)
            target_id:  Subject of action (student ID, approval ID, etc.)
            action:     What was done (CREATED, APPROVED, REJECTED, PAID, LOGIN_SUCCESS)
            amount:     Financial amount involved (0 if not applicable)
            metadata:   Additional context dict
        """
        entry = {
            "seq": len(_AUDIT_LOG) + 1,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "event_type": event_type,
            "actor_id": actor_id,
            "actor_role": actor_role,
            "target_id": target_id,
            "action": action,
            "amount": amount,
            "metadata": metadata or {},
            "compliance_status": "COMPLIANT"
        }
        entry["integrity_hash"] = _sign_entry(entry)
        _AUDIT_LOG.append(entry)

        log_line = (
            f"[AUDIT] #{entry['seq']} | {entry['event_type']} | "
            f"Actor: {actor_id} ({actor_role}) | Target: {target_id} | "
            f"Action: {action} | Amount: {amount:.2f} | Hash: {entry['integrity_hash'][:16]}..."
        ).encode("ascii", errors="replace").decode("ascii")
        print(log_line)
        return entry

    @staticmethod
    def verify_log_integrity() -> Dict[str, Any]:
        """Verifies that no audit entries have been tampered with."""
        violations = []
        for entry in _AUDIT_LOG:
            stored_hash = entry.get("integrity_hash", "")
            check_entry = {k: v for k, v in entry.items() if k != "integrity_hash"}
            expected_hash = _sign_entry(check_entry)
            if not hmac.compare_digest(stored_hash, expected_hash):
                violations.append(entry["seq"])
        
        return {
            "total_entries": len(_AUDIT_LOG),
            "verified": len(violations) == 0,
            "tampered_sequences": violations
        }

    @staticmethod
    def get_logs(event_type: str = None, actor_id: str = None) -> List[Dict[str, Any]]:
        """Retrieves audit log entries with optional filters."""
        logs = _AUDIT_LOG
        if event_type:
            logs = [e for e in logs if e["event_type"] == event_type]
        if actor_id:
            logs = [e for e in logs if e["actor_id"] == actor_id]
        return logs

    @staticmethod
    def export_compliance_report() -> Dict[str, Any]:
        """Generates a summary compliance report for regulatory submission."""
        payment_count = len([e for e in _AUDIT_LOG if e["event_type"] == "PAYMENT"])
        refund_count = len([e for e in _AUDIT_LOG if e["event_type"] == "REFUND"])
        approval_count = len([e for e in _AUDIT_LOG if e["event_type"] == "APPROVAL"])
        integrity = FinancialAuditLogger.verify_log_integrity()
        
        return {
            "report_generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "total_audit_events": len(_AUDIT_LOG),
            "payment_events": payment_count,
            "refund_events": refund_count,
            "approval_events": approval_count,
            "log_integrity_verified": integrity["verified"],
            "tampered_entries": integrity["tampered_sequences"],
            "compliance_frameworks": ["PCI-DSS v4.0", "ISO 27001", "RBI IT Framework"]
        }
