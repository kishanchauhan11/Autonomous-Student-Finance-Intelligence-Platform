import datetime
import json
import os
import sys
from typing import Dict, Any

# Ensure paths can resolve DBConnection
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    from database.MSSQL.db_connection import DBConnection
except ImportError:
    class DBConnection:
        @staticmethod
        def is_mssql_active(): return False

class FinVaultKafkaProducer:
    def __init__(self, mock_store: list = None):
        self.mock_store = mock_store
        
    def publish_event(self, topic: str, data: Dict[str, Any]):
        event = {
            "timestamp": datetime.datetime.now().isoformat(),
            "topic": topic,
            "payload": data
        }
        
        # Save to database if active
        if DBConnection.is_mssql_active():
            try:
                DBConnection.execute_non_query(
                    "INSERT INTO KafkaEvents (topic, payload) VALUES (?, ?)",
                    (topic, json.dumps(data))
                )
            except Exception as e:
                print(f"[KAFKA PRODUCER ERROR] Failed to save to SQL DB: {e}")
                
        # Also store in mock storage list if provided
        if self.mock_store is not None:
            self.mock_store.append(event)
            
        # Log payload safely (avoiding UnicodeEncodeError in Windows terminals for currency characters)
        try:
            print(f"[KAFKA EVENT] Published to topic '{topic}': {data}")
        except UnicodeEncodeError:
            import copy
            data_clean = copy.deepcopy(data)
            if isinstance(data_clean, dict):
                for k, v in data_clean.items():
                    if isinstance(v, str):
                        data_clean[k] = v.encode('ascii', errors='replace').decode('ascii')
            print(f"[KAFKA EVENT] Published to topic '{topic}': {data_clean}")
