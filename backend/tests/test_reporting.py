"""
Unit tests for Report Generation (JSON & CSV schemas).
"""

import json
import pytest
from ai_pipeline.reporting import build_detection_report, REPORT_COLUMNS


def test_build_report_json():
    detections = [
        {
            "detection_id": "det_001",
            "survey_id": "srv_123",
            "ping_index": 42,
            "latitude": 16.352,
            "longitude": 84.502,
            "depth_m": 24.5,
            "bbox_x": 120,
            "bbox_y": 340,
            "bbox_width": 45,
            "bbox_height": 22,
            "estimated_size_m": "3.5m x 1.2m",
            "predicted_class": "ghost_net",
            "confidence_score": 88.5,
            "confidence_tier": "High",
            "timestamp": "2026-09-02T12:00:00Z",
            "source_file": "sonar_survey_01.jpg"
        }
    ]
    survey_meta = {"id": "srv_123", "title": "Test Survey"}
    
    json_str = build_detection_report(detections, survey_meta, output_format="json")
    data = json.loads(json_str)
    
    assert data["total_detections"] == 1
    assert data["tier_counts"]["High"] == 1
    assert len(data["detections"]) == 1
    det = data["detections"][0]
    
    for col in REPORT_COLUMNS:
        assert col in det, f"Missing required column '{col}' in JSON report"


def test_build_report_csv():
    detections = [
        {
            "detection_id": "det_002",
            "survey_id": "srv_123",
            "ping_index": 105,
            "latitude": 16.355,
            "longitude": 84.505,
            "depth_m": 28.0,
            "bbox_x": 550,
            "bbox_y": 620,
            "bbox_width": 60,
            "bbox_height": 15,
            "estimated_size_m": "4.2m x 0.9m",
            "predicted_class": "pipe_cylinder",
            "confidence_score": 92.0,
            "confidence_tier": "High",
            "timestamp": "2026-09-02T12:05:00Z",
            "source_file": "sonar_survey_01.jpg"
        }
    ]
    
    csv_str = build_detection_report(detections, output_format="csv")
    lines = [line.strip() for line in csv_str.strip().splitlines() if line.strip()]
    header = [col.strip() for col in lines[0].split(",")]
    
    for col in REPORT_COLUMNS:
        assert col in header, f"Missing required column '{col}' in CSV header"
    assert len(lines) == 2
