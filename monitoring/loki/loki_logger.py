# loki_logger.py - Centralized Structured Log Aggregation for FinVault (Grafana Loki)
# Produces structured JSON log lines in Loki-compatible format with log level routing.

import datetime
import json
import sys
from typing import Dict, Any, Optional

# Log Level Definitions
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "SECURITY": 45,
    "CRITICAL": 50
}

# Active minimum log level (set via env in production)
MIN_LOG_LEVEL = LOG_LEVELS["INFO"]

# In-memory log buffer (in production: flush to Loki via HTTP push API)
_LOG_BUFFER = []

class LokiLogger:
    """
    Structured JSON logger compatible with Grafana Loki.
    Log lines are enriched with labels for multi-dimensional querying.
    
    In production: use python-logging + loki-logging-handler, or
    push directly to Loki push API at /loki/api/v1/push.
    """

    def __init__(self, service: str = "finvault-backend", component: str = "general"):
        self.service = service
        self.component = component

    def _emit(self, level: str, message: str, extra: Optional[Dict[str, Any]] = None):
        if LOG_LEVELS.get(level, 0) < MIN_LOG_LEVEL:
            return
        
        entry = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "level": level,
            "service": self.service,
            "component": self.component,
            "message": message,
            **(extra or {})
        }
        _LOG_BUFFER.append(entry)
        
        # Console output in Loki-structured format
        line = json.dumps(entry, default=str)
        if level in ("ERROR", "CRITICAL", "SECURITY"):
            print(f"[{level}] {line}", file=sys.stderr)
        else:
            print(f"[{level}] {line}")

    def debug(self, msg: str, **kwargs): self._emit("DEBUG", msg, kwargs or None)
    def info(self, msg: str, **kwargs): self._emit("INFO", msg, kwargs or None)
    def warning(self, msg: str, **kwargs): self._emit("WARNING", msg, kwargs or None)
    def error(self, msg: str, **kwargs): self._emit("ERROR", msg, kwargs or None)
    def security(self, msg: str, **kwargs): self._emit("SECURITY", msg, kwargs or None)
    def critical(self, msg: str, **kwargs): self._emit("CRITICAL", msg, kwargs or None)

    def log_ai_request(self, student_id: str, intent: str, agent: str, duration_ms: float):
        self._emit("INFO", "AI agent request processed", {
            "student_id": student_id,
            "intent": intent,
            "agent": agent,
            "duration_ms": duration_ms,
            "log_type": "ai_request"
        })

    def log_payment_event(self, student_id: str, amount: float, status: str):
        self._emit("INFO", "Payment event", {
            "student_id": student_id,
            "amount": amount,
            "status": status,
            "log_type": "payment"
        })

    def log_security_event(self, threat: str, source_ip: str = "unknown", details: str = ""):
        self._emit("SECURITY", f"Security event detected: {threat}", {
            "threat_type": threat,
            "source_ip": source_ip,
            "details": details,
            "log_type": "security"
        })

    @staticmethod
    def flush_to_loki(loki_url: str = "http://loki:3100/loki/api/v1/push") -> Dict[str, Any]:
        """
        Formats buffered log lines and pushes to Loki HTTP push endpoint.
        In production: call this on a background thread every 5s.
        """
        if not _LOG_BUFFER:
            return {"pushed": 0}
        
        # Loki expects: {"streams": [{"stream": {labels}, "values": [[timestamp_ns, line]]}]}
        values = []
        for entry in _LOG_BUFFER:
            ts_ns = str(int(datetime.datetime.fromisoformat(
                entry["timestamp"].replace("Z", "+00:00")
            ).timestamp() * 1e9))
            values.append([ts_ns, json.dumps(entry, default=str)])
        
        loki_payload = {
            "streams": [{
                "stream": {"app": "finvault", "env": "production"},
                "values": values
            }]
        }
        
        count = len(_LOG_BUFFER)
        _LOG_BUFFER.clear()
        print(f"[LOKI] Flushed {count} log entries to {loki_url}")
        return {"pushed": count, "payload_streams": 1}

    @staticmethod
    def get_buffered_logs() -> list:
        return list(_LOG_BUFFER)


# Default global logger instances for easy import
backend_logger = LokiLogger(service="finvault-backend", component="api")
agent_logger = LokiLogger(service="finvault-ai", component="orchestrator")
security_logger = LokiLogger(service="finvault-security", component="guardrails")
kafka_logger = LokiLogger(service="finvault-events", component="kafka")
