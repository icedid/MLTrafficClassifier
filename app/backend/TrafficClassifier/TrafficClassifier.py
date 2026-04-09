import joblib
import pandas as pd
import numpy as np

class TrafficClassifier:
    def __init__(self, model_path: str, encoder_path: str, interface: str):
        """
        Initializes the brain of Net-Sentinel.
        Loads the Random Forest model and the Label Encoder.
        """
        try:
            self.model = joblib.load(model_path)
            self.encoder = joblib.load(encoder_path)
            print(f"Successfully loaded model from {model_path}")
        except Exception as e:
            print(f"Error loading ML assets: {e}")
            raise

    def predict(self, feature_vector: list) -> str:
        """
        Takes a list of numerical features and returns a human-readable string.
        
        Args:
            feature_vector: A list of floats/ints (e.g., [IAT, pkt_len, etc.])
                           MUST match the order used during training.
        """
        try:
            # 1. Convert to 2D array (1 sample, N features)
            data = np.array(feature_vector).reshape(1, -1)
            
            # 2. Perform the prediction (returns a number)
            prediction_numeric = self.model.predict(data)
            
            # 3. Decode the number back into a human-readable string
            label = self.encoder.inverse_transform(prediction_numeric)[0]
            
            return label
        except Exception as e:
            print(f"Inference error: {e}")
            return "Unknown"
        

    def get_confidence(self, feature_vector: list) -> float:
        """
        Optional: Returns the probability score (0.0 to 1.0)
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
            # 1. Single Inference Pass
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

            return label, float(max_prob)

        except Exception as e:
            print(f"Inference error: {e}")
            return "Error", 0.0