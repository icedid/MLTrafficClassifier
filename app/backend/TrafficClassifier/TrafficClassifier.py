import joblib
import pandas as pd
import numpy as np

from backend.TrafficClassifier.DataScraper import PacketSniffer

class TrafficClassifier:
    def __init__(self, model_path: str, encoder_path: str):
        """
        Initializes the brain of Net-Sentinel.
        Loads the Random Forest model and the Label Encoder.
        """
        try:
            self.model = joblib.load(model_path)
            self.encoder = joblib.load(encoder_path)
            self.sniffer = PacketSniffer(interface=interface, packet_callback=self.process_packet)
            print(f"Successfully loaded model from {model_path}")
        except Exception as e:
            print(f"Error loading ML assets: {e}")
            raise

    def process_packet(self, packet):
        """
        This is the bridge. Every time the sniffer hears a packet, 
        it runs this function.
        """
        # A. Extract features from the raw packet
        features = self.sniffer.extract_features(packet)
        
        if features:
            # B. Get the prediction and confidence from the classifier
            prediction = self.classifier.predict(features)
            confidence = self.classifier.get_confidence(features)
            
            # C. Output the result (This is where your frontend would get data)
            print(f"[+] Traffic Detected: {prediction} ({confidence:.2%} confidence)")
        else:
            # Optionally handle non-IP or non-relevant traffic
            pass

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