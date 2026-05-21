# grafana_dashboard.py - Grafana Dashboard Configuration Generator for FinVault
# Generates Grafana-compatible JSON dashboard definitions for financial monitoring.

import json
from typing import Dict, Any

def _make_panel(title: str, panel_id: int, expr: str, unit: str = "short", panel_type: str = "stat", x: int = 0, y: int = 0) -> Dict[str, Any]:
    """Helper to generate a Grafana panel definition."""
    return {
        "id": panel_id,
        "title": title,
        "type": panel_type,
        "gridPos": {"x": x, "y": y, "w": 6, "h": 4},
        "targets": [{"expr": expr, "legendFormat": title}],
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "color": {"mode": "thresholds"},
                "thresholds": {
                    "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 0.8},
                        {"color": "red", "value": 0.95}
                    ]
                }
            }
        },
        "options": {"reduceOptions": {"calcs": ["lastNotNull"]}}
    }

def generate_finvault_dashboard() -> Dict[str, Any]:
    """
    Generates the main FinVault Grafana dashboard JSON definition.
    Import this into Grafana via Dashboard > Import JSON.
    """
    return {
        "uid": "finvault-main-v1",
        "title": "FinVault — Student Finance Intelligence Platform",
        "description": "Real-time monitoring: AI agents, payment pipeline, refund SLA, Kafka events",
        "tags": ["finvault", "finance", "ai", "kafka"],
        "timezone": "Asia/Kolkata",
        "refresh": "10s",
        "time": {"from": "now-6h", "to": "now"},
        "panels": [
            _make_panel("Active Students Online",    1, 'finvault_active_sessions_total',          unit="none",   panel_type="stat", x=0,  y=0),
            _make_panel("AI Requests / min",         2, 'rate(finvault_ai_requests_total[1m])',      unit="reqps",  panel_type="stat", x=6,  y=0),
            _make_panel("Kafka Events / min",         3, 'rate(finvault_kafka_events_total[1m])',    unit="reqps",  panel_type="stat", x=12, y=0),
            _make_panel("Pending Approvals",          4, 'finvault_approvals_pending_total',         unit="none",   panel_type="stat", x=18, y=0),
            _make_panel("AI Orchestrator P95 Latency", 5, 'histogram_quantile(0.95, finvault_ai_latency_seconds_bucket)', unit="s", panel_type="gauge", x=0, y=4),
            _make_panel("Payment Processing SLA",    6, 'finvault_payment_sla_compliance_ratio',    unit="percentunit", panel_type="gauge", x=6,  y=4),
            _make_panel("Refund SLA Compliance",     7, 'finvault_refund_sla_compliance_ratio',     unit="percentunit", panel_type="gauge", x=12, y=4),
            _make_panel("Unmatched Exceptions",      8, 'finvault_reconciliation_exceptions_open',  unit="none",   panel_type="stat", x=18, y=4),
            {
                "id": 9,
                "title": "AI Agent Response Times (Time Series)",
                "type": "timeseries",
                "gridPos": {"x": 0, "y": 8, "w": 24, "h": 8},
                "targets": [
                    {"expr": "finvault_ai_agent_duration_seconds{agent='root_orchestrator'}", "legendFormat": "Root Orchestrator"},
                    {"expr": "finvault_ai_agent_duration_seconds{agent='faq_agent'}", "legendFormat": "FAQ Agent"},
                    {"expr": "finvault_ai_agent_duration_seconds{agent='refund_agent'}", "legendFormat": "Refund Agent"},
                    {"expr": "finvault_ai_agent_duration_seconds{agent='payment_agent'}", "legendFormat": "Payment Agent"},
                ],
                "fieldConfig": {"defaults": {"unit": "s"}}
            },
            {
                "id": 10,
                "title": "Kafka Topic Event Rate",
                "type": "barchart",
                "gridPos": {"x": 0, "y": 16, "w": 12, "h": 6},
                "targets": [
                    {"expr": "rate(finvault_kafka_events_total[5m]) by (topic)", "legendFormat": "{{topic}}"}
                ],
                "fieldConfig": {"defaults": {"unit": "reqps"}}
            },
            {
                "id": 11,
                "title": "Security Events Log",
                "type": "logs",
                "gridPos": {"x": 12, "y": 16, "w": 12, "h": 6},
                "targets": [
                    {"expr": '{app="finvault",level="SECURITY"}', "legendFormat": "Security Events"}
                ]
            }
        ],
        "schemaVersion": 38,
        "version": 1,
        "links": [
            {"title": "FinVault API", "url": "http://localhost:8000/docs", "type": "link"},
            {"title": "Kafka UI", "url": "http://localhost:9000", "type": "link"}
        ]
    }

if __name__ == "__main__":
    dashboard = generate_finvault_dashboard()
    with open("finvault_dashboard.json", "w") as f:
        json.dump(dashboard, f, indent=2)
    print("Grafana dashboard JSON exported to finvault_dashboard.json")
    print(f"Total panels: {len(dashboard['panels'])}")
