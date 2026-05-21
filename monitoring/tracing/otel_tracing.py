# otel_tracing.py - OpenTelemetry Distributed Tracing for FinVault
# Provides end-to-end trace context propagation across AI agents, APIs, and Kafka events.

import uuid
import time
import datetime
from typing import Dict, Any, List, Optional
from contextlib import contextmanager

# In-memory trace store (in production: export to Jaeger/Tempo via OTLP)
_TRACE_STORE: List[Dict[str, Any]] = []

# OpenTelemetry resource attributes
OTEL_RESOURCE = {
    "service.name": "finvault-platform",
    "service.version": "1.0.0",
    "deployment.environment": "production",
    "host.name": "finvault-backend-01"
}

class Span:
    """Represents an OpenTelemetry span (a single timed unit of work)."""

    def __init__(self, name: str, trace_id: str, parent_span_id: Optional[str] = None,
                 attributes: Dict[str, Any] = None):
        self.span_id = str(uuid.uuid4())[:16]
        self.trace_id = trace_id
        self.parent_span_id = parent_span_id
        self.name = name
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status = "OK"
        self.attributes = attributes or {}
        self.events: List[Dict[str, Any]] = []

    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        self.events.append({
            "name": name,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "attributes": attributes or {}
        })

    def set_status(self, status: str, description: str = ""):
        self.status = status
        if description:
            self.attributes["error.description"] = description

    def end(self):
        self.end_time = time.time()
        duration_ms = (self.end_time - self.start_time) * 1000
        self.attributes["duration_ms"] = round(duration_ms, 2)
        
        span_record = {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": duration_ms,
            "status": self.status,
            "attributes": self.attributes,
            "events": self.events,
            "resource": OTEL_RESOURCE
        }
        _TRACE_STORE.append(span_record)
        print(f"[OTEL] Span '{self.name}' | trace={self.trace_id[:8]}... | "
              f"duration={duration_ms:.1f}ms | status={self.status}")
        return span_record


class FinVaultTracer:
    """
    OpenTelemetry-compatible distributed tracer for FinVault.
    Traces the full lifecycle: HTTP request → intent classification → agent execution → response.
    """

    @staticmethod
    def start_trace(operation: str = "student-finance-request") -> str:
        """Starts a new root trace and returns the trace_id."""
        trace_id = str(uuid.uuid4()).replace("-", "")
        print(f"[OTEL] New trace started: {trace_id[:16]}... ({operation})")
        return trace_id

    @staticmethod
    def start_span(name: str, trace_id: str, parent_span_id: Optional[str] = None,
                   attributes: Dict[str, Any] = None) -> Span:
        """Creates and returns a new span within a trace."""
        return Span(name=name, trace_id=trace_id, parent_span_id=parent_span_id,
                    attributes=attributes or {})

    @staticmethod
    @contextmanager
    def traced_operation(name: str, trace_id: str, parent_span_id: Optional[str] = None,
                         attributes: Dict[str, Any] = None):
        """Context manager for automatically ending a span when the block exits."""
        span = FinVaultTracer.start_span(name, trace_id, parent_span_id, attributes)
        try:
            yield span
            span.status = "OK"
        except Exception as e:
            span.set_status("ERROR", str(e))
            raise
        finally:
            span.end()

    @staticmethod
    def trace_ai_pipeline(student_id: str, query: str, intent: str, agent: str,
                          duration_ms: float, trace_id: str) -> Dict[str, Any]:
        """Records a complete AI pipeline span with standard FinVault attributes."""
        span = Span(
            name=f"ai.{agent}.execute",
            trace_id=trace_id,
            attributes={
                "student.id": student_id,
                "ai.query_length": len(query),
                "ai.intent": intent,
                "ai.agent": agent,
                "duration_ms": duration_ms
            }
        )
        # Simulate completing the span
        span.start_time = time.time() - (duration_ms / 1000)
        return span.end()

    @staticmethod
    def get_trace(trace_id: str) -> List[Dict[str, Any]]:
        """Retrieves all spans for a given trace ID."""
        return [s for s in _TRACE_STORE if s["trace_id"] == trace_id]

    @staticmethod
    def get_recent_traces(limit: int = 20) -> List[Dict[str, Any]]:
        """Returns the most recent spans across all traces."""
        return sorted(_TRACE_STORE, key=lambda s: s["start_time"], reverse=True)[:limit]

    @staticmethod
    def export_otlp_format() -> Dict[str, Any]:
        """Exports spans in OTLP-like JSON format for Jaeger/Tempo ingestion."""
        return {
            "resourceSpans": [
                {
                    "resource": {"attributes": [{"key": k, "value": {"stringValue": v}} for k, v in OTEL_RESOURCE.items()]},
                    "scopeSpans": [{"spans": _TRACE_STORE[-50:]}]
                }
            ]
        }
