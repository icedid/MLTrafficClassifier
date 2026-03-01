

class TrafficClassifier:
    def __init__(self, model_path:str, encoder_path:str):
        self.model = joblib.load(model_path)
        self.encoder = joblib.load(encoder_path)
        
