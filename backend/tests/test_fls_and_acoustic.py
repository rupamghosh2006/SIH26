"""
Unit Tests for FLS Marine Debris Conversion and Acoustic Frequency Classifier.
"""

import os
import pytest
import numpy as np
from pathlib import Path

from ai_pipeline.acoustic_classifier import AcousticSonarClassifier


def test_acoustic_classifier_inference():
    """Verify that the trained acoustic classifier loads and runs predictions on 60-band pings."""
    classifier = AcousticSonarClassifier()
    assert classifier.model is not None, "Acoustic classifier model should be loaded"
    assert classifier.scaler is not None, "Scaler should be loaded"

    # Synthetic ping with 60 features
    dummy_ping = np.random.uniform(0.01, 0.2, 60).astype(np.float32)
    res = classifier.predict(dummy_ping)

    assert res["success"] is True
    assert res["prediction"] in ["Mine", "Rock"]
    assert 0.0 <= res["confidence_score"] <= 100.0
    assert res["threat_level"] in ["CRITICAL", "HIGH", "BENIGN"]


def test_acoustic_classifier_invalid_input():
    """Verify error handling on invalid dimension input."""
    classifier = AcousticSonarClassifier()
    invalid_ping = [0.1, 0.2, 0.3]  # Only 3 features instead of 60
    with pytest.raises(ValueError):
        classifier.predict(invalid_ping)


def test_trained_yolo_checkpoints_exist():
    """Verify that the trained YOLOv8 sonar weights exist and are non-empty."""
    checkpoints = [
        "best.pt",
        "backend/models/yolov8_varuna.pt",
        "backend/models/yolov8_seaguard.pt"
    ]
    for cp in checkpoints:
        assert os.path.exists(cp), f"Checkpoint {cp} must exist"
        assert os.path.getsize(cp) > 1_000_000, f"Checkpoint {cp} must have valid size"
