"""
Active Verification Test Suite.
Verifies adaptive rescan planning, target association, multi-observation evidence comparison,
and deterministic simulation scenarios for VARUNA AI.
"""

import unittest
import numpy as np
from backend.ai_pipeline.active_verification import (
    assess_verification_need,
    plan_secondary_rescan,
    match_secondary_detection,
    compare_observations,
    generate_synthetic_rescan_image
)


class TestVerificationNeed(unittest.TestCase):
    def test_low_confidence_requires_mandatory_rescan(self):
        result = assess_verification_need(
            confidence_score=38.5,
            confidence_tier="Low",
            shadow_detected=False,
            shadow_score=15.0,
            detector_score=42.0
        )
        assert result["recommendation"] == "MANDATORY"
        assert result["tier"] == "Low"
        assert len(result["reasons"]) >= 2
        assert any("Missing acoustic cast shadow" in r for r in result["reasons"])

    def test_medium_confidence_recommends_rescan(self):
        result = assess_verification_need(
            confidence_score=63.2,
            confidence_tier="Medium",
            shadow_detected=True,
            shadow_score=52.4,
            detector_score=68.0
        )
        assert result["recommendation"] == "RECOMMENDED"
        assert result["tier"] == "Medium"
        assert any("Medium tier" in r for r in result["reasons"])

    def test_high_confidence_is_optional(self):
        result = assess_verification_need(
            confidence_score=89.5,
            confidence_tier="High",
            shadow_detected=True,
            shadow_score=88.0,
            detector_score=92.0
        )
        assert result["recommendation"] == "OPTIONAL"
        assert result["tier"] == "High"


class TestRescanPlanning(unittest.TestCase):
    def test_generates_valid_swath_geometry_and_waypoints(self):
        det = {
            "bbox": [280, 180, 80, 60],
            "class": "ghost_net",
            "confidence_score": 62.5,
            "confidence_tier": "Medium",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "shadow_detected": True,
            "shadow_score": 54.0,
            "detector_score": 65.0
        }
        plan = plan_secondary_rescan(
            detection=det,
            nadir_x=512,
            image_width=1024,
            slant_range_m=75.0
        )
        assert "target_info" in plan
        assert "recommended_observation" in plan
        assert "geospatial_routes" in plan
        assert plan["recommended_observation"]["suggested_offset_meters"] > 0
        assert len(plan["geospatial_routes"]["primary_survey"]) == 3
        assert len(plan["geospatial_routes"]["verification_survey"]) == 3
        assert plan["simulation_mode"]["is_simulation"] is True


class TestTargetAssociation(unittest.TestCase):
    def test_associates_correct_target_spatially_and_by_class(self):
        primary_bbox = [300, 200, 80, 60]
        secondary_candidates = [
            {"bbox": [50, 50, 40, 40], "class": "tires", "confidence": 0.4},
            {"bbox": [310, 205, 82, 58], "class": "ghost_net", "confidence": 0.85},
            {"bbox": [400, 400, 70, 70], "class": "rock_cluster", "confidence": 0.5}
        ]
        matched, score = match_secondary_detection(
            primary_bbox=primary_bbox,
            primary_class="ghost_net",
            secondary_detections=secondary_candidates,
            image_shape=(512, 512)
        )
        assert matched is not None
        assert matched["class"] == "ghost_net"
        assert score >= 70.0

    def test_returns_none_when_no_candidate_matches(self):
        primary_bbox = [300, 200, 80, 60]
        secondary_candidates = [
            {"bbox": [20, 20, 30, 30], "class": "rock_cluster", "confidence": 0.2}
        ]
        matched, score = match_secondary_detection(
            primary_bbox=primary_bbox,
            primary_class="ghost_net",
            secondary_detections=secondary_candidates,
            image_shape=(512, 512)
        )
        assert matched is None


class TestEvidenceComparison(unittest.TestCase):
    def test_scenario_a_confirms_target(self):
        primary = {
            "class": "ghost_net",
            "confidence_score": 62.0,
            "detector_score": 65.0,
            "shadow_score": 52.0,
            "shape_score": 70.0
        }
        secondary = {
            "class": "ghost_net",
            "confidence_score": 88.5,
            "detector_score": 90.0,
            "shadow_score": 86.0,
            "shape_score": 82.0
        }
        res = compare_observations(primary, secondary, match_score=85.0)
        assert res["status"] == "VERIFIED"
        assert res["class_consistent"] is True
        assert res["confidence_delta"] == 26.5
        assert res["evidence_strengthened"] is True
        assert res["recommended_action"] == "CONFIRM"

    def test_scenario_b_rejects_false_alarm_with_lower_confidence(self):
        primary = {
            "class": "ghost_net",
            "confidence_score": 62.0,
            "detector_score": 65.0,
            "shadow_score": 52.0,
            "shape_score": 70.0
        }
        secondary = {
            "class": "rock_cluster",
            "confidence_score": 34.0,
            "detector_score": 35.0,
            "shadow_score": 20.0,
            "shape_score": 45.0
        }
        res = compare_observations(primary, secondary, match_score=40.0)
        assert res["status"] == "NOT_CONFIRMED"
        assert res["class_consistent"] is False
        assert res["confidence_delta"] < 0
        assert res["evidence_strengthened"] is False
        assert res["recommended_action"] == "REJECT"

    def test_missing_secondary_target_is_not_confirmed(self):
        primary = {
            "class": "ghost_net",
            "confidence_score": 60.0
        }
        res = compare_observations(primary, None, match_score=0.0)
        assert res["status"] == "NOT_CONFIRMED"
        assert res["target_associated"] is False
        assert res["confidence_delta"] == -60.0

    def test_no_artificial_confidence_boosting(self):
        primary = {"class": "pipe_cylinder", "confidence_score": 50.0, "shadow_score": 40.0}
        secondary = {"class": "pipe_cylinder", "confidence_score": 53.2, "shadow_score": 46.0}
        res = compare_observations(primary, secondary, match_score=80.0)
        assert res["confidence_delta"] == 3.2


class TestSyntheticRescanGeneration(unittest.TestCase):
    def test_synthetic_confirm_image_produces_valid_high_confidence_roi(self):
        img, dets = generate_synthetic_rescan_image("confirm", "ghost_net")
        assert isinstance(img, np.ndarray)
        assert img.shape == (512, 512, 3)
        assert len(dets) == 1
        assert dets[0]["class"] == "ghost_net"
        assert dets[0]["confidence_score"] >= 70.0

    def test_synthetic_reject_image_produces_low_confidence_anomaly(self):
        img, dets = generate_synthetic_rescan_image("reject", "ghost_net")
        assert isinstance(img, np.ndarray)
        assert len(dets) == 1
        assert dets[0]["confidence_score"] < 50.0


if __name__ == "__main__":
    unittest.main()

