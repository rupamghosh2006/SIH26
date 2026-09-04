"""
Integration tests for FastAPI endpoints.
"""

import io
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import Base, engine
import numpy as np
import cv2

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "model_loaded" in data


def test_create_and_query_demo_survey():
    # 1. Create demo survey
    response = client.post("/api/surveys/demo/create", json={
        "title": "Automated Test Survey",
        "scenario": "coastal",
        "num_debris": 3
    })
    assert response.status_code == 201
    survey_data = response.json()
    survey_id = survey_data["id"]
    assert survey_data["status"] == "done"
    assert survey_data["total_detections"] >= 0

    # 2. Get survey detail
    detail_res = client.get(f"/api/surveys/{survey_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert detail["id"] == survey_id
    assert "detections" in detail
    assert "image_url" in detail

    # 3. Get detections list
    det_res = client.get(f"/api/surveys/{survey_id}/detections")
    assert det_res.status_code == 200
    assert isinstance(det_res.json(), list)

    # 4. Download report as JSON
    rep_json = client.get(f"/api/surveys/{survey_id}/report?format=json")
    assert rep_json.status_code == 200
    assert "application/json" in rep_json.headers["content-type"]

    # 5. Download report as CSV
    rep_csv = client.get(f"/api/surveys/{survey_id}/report?format=csv")
    assert rep_csv.status_code == 200
    assert "text/csv" in rep_csv.headers["content-type"]

    # 6. Delete survey
    del_res = client.delete(f"/api/surveys/{survey_id}")
    assert del_res.status_code == 200
    
    # 7. Verify deletion
    not_found = client.get(f"/api/surveys/{survey_id}")
    assert not_found.status_code == 404
