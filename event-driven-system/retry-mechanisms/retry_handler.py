# retry_handler.py - Error retry mechanisms for asynchronous event handling
import time
import random
from typing import Callable, Any

class EventRetryHandler:
    @staticmethod
    def execute_with_retry(func: Callable[[], Any], max_retries: int = 3, initial_delay: float = 1.0) -> Any:
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"[RETRY LIMIT REACHED] Function failed after {max_retries} attempts: {e}")
                    raise e
                # Exponential backoff with jitter
                sleep_time = delay * (1.5 + random.random())
                print(f"[RETRYING] Function failed: {e}. Retrying in {sleep_time:.2f} seconds (Attempt {attempt + 1}/{max_retries})...")
                time.sleep(sleep_time)
                delay *= 2
