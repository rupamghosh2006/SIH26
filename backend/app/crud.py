"""
Database CRUD operations for Surveys, Detections, and Navigation Pings.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from . import models, schemas


def get_survey(db: Session, survey_id: str) -> Optional[models.Survey]:
    return db.query(models.Survey).filter(models.Survey.id == survey_id).first()


def get_surveys(db: Session, skip: int = 0, limit: int = 100) -> List[models.Survey]:
    return db.query(models.Survey).order_by(desc(models.Survey.created_at)).offset(skip).limit(limit).all()


def create_survey(db: Session, survey_data: Dict[str, Any]) -> models.Survey:
    db_survey = models.Survey(**survey_data)
    db.add(db_survey)
    db.commit()
    db.refresh(db_survey)
    return db_survey


def update_survey_status(
    db: Session,
    survey_id: str,
    status: str,
    error_message: Optional[str] = None
) -> Optional[models.Survey]:
    survey = get_survey(db, survey_id)
    if survey:
        survey.status = status
        if error_message is not None:
            survey.error_message = error_message
        db.commit()
        db.refresh(survey)
    return survey


def delete_survey(db: Session, survey_id: str) -> bool:
    survey = get_survey(db, survey_id)
    if survey:
        db.delete(survey)
        db.commit()
        return True
    return False


def get_detections_for_survey(
    db: Session,
    survey_id: str,
    min_confidence: Optional[float] = None,
    tier: Optional[str] = None,
    predicted_class: Optional[str] = None
) -> List[models.Detection]:
    query = db.query(models.Detection).filter(models.Detection.survey_id == survey_id)
    
    if min_confidence is not None:
        query = query.filter(models.Detection.confidence_score >= min_confidence)
    if tier is not None:
        query = query.filter(models.Detection.confidence_tier == tier)
    if predicted_class is not None:
        query = query.filter(models.Detection.predicted_class == predicted_class)
        
    return query.order_by(desc(models.Detection.confidence_score)).all()


def save_survey_results(
    db: Session,
    survey_id: str,
    detections: List[Dict[str, Any]],
    nadir_x: int,
    image_width: int,
    image_height: int
) -> Optional[models.Survey]:
    import json
    survey = get_survey(db, survey_id)
    if not survey:
        return None

    # Clear previous detections if any
    db.query(models.Detection).filter(models.Detection.survey_id == survey_id).delete()

    high_count = 0
    med_count = 0
    low_count = 0

    for d in detections:
        tier = d["confidence_tier"]
        if tier == "High":
            high_count += 1
        elif tier == "Medium":
            med_count += 1
        else:
            low_count += 1

        det_obj = models.Detection(
            id=d["id"],
            survey_id=survey_id,
            ping_index=d["ping_index"],
            latitude=d["latitude"],
            longitude=d["longitude"],
            depth_m=d.get("depth_m"),
            bbox_x=d["bbox_x"],
            bbox_y=d["bbox_y"],
            bbox_width=d["bbox_width"],
            bbox_height=d["bbox_height"],
            estimated_size_m=d.get("estimated_size_m", "Unknown"),
            predicted_class=d["predicted_class"],
            confidence_score=d["confidence_score"],
            confidence_tier=tier,
            detector_score=d.get("detector_score", 0.0),
            shadow_score=d.get("shadow_score", 0.0),
            shape_score=d.get("shape_score", 0.0),
            shadow_detected=d.get("shadow_detected", False),
            thumbnail_url=d.get("thumbnail_url"),
            timestamp=d["timestamp"],
            filter_details_json=json.dumps(d.get("filter_details", {}))
        )
        db.add(det_obj)

    survey.status = "done"
    survey.nadir_x = nadir_x
    survey.image_width = image_width
    survey.image_height = image_height
    survey.total_detections = len(detections)
    survey.high_tier_count = high_count
    survey.medium_tier_count = med_count
    survey.low_tier_count = low_count

    db.commit()
    db.refresh(survey)
    return survey
