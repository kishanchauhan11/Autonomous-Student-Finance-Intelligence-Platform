# kafka_consumer.py - Centralized consumer logic for FinVault Event Architecture

import json
from typing import Dict, Any, Callable, List

class FinVaultKafkaConsumer:
    def __init__(self):
        self.listeners: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {}

    def subscribe(self, topic: str, callback: Callable[[Dict[str, Any]], None]):
        if topic not in self.listeners:
            self.listeners[topic] = []
        self.listeners[topic].append(callback)

    def process_event(self, topic: str, data: Dict[str, Any]):
        """Simulates ingestion and execution of a message queue payload"""
        if topic in self.listeners:
            for callback in self.listeners[topic]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"[KAFKA CONSUMER ERROR] Callback failed for topic {topic}: {e}")
