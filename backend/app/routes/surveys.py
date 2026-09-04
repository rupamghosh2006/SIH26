"""
Survey API Endpoints:
- Upload sonar image and optional navigation metadata
- Trigger asynchronous / background AI processing
- List, retrieve details, and query detections
- Download structured reports (JSON / CSV)
- Delete surveys and associated artifacts
- Generate instant sample surveys
"""

import os
import uuid
import aiofiles
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, Query, Response
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from ..database import get_db, SessionLocal
from ..config import settings
from .. import crud, schemas, models
from ..service import run_survey_pipeline, create_sample_demo_survey
from ai_pipeline.reporting import build_detection_report

router = APIRouter(prefix="/surveys", tags=["Surveys"])


def bg_process_survey(survey_id: str):
    """Background task wrapper with independent DB session."""
    db = SessionLocal()
    try:
        run_survey_pipeline(db, survey_id)
    finally:
        db.close()


@router.post("/upload", response_model=schemas.SurveySummary, status_code=201)
async def upload_survey(
    background_tasks: BackgroundTasks,
    image_file: UploadFile = File(...),
    metadata_file: Optional[UploadFile] = File(None),
    title: Optional[str] = Form(None),
    slant_range_m: float = Form(75.0),
    auto_process: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    Upload a side-scan sonar waterfall image (PNG/JPG) along with an optional
    navigation metadata file (CSV or JSON with ping_index, lat, lon, timestamp).
    """
    # 1. Validate Image File
    allowed_extensions = [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"]
    file_ext = os.path.splitext(image_file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file_ext}'. Allowed sonar image formats: {allowed_extensions}"
        )

    survey_id = f"srv_{uuid.uuid4().hex[:10]}"
    clean_title = title.strip() if title and title.strip() else f"Sonar Survey {survey_id[-6:]}"
    
    # 2. Save Image File
    image_filename = f"{survey_id}_{image_file.filename}"
    image_save_path = settings.UPLOADS_DIR / image_filename
    
    try:
        async with aiofiles.open(image_save_path, "wb") as out_file:
            content = await image_file.read()
            if len(content) == 0:
                raise HTTPException(status_code=400, detail="Uploaded image file is empty.")
            await out_file.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed saving image file: {e}")

    # 3. Save Navigation Metadata File if provided
    metadata_save_path = None
    if metadata_file and metadata_file.filename:
        meta_ext = os.path.splitext(metadata_file.filename)[1].lower()
        if meta_ext not in [".csv", ".json", ".txt"]:
            raise HTTPException(status_code=400, detail="Metadata file must be CSV or JSON format.")
        
        meta_filename = f"{survey_id}_nav{meta_ext}"
        metadata_save_path = str(settings.UPLOADS_DIR / meta_filename)
        async with aiofiles.open(metadata_save_path, "wb") as out_meta:
            meta_content = await metadata_file.read()
            await out_meta.write(meta_content)

    # 4. Create DB Survey Record
    survey_data = {
        "id": survey_id,
        "title": clean_title,
        "filename": image_file.filename,
        "image_path": str(image_save_path),
        "metadata_path": metadata_save_path,
        "slant_range_m": slant_range_m,
        "status": "uploaded"
    }
    
    survey = crud.create_survey(db, survey_data)

    # 5. Kick off auto-processing in background if requested
    if auto_process:
        background_tasks.add_task(bg_process_survey, survey_id)

    return survey


@router.post("/{survey_id}/process", response_model=schemas.ProcessSurveyResponse)
async def process_survey(
    survey_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Triggers the AI detection, confidence filtering, and geotagging pipeline on a survey.
    """
    survey = crud.get_survey(db, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found.")

    crud.update_survey_status(db, survey_id, "processing")
    background_tasks.add_task(bg_process_survey, survey_id)

    return {
        "survey_id": survey_id,
        "status": "processing",
        "message": "AI detection pipeline has been launched in the background."
    }


@router.get("", response_model=schemas.SurveyListResponse)
def list_surveys(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all uploaded surveys with their processing statuses and detection tier counts.
    """
    surveys = crud.get_surveys(db, skip=skip, limit=limit)
    total = db.query(models.Survey).count()
    return {"total": total, "surveys": surveys}


@router.get("/{survey_id}", response_model=schemas.SurveyDetailResponse)
def get_survey_detail(
    survey_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieve survey details, image metadata, and associated detections.
    """
    survey = crud.get_survey(db, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found.")

    image_rel_filename = os.path.basename(survey.image_path)
    image_url = f"/static/uploads/{image_rel_filename}"

    # Format detections
    formatted_detections = []
    for d in survey.detections:
        det_dict = schemas.DetectionResponse.model_validate(d).model_dump()
        det_dict["bbox"] = [d.bbox_x, d.bbox_y, d.bbox_width, d.bbox_height]
        det_dict["filter_details"] = d.filter_details
        formatted_detections.append(det_dict)

    # Sort detections by confidence descending
    formatted_detections.sort(key=lambda x: x["confidence_score"], reverse=True)

    summary = schemas.SurveySummary.model_validate(survey).model_dump()
    return {
        **summary,
        "image_url": image_url,
        "nadir_x": survey.nadir_x,
        "error_message": survey.error_message,
        "detections": formatted_detections
    }


@router.get("/{survey_id}/detections", response_model=List[schemas.DetectionResponse])
def get_survey_detections(
    survey_id: str,
    min_confidence: Optional[float] = Query(None, ge=0, le=100),
    tier: Optional[str] = Query(None, pattern="^(High|Medium|Low)$"),
    predicted_class: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    Get filtered list of detections for a survey.
    """
    survey = crud.get_survey(db, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found.")

    detections = crud.get_detections_for_survey(
        db=db,
        survey_id=survey_id,
        min_confidence=min_confidence,
        tier=tier,
        predicted_class=predicted_class
    )
    
    results = []
    for d in detections:
        det_dict = schemas.DetectionResponse.model_validate(d).model_dump()
        det_dict["bbox"] = [d.bbox_x, d.bbox_y, d.bbox_width, d.bbox_height]
        det_dict["filter_details"] = d.filter_details
        results.append(det_dict)
        
    return results


@router.get("/{survey_id}/report")
def download_survey_report(
    survey_id: str,
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db)
):
    """
    Generate and download the structured report in CSV or JSON format.
    """
    survey = crud.get_survey(db, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found.")

    detections = crud.get_detections_for_survey(db, survey_id)
    
    det_list = []
    for d in detections:
        det_list.append({
            "detection_id": d.id,
            "survey_id": d.survey_id,
            "ping_index": d.ping_index,
            "latitude": d.latitude,
            "longitude": d.longitude,
            "depth_m": d.depth_m,
            "bbox_x": d.bbox_x,
            "bbox_y": d.bbox_y,
            "bbox_width": d.bbox_width,
            "bbox_height": d.bbox_height,
            "estimated_size_m": d.estimated_size_m,
            "predicted_class": d.predicted_class,
            "confidence_score": d.confidence_score,
            "confidence_tier": d.confidence_tier,
            "timestamp": d.timestamp,
            "source_file": survey.filename
        })

    survey_meta = {
        "id": survey.id,
        "title": survey.title,
        "filename": survey.filename,
        "status": survey.status,
        "created_at": survey.created_at.isoformat() if survey.created_at else None,
        "total_detections": survey.total_detections,
        "high_tier_count": survey.high_tier_count,
        "medium_tier_count": survey.medium_tier_count,
        "low_tier_count": survey.low_tier_count
    }

    report_content = build_detection_report(
        detections=det_list,
        survey_meta=survey_meta,
        output_format=format
    )

    if format == "csv":
        return Response(
            content=report_content,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="seaguard_{survey_id}_report.csv"'}
        )
    else:
        return Response(
            content=report_content,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="seaguard_{survey_id}_report.json"'}
        )


@router.delete("/{survey_id}")
def delete_survey(
    survey_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete survey record and its associated image files and thumbnails from disk.
    """
    survey = crud.get_survey(db, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found.")

    # Remove files on disk
    if survey.image_path and os.path.exists(survey.image_path):
        try:
            os.remove(survey.image_path)
        except Exception:
            pass
            
    if survey.metadata_path and os.path.exists(survey.metadata_path):
        try:
            os.remove(survey.metadata_path)
        except Exception:
            pass

    # Delete thumbnails matching survey prefix
    for thumb_file in os.listdir(settings.THUMBNAILS_DIR):
        if thumb_file.startswith(survey_id):
            try:
                os.remove(settings.THUMBNAILS_DIR / thumb_file)
            except Exception:
                pass

    crud.delete_survey(db, survey_id)
    return {"message": f"Survey {survey_id} deleted successfully."}


@router.post("/demo/create", response_model=schemas.SurveySummary, status_code=201)
def create_demo(
    req: schemas.DemoSurveyRequest,
    db: Session = Depends(get_db)
):
    """
    Generates a full synthetic sonar survey and processes it immediately
    for instant 1-click exploration.
    """
    survey = create_sample_demo_survey(
        db=db,
        title=req.title or "Demo Mission: Monterey Canyon",
        scenario=req.scenario or "coastal",
        num_debris=req.num_debris or 4
    )
    return survey

@router.get("/{survey_id}/stats")
def get_survey_stats(
    survey_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns aggregated statistics for a survey: class breakdown, tier counts,
    average confidence, shadow detection rate, and bounding box distributions.
    """
    survey = crud.get_survey(db, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found.")
    
    detections = crud.get_detections_for_survey(db, survey_id)
    
    total = len(detections)
    if total == 0:
        return {
            "survey_id": survey_id,
            "total": 0,
            "class_breakdown": {},
            "tier_breakdown": {"High": 0, "Medium": 0, "Low": 0},
            "avg_confidence": 0,
            "shadow_detection_rate": 0,
            "avg_detector_score": 0,
            "avg_shadow_score": 0,
            "avg_shape_score": 0,
        }
    
    class_breakdown = {}
    tier_breakdown = {"High": 0, "Medium": 0, "Low": 0}
    shadow_count = 0
    
    for d in detections:
        class_breakdown[d.predicted_class] = class_breakdown.get(d.predicted_class, 0) + 1
        if d.confidence_tier in tier_breakdown:
            tier_breakdown[d.confidence_tier] += 1
        if d.shadow_detected:
            shadow_count += 1
    
    avg_confidence = round(sum(d.confidence_score for d in detections) / total, 1)
    avg_detector = round(sum(d.detector_score for d in detections) / total, 1)
    avg_shadow = round(sum(d.shadow_score for d in detections) / total, 1)
    avg_shape = round(sum(d.shape_score for d in detections) / total, 1)
    
    return {
        "survey_id": survey_id,
        "total": total,
        "class_breakdown": class_breakdown,
        "tier_breakdown": tier_breakdown,
        "avg_confidence": avg_confidence,
        "shadow_detection_rate": round((shadow_count / total) * 100, 1),
        "avg_detector_score": avg_detector,
        "avg_shadow_score": avg_shadow,
        "avg_shape_score": avg_shape,
    }
