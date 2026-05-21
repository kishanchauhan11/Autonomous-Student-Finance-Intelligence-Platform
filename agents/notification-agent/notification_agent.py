import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from backend.database_mock import DatabaseMock

class NotificationAgent:
    def __init__(self, nv_client=None):
        self.nv_client = nv_client
        self.name = "Notification Agent"
        
    def dispatch_notification(self, student_id: str, channel: str, message: str) -> dict:
        """
        Sends an automated notification (Email, SMS, or Dashboard Alert) to a student.
        """
        notification = {
            "student_id": student_id,
            "channel": channel.upper(), # EMAIL | SMS | DASHBOARD
            "message": message,
            "status": "DELIVERED"
        }
        # Publish notification event to the Kafka event log
        DatabaseMock.log_kafka_event("notification-sent", notification)
        print(f"[NOTIFICATION] Dispatched to {student_id} via {channel.upper()}: {message}")
        return notification
