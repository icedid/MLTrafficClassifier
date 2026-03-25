import random
import threading
import time
from typing import Dict
from backend.engineblueprint import NetworkEngineProvider

class FakeTrafficEngine(NetworkEngineProvider):
    def __init__(self):
        # Match the labels defined in your existing networkengine.py
        self.label_counts = {
            "GAME": 0,
            "INSTANT-MESSAGE": 0,
            "MAIL-SERVICE": 0,
            "NETWORK-STORAGE": 0,
            "NETWORK-TRANSMISSION": 0,
            "VIDEO": 0,
            "WEB-BROWSING": 0,
        }
        self._running = False
        self._thread = None

    def start(self) -> None:
        """Starts a background thread that generates 'fake' packets."""
        self._running = True
        self._thread = threading.Thread(target=self._simulate_traffic, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Signals the background simulation to stop."""
        self._running = False

    def ReturnLabelcount(self) -> Dict[str, int]:
        """Standardized method to return data to the FastAPI router."""
        return self.label_counts.copy()

    def _simulate_traffic(self):
        """Internal loop to simulate incoming flow classifications."""
        categories = list(self.label_counts.keys())
        while self._running:
            # Randomly pick a category and 'detect' 1-5 flows
            chosen_app = random.choice(categories)
            self.label_counts[chosen_app] += random.randint(1, 5)
            
            # Sleep for a bit to simulate real-world arrival times
            time.sleep(random.uniform(0.5, 2.0))