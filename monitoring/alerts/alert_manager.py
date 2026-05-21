# alert_manager.py - Alert & Incident Management for FinVault
# Defines alert rules, severity levels, and notification dispatch (PagerDuty, Slack, email).

import datetime
from typing import Dict, Any, List, Optional

# Alert severity definitions
SEVERITY_LEVELS = {
    "P1": {"label": "CRITICAL",  "sla_minutes": 15,   "notify": ["pagerduty", "slack", "email"]},
    "P2": {"label": "HIGH",      "sla_minutes": 60,   "notify": ["slack", "email"]},
    "P3": {"label": "MEDIUM",    "sla_minutes": 240,  "notify": ["slack"]},
    "P4": {"label": "LOW",       "sla_minutes": 1440, "notify": ["email"]}
}

# Alert Rule Registry
ALERT_RULES: List[Dict[str, Any]] = [
    {
        "name": "AIAgentDown",
        "condition": "finvault_ai_agent_up == 0",
        "severity": "P1",
        "description": "AI orchestrator is unreachable. All student chat queries are failing.",
        "runbook": "https://docs.finvault.internal/runbooks/ai-agent-down"
    },
    {
        "name": "HighAILatency",
        "condition": "finvault_ai_latency_seconds{quantile='0.95'} > 10",
        "severity": "P2",
        "description": "AI agent P95 response latency exceeds 10 seconds. Student experience degraded.",
        "runbook": "https://docs.finvault.internal/runbooks/high-latency"
    },
    {
        "name": "KafkaTopicLag",
        "condition": "finvault_kafka_consumer_lag > 1000",
        "severity": "P2",
        "description": "Kafka consumer lag is high. Event processing pipeline is behind.",
        "runbook": "https://docs.finvault.internal/runbooks/kafka-lag"
    },
    {
        "name": "HighPendingApprovals",
        "condition": "finvault_approvals_pending_total > 20",
        "severity": "P3",
        "description": "Pending approval queue has more than 20 items. Finance Officers need to action.",
        "runbook": "https://docs.finvault.internal/runbooks/approval-queue"
    },
    {
        "name": "ReconciliationExceptionsSpike",
        "condition": "finvault_reconciliation_exceptions_open > 5",
        "severity": "P2",
        "description": "More than 5 unresolved reconciliation exceptions. ERP sync may be failing.",
        "runbook": "https://docs.finvault.internal/runbooks/reconciliation-exceptions"
    },
    {
        "name": "SecurityEventDetected",
        "condition": "rate(finvault_security_events_total[5m]) > 0",
        "severity": "P1",
        "description": "Security guardrails have detected prompt injection or blocked topics.",
        "runbook": "https://docs.finvault.internal/runbooks/security-incident"
    },
    {
        "name": "BackendErrorRateHigh",
        "condition": "rate(http_requests_total{status=~'5..'} [5m]) > 0.05",
        "severity": "P2",
        "description": "FastAPI backend 5xx error rate exceeds 5%. Possible service failure.",
        "runbook": "https://docs.finvault.internal/runbooks/backend-errors"
    }
]

# Active incident registry
_ACTIVE_INCIDENTS: List[Dict[str, Any]] = []

class AlertManager:
    """
    Alert rule evaluator and incident dispatch system for FinVault.
    Integrates with Prometheus Alertmanager, PagerDuty, and Slack.
    """

    @staticmethod
    def fire_alert(rule_name: str, severity: str, description: str,
                   value: Optional[float] = None) -> Dict[str, Any]:
        """
        Fires an alert and creates an incident record.
        In production: POST to Alertmanager /api/v2/alerts endpoint.
        """
        level = SEVERITY_LEVELS.get(severity, SEVERITY_LEVELS["P3"])
        incident_id = f"INC-{len(_ACTIVE_INCIDENTS) + 1001}"
        
        incident = {
            "incident_id": incident_id,
            "alert_name": rule_name,
            "severity": severity,
            "severity_label": level["label"],
            "description": description,
            "current_value": value,
            "fired_at": datetime.datetime.utcnow().isoformat() + "Z",
            "sla_minutes": level["sla_minutes"],
            "status": "FIRING",
            "notify_channels": level["notify"]
        }
        _ACTIVE_INCIDENTS.append(incident)
        
        print(f"[ALERT {severity}] {incident_id}: {rule_name} — {description}")
        AlertManager._dispatch_notifications(incident)
        return incident

    @staticmethod
    def resolve_alert(incident_id: str) -> bool:
        """Marks an incident as resolved."""
        for inc in _ACTIVE_INCIDENTS:
            if inc["incident_id"] == incident_id and inc["status"] == "FIRING":
                inc["status"] = "RESOLVED"
                inc["resolved_at"] = datetime.datetime.utcnow().isoformat() + "Z"
                print(f"[ALERT RESOLVED] {incident_id}")
                return True
        return False

    @staticmethod
    def _dispatch_notifications(incident: Dict[str, Any]):
        """Simulates dispatching notifications to configured channels."""
        channels = incident.get("notify_channels", [])
        for channel in channels:
            if channel == "pagerduty":
                print(f"  → PagerDuty: Paging on-call engineer for {incident['incident_id']}")
            elif channel == "slack":
                print(f"  → Slack #finvault-alerts: [{incident['severity']}] {incident['alert_name']}: {incident['description'][:80]}")
            elif channel == "email":
                print(f"  → Email: Sending alert email for {incident['incident_id']}")

    @staticmethod
    def evaluate_metric(metric_name: str, value: float) -> Optional[Dict[str, Any]]:
        """
        Checks a metric value against all matching alert rules.
        Returns fired incident or None.
        """
        trigger_map = {
            "finvault_ai_agent_up": ("AIAgentDown", "P1", value == 0),
            "finvault_approvals_pending_total": ("HighPendingApprovals", "P3", value > 20),
            "finvault_reconciliation_exceptions_open": ("ReconciliationExceptionsSpike", "P2", value > 5),
        }
        
        if metric_name in trigger_map:
            name, severity, should_fire = trigger_map[metric_name]
            if should_fire:
                rule = next((r for r in ALERT_RULES if r["name"] == name), {})
                return AlertManager.fire_alert(name, severity, rule.get("description", ""), value)
        return None

    @staticmethod
    def get_active_incidents() -> List[Dict[str, Any]]:
        return [i for i in _ACTIVE_INCIDENTS if i["status"] == "FIRING"]

    @staticmethod
    def get_all_alert_rules() -> List[Dict[str, Any]]:
        return ALERT_RULES
