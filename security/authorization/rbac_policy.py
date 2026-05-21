# rbac_policy.py - Role-Based & Attribute-Based Access Control for FinVault
# Enforces permission policies for student and finance officer roles

from typing import Dict, List, Any, Optional

# Role Permission Definitions
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    "student": [
        "read:own_ledger",
        "read:own_transactions",
        "read:own_refunds",
        "write:refund_request",
        "read:own_loans",
        "write:loan_request",
        "read:international_info",
        "write:chat_student",
    ],
    "finance_officer": [
        "read:all_students",
        "read:all_transactions",
        "read:all_refunds",
        "write:approve_refund",
        "write:reject_refund",
        "read:reconciliation_exceptions",
        "write:reconcile_exception",
        "read:approval_queue",
        "write:process_approval",
        "read:kafka_audit_logs",
        "read:analytics",
        "write:chat_officer",
        "write:escalation_override",
    ],
    "system_admin": [
        "*"  # Full access
    ]
}

# Resource-level Attribute-Based Access Control rules
ABAC_RULES: Dict[str, Any] = {
    "high_value_refund_threshold": 100000.00,    # Requires finance_officer approval
    "officer_only_endpoints": [
        "/api/officer/chat",
        "/api/approvals",
        "/api/exceptions",
        "/api/kafka/events",
        "/api/reconcile/run"
    ],
    "student_restricted_endpoints": [
        "/api/student/{student_id}",
        "/api/transactions/{student_id}",
        "/api/refunds/{student_id}",
        "/api/loans/{student_id}",
        "/api/chat",
        "/api/refunds/request",
        "/api/loans/request",
    ]
}

class RBACService:
    """Enforces Role-Based and Attribute-Based Access Control."""

    @staticmethod
    def has_permission(role: str, permission: str) -> bool:
        """Check if a role has a specific permission."""
        perms = ROLE_PERMISSIONS.get(role, [])
        return "*" in perms or permission in perms

    @staticmethod
    def authorize_endpoint(role: str, endpoint: str) -> bool:
        """Check if a role is allowed to access a given endpoint."""
        if role == "system_admin":
            return True
        officer_only = ABAC_RULES["officer_only_endpoints"]
        student_restricted = ABAC_RULES["student_restricted_endpoints"]
        
        for pattern in officer_only:
            # Simple prefix/pattern matching
            base = pattern.split("{")[0].rstrip("/")
            if endpoint.startswith(base):
                return role == "finance_officer"
        return True  # Default allow for student-accessible endpoints

    @staticmethod
    def requires_officer_approval(amount: float) -> bool:
        """Returns True if the refund amount requires Finance Officer authorization."""
        return amount > ABAC_RULES["high_value_refund_threshold"]

    @staticmethod
    def get_role_permissions(role: str) -> List[str]:
        return ROLE_PERMISSIONS.get(role, [])

    @staticmethod
    def audit_access(user_id: str, role: str, endpoint: str, allowed: bool):
        """Log access control decisions for compliance audit trail."""
        verdict = "GRANTED" if allowed else "DENIED"
        print(f"[RBAC AUDIT] User={user_id} Role={role} Endpoint={endpoint} -> {verdict}")
