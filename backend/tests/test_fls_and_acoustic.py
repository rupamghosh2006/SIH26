"""
Unit Tests for FLS Marine Debris Conversion and Acoustic Frequency Classifier.
"""

import os
import pytest
import numpy as np
from pathlib import Path

from ai_pipeline.seabed_classifier import SeabedClassifier


def test_seabed_geological_classifier():
    """Verify that the seabed classifier evaluates seafloor geological facies."""
    classifier = SeabedClassifier()
    dummy_sonar_patch = np.random.uniform(50, 200, (128, 128)).astype(np.uint8)
    res = classifier.classify_facies(dummy_sonar_patch)

    assert "facies" in res
    assert "confidence" in res
    assert res["facies"] in [
        "sand_ripples", "rocky_reef_boulders", "smooth_mud", "flat_sand"
    ]
    assert 0.0 <= res["confidence"] <= 1.0

    # Test geological interference evaluation
    full_img = np.random.uniform(50, 200, (256, 256)).astype(np.uint8)
    inter_res = classifier.evaluate_geological_interference(
        full_image=full_img,
        bbox=(50, 50, 30, 30),
        has_shadow=False,
        shadow_score=0.2,
        shape_score=0.5
    )
    assert "facies" in inter_res
    assert "penalty" in inter_res
    assert "is_geological_risk" in inter_res


def test_trained_yolo_checkpoints_exist():
    """Verify that the trained YOLOv8 sonar weights exist and are non-empty."""
    checkpoints = [
        "best.pt",
        "models/yolov8_varuna.pt",
        "models/yolov8_crab_pot.pt"
    ]
    for cp in checkpoints:
        candidates = [
            cp,
            os.path.join("backend", cp),
            os.path.join("..", cp),
            os.path.join(os.path.dirname(__file__), "..", cp),
            os.path.join(os.path.dirname(__file__), "..", "..", cp),
        ]
        found = any(os.path.exists(p) and os.path.getsize(p) > 1_000_000 for p in candidates)
        assert found, f"Checkpoint {cp} must exist"
