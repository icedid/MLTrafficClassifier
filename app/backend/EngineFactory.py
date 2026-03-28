#from backend.TrafficClassifier.RealEngine import RealTrafficEngine
from backend.FakeTrafficEngine import FakeTrafficEngine
from backend.networkengine import NetworkEngine as RealTrafficEngine

class EngineFactory:
    @staticmethod
    def getEngine(mode):
        if mode == "test":
            print("--- RUNNING IN TEST MODE (FAKE TRAFFIC) ---")
            return FakeTrafficEngine()
        if mode == "prod":
            print("--- RUNNING IN PRODUCTION MODE (REAL TRAFFIC) ---")
            return RealTrafficEngine()
        else:
            raise ValueError(f"Invalid mode '{mode}'")