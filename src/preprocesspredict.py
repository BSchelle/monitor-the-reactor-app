from pathlib import Path
from typing import Dict, Any
import joblib
import numpy as np

class PredictionPipeline:
    def __init__(self, modelpath="models/bestmodel.pkl", scalerpath="models/preprocessor.pkl"):
        self.model_path = Path(modelpath)
        self.scaler_path = Path(scalerpath)
        self.model = joblib.load(self.model_path) if self.model_path.exists() else None
        self.scaler = joblib.load(self.scaler_path) if self.scaler_path.exists() else None

    def preprocess(self, data: Dict[str, Any]) -> np.ndarray:
        features_order = ["temperature", "pressure", "flowrate", "vibration"]
        missing = [f for f in features_order if f not in data]
        if missing:
            raise ValueError(f"Missing features: {missing}")
        X = np.array([data[f] for f in features_order]).reshape(1, -1)
        return self.scaler.transform(X) if self.scaler else X

    def predict_proba(self, data: Dict[str, Any]) -> float:
        if not self.model:
            return 0.0
        Xp = self.preprocess(data)
        return float(self.model.predict_proba(Xp)[0, 1])

    def predict_with_alert(self, data: Dict[str, Any], threshold: float = 0.8):
        proba = self.predict_proba(data)
        alert = proba >= threshold
        return {"probability": proba, "alert": alert, "threshold": threshold}
