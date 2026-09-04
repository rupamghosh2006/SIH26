"""
Unit tests for the Classical Physics-Based Acoustic Confidence Filter.
Specifically verifies:
1. A synthetic rock cluster without an acoustic shadow is suppressed to a LOW confidence score (<45).
2. A synthetic debris target with a clean, physics-aligned acoustic cast shadow scores HIGH (>=75).
"""

import pytest
import numpy as np
import cv2
from ai_pipeline.confidence_filter import evaluate_detection_confidence, analyze_acoustic_shadow


def create_synthetic_rock_cluster_fixture(width: int = 400, height: int = 400) -> np.ndarray:
    """
    Creates a synthetic flat seabed with a rock cluster:
    Bright backscatter spots with NO systematic acoustic cast shadow.
    """
    img = np.full((height, width), 115, dtype=np.uint8)
    # Add random speckle
    noise = np.random.normal(0, 10, (height, width))
    img = np.clip(img + noise, 0, 255).astype(np.uint8)
    
    # Draw rock cluster at center (x=200, y=200)
    for _ in range(15):
        rx = int(np.random.normal(200, 18))
        ry = int(np.random.normal(200, 18))
        cv2.circle(img, (rx, ry), np.random.randint(2, 6), 240, -1)
        
    return img


def create_synthetic_debris_with_shadow_fixture(width: int = 400, height: int = 400, side: str = "starboard") -> np.ndarray:
    """
    Creates a synthetic seabed with a distinct debris target:
    Specular highlight with a strong acoustic shadow cast away from nadir.
    """
    img = np.full((height, width), 115, dtype=np.uint8)
    noise = np.random.normal(0, 8, (height, width))
    img = np.clip(img + noise, 0, 255).astype(np.uint8)
    
    cx, cy = 200, 200
    nadir_x = 50 if side == "starboard" else 350
    shadow_dir = 1 if side == "starboard" else -1
    
    # Draw acoustic shadow (very dark region away from nadir)
    if side == "starboard":
        # Shadow to the right
        cv2.rectangle(img, (cx + 5, cy - 15), (cx + 60, cy + 15), 15, -1)
        # Highlight on the left
        cv2.rectangle(img, (cx - 10, cy - 15), (cx + 5, cy + 15), 245, -1)
    else:
        # Shadow to the left
        cv2.rectangle(img, (cx - 60, cy - 15), (cx - 5, cy + 15), 15, -1)
        # Highlight on the right
        cv2.rectangle(img, (cx - 5, cy - 15), (cx + 10, cy + 15), 245, -1)
        
    return img


def test_rock_cluster_suppression_low_tier():
    """
    Test that a rock cluster lacking an acoustic shadow is heavily penalized
    and assigned to the 'Low' confidence tier (< 45).
    """
    img = create_synthetic_rock_cluster_fixture()
    nadir_x = 50  # Detection is starboard
    
    # Bounding box around the rock cluster
    bbox = (160, 160, 80, 80)
    yolo_raw_conf = 0.82  # Suppose YOLO detector was moderately/highly triggered by brightness
    
    result = evaluate_detection_confidence(img, bbox, yolo_raw_conf, nadir_x)
    
    # Assertions
    assert result.shadow_detected is False, "Rock cluster should not trigger valid acoustic shadow detection"
    assert result.tier == "Low", f"Expected 'Low' tier for no-shadow rock cluster, got '{result.tier}'"
    assert result.final_score < 45.0, f"Expected final score < 45.0 for suppressed cluster, got {result.final_score}"
    assert result.shadow_score < 35.0, f"Expected shadow score < 35.0, got {result.shadow_score}"


def test_debris_with_shadow_high_tier():
    """
    Test that a debris object with clean acoustic highlight and shadow
    scores in the 'High' confidence tier (>= 75).
    """
    img = create_synthetic_debris_with_shadow_fixture(side="starboard")
    nadir_x = 50  # Starboard side
    
    # Bounding box covering highlight + shadow
    bbox = (180, 175, 90, 50)
    yolo_raw_conf = 0.88
    
    result = evaluate_detection_confidence(img, bbox, yolo_raw_conf, nadir_x)
    
    # Assertions
    assert result.shadow_detected is True, "Debris with shadow must detect valid shadow"
    assert result.tier == "High", f"Expected 'High' tier for clean debris shadow, got '{result.tier}'"
    assert result.final_score >= 75.0, f"Expected final score >= 75.0, got {result.final_score}"
    assert result.shadow_score >= 70.0, f"Expected high shadow score >= 70.0, got {result.shadow_score}"


def test_port_side_shadow_alignment():
    """
    Test port-side acoustic shadow physics (shadow extending leftward towards x=0).
    """
    img = create_synthetic_debris_with_shadow_fixture(side="port")
    nadir_x = 350  # Port side (detection center at x=200 < nadir_x=350)
    
    bbox = (130, 175, 90, 50)
    yolo_raw_conf = 0.85
    
    result = evaluate_detection_confidence(img, bbox, yolo_raw_conf, nadir_x)
    assert result.shadow_detected is True
    assert result.tier == "High"
    assert result.details["shadow_details"]["expected_shadow_side"] == "left"
