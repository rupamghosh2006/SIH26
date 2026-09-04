"""
Acoustic Frequency Signal Inference Engine for Varuna AI.
Loads trained acoustic models to predict whether a 60-band sonar beam echo
originates from an artificial Mine (Threat) or a natural Rock (Benthic Clutter).
"""

import os
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Any, Union, List, Optional


class AcousticSonarClassifier:
    """
    Classifier for 60-band frequency sonar signals.
    """
    def __init__(
        self,
        model_path: Optional[str] = None,
        scaler_path: Optional[str] = None
    ):
        base_dir = Path(__file__).resolve().parent.parent / "models"
        self.model_path = model_path or str(base_dir / "sonar_mine_rock_classifier.joblib")
        self.scaler_path = scaler_path or str(base_dir / "sonar_scaler.joblib")
        self.model = None
        self.scaler = None
        self.load_models()

    def load_models(self) -> bool:
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                return True
        except Exception as e:
            print(f"Warning: Could not load acoustic classifier: {e}")
        return False

    def predict(self, frequency_bands: Union[List[float], np.ndarray]) -> Dict[str, Any]:
        """
        Predicts whether a 60-element frequency return is a Mine or Rock.
        """
        arr = np.asarray(frequency_bands, dtype=np.float32)
        if arr.ndim == 1:
            if len(arr) != 60:
                raise ValueError(f"Expected 60 acoustic frequency bands, received {len(arr)}")
            arr = arr.reshape(1, -1)

        if self.model is None or self.scaler is None:
            return {
                "success": False,
                "error": "Acoustic classifier weights not loaded"
            }

        scaled = self.scaler.transform(arr)
        pred_class = int(self.model.predict(scaled)[0])
        probs = self.model.predict_proba(scaled)[0]

        mine_prob = float(probs[1])
        rock_prob = float(probs[0])
        label = "Mine" if pred_class == 1 else "Rock"
        threat_level = "CRITICAL" if label == "Mine" and mine_prob > 0.75 else ("HIGH" if label == "Mine" else "BENIGN")

        return {
            "success": True,
            "prediction": label,
            "class_id": pred_class,
            "mine_probability": round(mine_prob, 4),
            "rock_probability": round(rock_prob, 4),
            "confidence_score": round(max(mine_prob, rock_prob) * 100, 2),
            "threat_level": threat_level
        }
