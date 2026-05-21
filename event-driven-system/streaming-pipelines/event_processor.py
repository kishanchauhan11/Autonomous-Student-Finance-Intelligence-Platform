# event_processor.py - Simulates asynchronous stream processing pipelines
import time
from typing import Dict, Any, Callable

class EventStreamingPipeline:
    def __init__(self, consumer):
        self.consumer = consumer
        self.setup_subscriptions()

    def setup_subscriptions(self):
        # Subscribe to refund submissions to log audit trail
        self.consumer.subscribe("refund-submitted", self.on_refund_submitted)
        self.consumer.subscribe("payment-reconciled", self.on_payment_reconciled)

    def on_refund_submitted(self, event_data: Dict[str, Any]):
        print(f"[STREAM PIPELINE] Processing refund submission: Request ID {event_data.get('request_id')} for Student {event_data.get('student_id')}")

    def on_payment_reconciled(self, event_data: Dict[str, Any]):
        print(f"[STREAM PIPELINE] Processing payment reconciliation: Txn ID {event_data.get('txn_id')} - Amount: {event_data.get('amount')}")
