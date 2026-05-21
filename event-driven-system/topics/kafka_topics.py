# kafka_topics.py - Centralized topic definitions for FinVault Event Architecture

TOPIC_AGENT_RESPONSE = "agent-response-generated"
TOPIC_REFUND_SUBMITTED = "refund-submitted"
TOPIC_NOTIFICATION_SENT = "notification-sent"
TOPIC_PAYMENT_RECONCILED = "payment-reconciled"
TOPIC_REFUND_APPROVED = "refund-approved"
TOPIC_REFUND_REJECTED = "refund-rejected"
TOPIC_ESCALATION_TRIGGERED = "escalation-triggered"

ALL_TOPICS = [
    TOPIC_AGENT_RESPONSE,
    TOPIC_REFUND_SUBMITTED,
    TOPIC_NOTIFICATION_SENT,
    TOPIC_PAYMENT_RECONCILED,
    TOPIC_REFUND_APPROVED,
    TOPIC_REFUND_REJECTED,
    TOPIC_ESCALATION_TRIGGERED
]
