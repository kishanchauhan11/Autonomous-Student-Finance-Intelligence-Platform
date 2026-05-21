# prometheus_metrics.py - Prometheus Metrics Registry for FinVault
# Defines and exposes all platform observability metrics via Prometheus client.

import time
from typing import Dict, Any

# ──────────────────────────────────────────────────────────────────────────────
# In-memory metric store (mirrors Prometheus Counter/Gauge/Histogram semantics)
# In production: use `prometheus_client` library and expose /metrics endpoint
# ──────────────────────────────────────────────────────────────────────────────

_METRICS: Dict[str, Any] = {
    # Counters
    "finvault_ai_requests_total": 0,
    "finvault_kafka_events_total": {},          # keyed by topic
    "finvault_payment_transactions_total": 0,
    "finvault_refund_requests_total": 0,
    "finvault_loan_letters_total": 0,
    "finvault_approval_actions_total": {},      # keyed by action (APPROVE/REJECT)
    "finvault_security_events_total": {},       # keyed by event_type
    
    # Gauges
    "finvault_active_sessions_total": 0,
    "finvault_approvals_pending_total": 0,
    "finvault_reconciliation_exceptions_open": 0,
    "finvault_ai_agent_up": 1,                 # 1=healthy, 0=degraded
    
    # Histograms (stored as lists of durations)
    "finvault_ai_latency_seconds": [],
    "finvault_agent_latency": {},              # keyed by agent name
    "finvault_payment_sla_compliance_ratio": 1.0,
    "finvault_refund_sla_compliance_ratio": 1.0,
}

class PrometheusMetrics:
    """
    FinVault Prometheus metrics registry.
    Exposes platform KPIs for Grafana dashboarding and alerting.
    """

    @staticmethod
    def increment_ai_requests():
        _METRICS["finvault_ai_requests_total"] += 1

    @staticmethod
    def record_kafka_event(topic: str):
        _METRICS["finvault_kafka_events_total"][topic] = (
            _METRICS["finvault_kafka_events_total"].get(topic, 0) + 1
        )

    @staticmethod
    def record_ai_latency(duration_seconds: float, agent: str = "root_orchestrator"):
        _METRICS["finvault_ai_latency_seconds"].append(duration_seconds)
        if agent not in _METRICS["finvault_agent_latency"]:
            _METRICS["finvault_agent_latency"][agent] = []
        _METRICS["finvault_agent_latency"][agent].append(duration_seconds)

    @staticmethod
    def set_pending_approvals(count: int):
        _METRICS["finvault_approvals_pending_total"] = count

    @staticmethod
    def set_open_exceptions(count: int):
        _METRICS["finvault_reconciliation_exceptions_open"] = count

    @staticmethod
    def increment_payment():
        _METRICS["finvault_payment_transactions_total"] += 1

    @staticmethod
    def increment_refund():
        _METRICS["finvault_refund_requests_total"] += 1

    @staticmethod
    def record_security_event(event_type: str):
        _METRICS["finvault_security_events_total"][event_type] = (
            _METRICS["finvault_security_events_total"].get(event_type, 0) + 1
        )

    @staticmethod
    def set_agent_health(healthy: bool):
        _METRICS["finvault_ai_agent_up"] = 1 if healthy else 0

    @staticmethod
    def get_percentile(values: list, p: float) -> float:
        """Calculates a percentile value from a list of measurements."""
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * p / 100)
        return sorted_vals[min(idx, len(sorted_vals) - 1)]

    @staticmethod
    def export_metrics_text() -> str:
        """
        Exports metrics in Prometheus text exposition format (for /metrics endpoint).
        In production: use prometheus_client's generate_latest().
        """
        lines = [
            "# HELP finvault_ai_requests_total Total AI orchestrator requests",
            "# TYPE finvault_ai_requests_total counter",
            f"finvault_ai_requests_total {_METRICS['finvault_ai_requests_total']}",
            "",
            "# HELP finvault_approvals_pending_total Current pending approval tasks",
            "# TYPE finvault_approvals_pending_total gauge",
            f"finvault_approvals_pending_total {_METRICS['finvault_approvals_pending_total']}",
            "",
            "# HELP finvault_reconciliation_exceptions_open Open reconciliation exceptions",
            "# TYPE finvault_reconciliation_exceptions_open gauge",
            f"finvault_reconciliation_exceptions_open {_METRICS['finvault_reconciliation_exceptions_open']}",
            "",
            "# HELP finvault_ai_agent_up AI orchestrator health (1=up, 0=down)",
            "# TYPE finvault_ai_agent_up gauge",
            f"finvault_ai_agent_up {_METRICS['finvault_ai_agent_up']}",
        ]
        
        latencies = _METRICS["finvault_ai_latency_seconds"]
        if latencies:
            p50 = PrometheusMetrics.get_percentile(latencies, 50)
            p95 = PrometheusMetrics.get_percentile(latencies, 95)
            p99 = PrometheusMetrics.get_percentile(latencies, 99)
            lines += [
                "",
                "# HELP finvault_ai_latency_seconds AI orchestrator latency",
                "# TYPE finvault_ai_latency_seconds summary",
                f'finvault_ai_latency_seconds{{quantile="0.5"}} {p50:.4f}',
                f'finvault_ai_latency_seconds{{quantile="0.95"}} {p95:.4f}',
                f'finvault_ai_latency_seconds{{quantile="0.99"}} {p99:.4f}',
                f"finvault_ai_latency_seconds_count {len(latencies)}",
            ]

        for topic, count in _METRICS["finvault_kafka_events_total"].items():
            lines.append(f'finvault_kafka_events_total{{topic="{topic}"}} {count}')

        return "\n".join(lines)

    @staticmethod
    def get_summary() -> Dict[str, Any]:
        latencies = _METRICS["finvault_ai_latency_seconds"]
        return {
            "ai_requests_total": _METRICS["finvault_ai_requests_total"],
            "payment_transactions": _METRICS["finvault_payment_transactions_total"],
            "refund_requests": _METRICS["finvault_refund_requests_total"],
            "pending_approvals": _METRICS["finvault_approvals_pending_total"],
            "open_exceptions": _METRICS["finvault_reconciliation_exceptions_open"],
            "ai_agent_healthy": bool(_METRICS["finvault_ai_agent_up"]),
            "ai_p95_latency_s": PrometheusMetrics.get_percentile(latencies, 95),
            "kafka_events_by_topic": _METRICS["finvault_kafka_events_total"]
        }
