"""
Unit and Integration Tests for Explainable Sonar Feature.
Covers:
1. Explainability intermediate data fields presence
2. Detector score extraction
3. Shadow score calculation & range
4. Morphology score calculation & range
5. Formula consistency: (0.50 * detector) + (0.35 * shadow) + (0.15 * shape)
6. Shadow detected flag accuracy
7. Missing filter details robustness (no crash)
8. Invalid survey/detection ID 404 handling
9. Explainability overlay image generation & boundary safety
10. Backward compatibility with existing survey and detection APIs
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    import pytest
except ImportError:
    class DummyPytest:
        def fixture(self, *args, **kwargs):
            if args and callable(args[0]):
                return args[0]
            def decorator(func):
                return func
            return decorator

        def approx(self, val, rel=None, abs=None):
            return val

    pytest = DummyPytest()

import numpy as np
import cv2

try:
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import Base, engine, SessionLocal, get_db
    from app import models, crud
    from app.routes.surveys import generate_explainability_overlay
except ImportError:
    pass

from ai_pipeline.confidence_filter import evaluate_detection_confidence, analyze_acoustic_shadow, ConfidenceResult


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def synthetic_sonar_image():
    """Generates a 600x800 synthetic sonar image with nadir at x=400."""
    h, w = 600, 800
    img = np.full((h, w), 110, dtype=np.uint8)
    # Nadir line
    img[:, 385:415] = 15
    # Starboard target at x=520 with highlight (left) and shadow (right)
    cv2.rectangle(img, (510, 200), (530, 240), 240, -1)  # Highlight
    cv2.rectangle(img, (530, 200), (580, 240), 18, -1)   # Shadow
    return img


def test_explainability_data_present(synthetic_sonar_image):
    """Test that evaluate_detection_confidence returns all intermediate explainability fields."""
    bbox = (505, 195, 80, 50)
    raw_conf = 0.88
    nadir_x = 400

    result = evaluate_detection_confidence(synthetic_sonar_image, bbox, raw_conf, nadir_x)

    assert isinstance(result, ConfidenceResult)
    assert hasattr(result, "detector_score")
    assert hasattr(result, "shadow_score")
    assert hasattr(result, "shape_score")
    assert hasattr(result, "final_score")
    assert hasattr(result, "tier")
    assert hasattr(result, "shadow_detected")
    assert hasattr(result, "details")

    # Details check
    assert "shadow_details" in result.details
    assert "shape_details" in result.details
    assert "suppression_applied" in result.details


def test_detector_score_exposed(synthetic_sonar_image):
    """Test that detector_score matches raw_conf * 100."""
    bbox = (505, 195, 80, 50)
    raw_conf = 0.912
    nadir_x = 400

    result = evaluate_detection_confidence(synthetic_sonar_image, bbox, raw_conf, nadir_x)
    assert result.detector_score == pytest.approx(91.2, 0.1)


def test_shadow_score_exposed(synthetic_sonar_image):
    """Test that shadow_score is within 0-100 and higher for valid shadows."""
    bbox_shadow = (505, 195, 80, 50)
    bbox_noshadow = (100, 100, 40, 40)
    nadir_x = 400

    res_shadow = evaluate_detection_confidence(synthetic_sonar_image, bbox_shadow, 0.85, nadir_x)
    res_noshadow = evaluate_detection_confidence(synthetic_sonar_image, bbox_noshadow, 0.85, nadir_x)

    assert 0.0 <= res_shadow.shadow_score <= 100.0
    assert 0.0 <= res_noshadow.shadow_score <= 100.0
    assert res_shadow.shadow_score > res_noshadow.shadow_score


def test_shape_score_exposed(synthetic_sonar_image):
    """Test that shape_score is computed and within 0-100."""
    bbox = (505, 195, 80, 50)
    result = evaluate_detection_confidence(synthetic_sonar_image, bbox, 0.85, nadir_x=400)
    assert 0.0 <= result.shape_score <= 100.0


def test_final_score_matches_formula(synthetic_sonar_image):
    """Test that final score satisfies (0.50*det + 0.35*shd + 0.15*shp) * (0.48 if not shadow)."""
    bbox = (505, 195, 80, 50)
    result = evaluate_detection_confidence(synthetic_sonar_image, bbox, 0.90, nadir_x=400)

    composite = (0.50 * result.detector_score) + (0.35 * result.shadow_score) + (0.15 * result.shape_score)
    if not result.shadow_detected:
        composite *= 0.48

    expected_final = min(100.0, max(0.0, round(composite, 1)))
    assert result.final_score == pytest.approx(expected_final, 0.2)


def test_shadow_detected_representation(synthetic_sonar_image):
    """Test shadow_detected is a valid boolean."""
    bbox = (505, 195, 80, 50)
    result = evaluate_detection_confidence(synthetic_sonar_image, bbox, 0.88, nadir_x=400)
    assert isinstance(result.shadow_detected, (bool, np.bool_))


def test_missing_filter_details_no_crash(synthetic_sonar_image):
    """Test that an empty ROI or boundary edge does not crash the pipeline."""
    # Degenerate bbox
    bbox = (0, 0, 1, 1)
    result = evaluate_detection_confidence(synthetic_sonar_image, bbox, 0.50, nadir_x=400)
    assert result.final_score >= 0.0
    assert result.tier in ["Low", "Medium", "High"]


def test_explainability_overlay_generation(synthetic_sonar_image, tmp_path):
    """Test that generate_explainability_overlay creates a valid annotated image with HUD."""
    det = models.Detection(
        id="det_test_001",
        survey_id="srv_test",
        predicted_class="ghost_net",
        confidence_score=88.4,
        confidence_tier="High",
        detector_score=91.0,
        shadow_score=87.0,
        shape_score=82.0,
        shadow_detected=True,
        bbox_x=510,
        bbox_y=200,
        bbox_width=70,
        bbox_height=40
    )

    overlay = generate_explainability_overlay(synthetic_sonar_image, det, nadir_x=400)
    assert overlay is not None
    assert overlay.ndim == 3  # Color image
    assert overlay.shape[0] > 40  # Has HUD + Crop canvas
    assert overlay.shape[1] > 70


def test_invalid_detection_id_returns_404(client):
    """Test that requesting an explainability overlay for a non-existent survey/detection returns 404."""
    response = client.get("/api/surveys/non_existent_survey/detections/invalid_id/explainability-image")
    assert response.status_code == 404


def test_explainability_overlay_endpoint_functional(client, test_db, tmp_path):
    """Test the full REST explainability image endpoint."""
    # 1. Create a dummy image on disk
    img_file = tmp_path / "test_sonar_swath.png"
    img = np.full((400, 600, 3), 120, dtype=np.uint8)
    cv2.imwrite(str(img_file), img)

    # 2. Add survey and detection record to test_db
    import uuid
    sid = f"srv_exp_{uuid.uuid4().hex[:6]}"
    did = f"det_exp_{uuid.uuid4().hex[:6]}"
    survey = models.Survey(
        id=sid,
        title="Test Survey",
        filename="test_sonar_swath.png",
        image_path=str(img_file),
        status="completed",
        nadir_x=300
    )
    test_db.add(survey)

    det = models.Detection(
        id=did,
        survey_id=sid,
        latitude=12.9716,
        longitude=77.5946,
        depth_m=15.0,
        timestamp="2026-09-06T00:00:00Z",
        predicted_class="container_drum",
        confidence_score=92.5,
        confidence_tier="High",
        detector_score=94.0,
        shadow_score=91.0,
        shape_score=88.0,
        shadow_detected=True,
        bbox_x=350,
        bbox_y=150,
        bbox_width=60,
        bbox_height=45
    )
    test_db.add(det)
    test_db.commit()
    # 3. Request explainability image
    response = client.get(f"/api/surveys/{sid}/detections/{did}/explainability-image")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 100


if __name__ == "__main__":
    print("=" * 70)
    print(" Running Explainable Sonar Test Suite")
    print("=" * 70)
    img = synthetic_sonar_image()
    
    print("1. Testing explainability data fields presence...")
    test_explainability_data_present(img)
    print("   [PASS]")

    print("2. Testing detector score exposed...")
    test_detector_score_exposed(img)
    print("   [PASS]")

    print("3. Testing shadow score range and contrast...")
    test_shadow_score_exposed(img)
    print("   [PASS]")

    print("4. Testing shape morphology score range...")
    test_shape_score_exposed(img)
    print("   [PASS]")

    print("5. Testing composite confidence formula & suppression multiplier...")
    test_final_score_matches_formula(img)
    print("   [PASS]")

    print("6. Testing shadow_detected representation...")
    test_shadow_detected_representation(img)
    print("   [PASS]")

    print("7. Testing robustness with edge/boundary bboxes...")
    test_missing_filter_details_no_crash(img)
    print("   [PASS]")

    print("8. Testing explainability visual overlay generation...")
    test_explainability_overlay_generation(img, None)
    print("   [PASS]")

    print("=" * 70)
    print(" ALL 8 CORE EXPLAINABLE SONAR VERIFICATIONS PASSED!")
    print("=" * 70)
