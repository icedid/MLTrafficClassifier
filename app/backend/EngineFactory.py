#from backend.TrafficClassifier.RealEngine import RealTrafficEngine
from backend.FakeTrafficEngine import FakeTrafficEngine
from backend.networkengine import NetworkEngine as RealTrafficEngine
import os
from backend.core.validator import MLAssetValidator

class EngineFactory:
    
    @staticmethod
    def getEngine(mode):
        if mode == "test":
            print("--- RUNNING IN TEST MODE (FAKE TRAFFIC) ---")
            return FakeTrafficEngine()
        if mode == "prod":
            print("--- RUNNING IN PRODUCTION MODE (REAL TRAFFIC) ---")
            
            validators = [MLAssetValidator()]
            assets_to_check = [model_path, encoder_path]
            
            
            # 3. Execute Pre-flight Checks
            ml_check = MLAssetValidator().is_valid([model_path, encoder_path])
            if not ml_check.success:
                print(f"\n[!] ML ASSET ERROR: {ml_check.message}\n")
                raise SystemExit("Engine startup failed: ML assets invalid.")
            
            BASE_DIR = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(BASE_DIR, "TrafficClassifier", "traffic_classifier_rf.pkl")
            encoder_path = os.path.join(BASE_DIR, "TrafficClassifier", "label_encoder.pkl")
            return RealTrafficEngine(model_path,encoder_path)
        else:
            raise ValueError(f"Invalid mode '{mode}'")