"""
Pydantic v2 Request and Response Schemas.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class DetectionResponse(BaseModel):
    id: str
    detection_id: str
    survey_id: str
    ping_index: int
    latitude: float
    longitude: float
    depth_m: Optional[float] = None
    bbox_x: int
    bbox_y: int
    bbox_width: int
    bbox_height: int
    bbox: List[int] = Field(default_factory=list)
    estimated_size_m: str
    predicted_class: str
    confidence_score: float
    confidence_tier: str
    detector_score: float = 0.0
    shadow_score: float = 0.0
    shape_score: float = 0.0
    shadow_detected: bool = False
    thumbnail_url: Optional[str] = None
    timestamp: str
    filter_details: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SurveyBase(BaseModel):
    title: str
    filename: str
    slant_range_m: float = 75.0


class SurveySummary(BaseModel):
    id: str
    title: str
    filename: str
    status: str
    total_detections: int
    high_tier_count: int
    medium_tier_count: int
    low_tier_count: int
    image_width: int
    image_height: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SurveyListResponse(BaseModel):
    total: int
    surveys: List[SurveySummary]


class SurveyDetailResponse(SurveySummary):
    image_url: str
    nadir_x: Optional[int] = None
    error_message: Optional[str] = None
    detections: List[DetectionResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ProcessSurveyResponse(BaseModel):
    survey_id: str
    status: str
    message: str
    total_detections: Optional[int] = None


class DemoSurveyRequest(BaseModel):
    title: Optional[str] = "Demo Coastal Survey"
    scenario: Optional[str] = "coastal"  # coastal, trench, reef
    num_debris: Optional[int] = 4
