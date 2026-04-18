import joblib
import numpy as np
import warnings

class TrafficClassifier:
    def __init__(self, model_path: str, encoder_path: str, interface: str = None):
        """
        Initializes the brain of Net-Sentinel.
        Loads the LightGBM model and the Label Encoder.
        """
        warnings.filterwarnings("ignore", category=UserWarning, module='sklearn.utils.validation')
        try:
            self.model = joblib.load(model_path)
            self.encoder = joblib.load(encoder_path)
            print(f"[*] Successfully loaded ML assets from {model_path}")
        except Exception as e:
            print(f"[!] Error loading ML assets: {e}")
            raise

    def predict(self, feature_vector: list) -> str:
        """
        Takes a list of numerical features and returns a human-readable string.
        """
        try:
            # 1. Convert to 2D array exactly like the working test.py
            data = np.array(feature_vector).reshape(1, -1)
            
            # 2. Perform the prediction
            prediction_numeric = self.model.predict(data)
            
            # 3. Decode the number back into a human-readable string
            label = self.encoder.inverse_transform(prediction_numeric)[0]
            
            return str(label)
        except Exception as e:
            print(f"[!] Inference error: {e}")
            return "Unknown"
        
    def get_confidence(self, feature_vector: list) -> float:
        """
        Returns the probability score (0.0 to 1.0)
        Useful for the 'Confidence' bar on your frontend.
        """
        data = np.array(feature_vector).reshape(1, -1)
        probabilities = self.model.predict_proba(data)
        return float(np.max(probabilities))
    
    def get_prediction_with_threshold(self, feature_vector: list, threshold: float = 0.6):
        """
        The 'Gold Standard' method: Performs inference ONCE and applies logic.
        """
        try:
            # 1. Single Inference Pass using exact test.py shape
            data = np.array(feature_vector).reshape(1, -1)

            probabilities = self.model.predict_proba(data)[0] # Shape: [n_classes]
            
            # 2. Extract stats
            max_prob = np.max(probabilities)
            prediction_numeric = np.argmax(probabilities)

            # 3. Threshold Logic
            if max_prob >= threshold:
                label = self.encoder.inverse_transform([prediction_numeric])[0]
            else:
                label = "Unknown" # Noise reduction happens here

            return str(label), float(max_prob)

        except Exception as e:
            print(f"[!] Inference error: {e}")
            return "Error", 0.0
        
        
