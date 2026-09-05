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
import cv2
import numpy as np

from ..database import get_db, SessionLocal
from ..config import settings
from .. import crud, schemas, models
from ..service import run_survey_pipeline, create_sample_demo_survey
from ai_pipeline.reporting import build_detection_report
from ai_pipeline.active_verification import (
    plan_secondary_rescan,
    match_secondary_detection,
    compare_observations,
    generate_synthetic_rescan_image
)
import json
from datetime import datetime, timezone

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


def generate_explainability_overlay(
    image: np.ndarray,
    detection: models.Detection,
    nadir_x: int
) -> np.ndarray:
    """
    Generates a physics explainability visual overlay on the sonar image for a detection:
    - Marks Nadir track line
    - Marks Target Bounding Box
    - Highlights specular reflection region (Inner half facing nadir)
    - Highlights acoustic shadow region (Outer half / shadow zone facing away from nadir)
    - Draws acoustic wave propagation directional arrow
    - Renders tactical HUD labels with physics scores and shadow verification status
    """
    h, w = image.shape[:2]
    img = image.copy()
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)

    bx, by, bw, bh = detection.bbox_x, detection.bbox_y, detection.bbox_width, detection.bbox_height
    
    # Bound crop to image limits
    bx = max(0, min(bx, w - 1))
    by = max(0, min(by, h - 1))
    bw = max(4, min(bw, w - bx))
    bh = max(4, min(bh, h - by))

    det_cx = bx + bw / 2.0
    det_cy = by + bh / 2.0
    is_starboard = det_cx >= nadir_x
    side_label = "STARBOARD" if is_starboard else "PORT"
    expected_side = "RIGHT" if is_starboard else "LEFT"

    # Define crop bounding box for focused forensic inspection (+140px context)
    pad_ctx_x = max(60, int(bw * 1.5))
    pad_ctx_y = max(60, int(bh * 1.5))
    crop_x1 = max(0, bx - pad_ctx_x)
    crop_y1 = max(0, by - pad_ctx_y)
    crop_x2 = min(w, bx + bw + pad_ctx_x)
    crop_y2 = min(h, by + bh + pad_ctx_y)

    # Work on crop canvas
    crop = img[crop_y1:crop_y2, crop_x1:crop_x2].copy()
    ch, cw = crop.shape[:2]

    # Adjusted coordinates relative to crop
    rx = bx - crop_x1
    ry = by - crop_y1
    rcx = rx + bw // 2
    rcy = ry + bh // 2

    # Draw semi-transparent overlay layer
    overlay = crop.copy()

    # Split ROI into Highlight (inner facing nadir) and Shadow (outer facing away)
    half_w = max(2, bw // 2)
    if is_starboard:
        # Inner = left half of bbox, Outer/Shadow = right half + extension
        hl_x1, hl_y1, hl_x2, hl_y2 = rx, ry, rx + half_w, ry + bh
        sh_x1, sh_y1, sh_x2, sh_y2 = rx + half_w, ry, min(cw, rx + bw + int(bw * 0.8)), ry + bh
        arrow_start = (max(0, rx - 30), rcy)
        arrow_end = (min(cw - 10, rx + bw + int(bw * 0.9)), rcy)
    else:
        # Inner = right half of bbox, Outer/Shadow = left half + extension
        hl_x1, hl_y1, hl_x2, hl_y2 = rx + half_w, ry, rx + bw, ry + bh
        sh_x1, sh_y1, sh_x2, sh_y2 = max(0, rx - int(bw * 0.8)), ry, rx + half_w, ry + bh
        arrow_start = (min(cw, rx + bw + 30), rcy)
        arrow_end = (max(10, rx - int(bw * 0.9)), rcy)

    # Draw Highlight area in Green/Cyan tint
    cv2.rectangle(overlay, (hl_x1, hl_y1), (hl_x2, hl_y2), (0, 255, 128), -1)
    # Draw Shadow area in Orange/Red tint
    cv2.rectangle(overlay, (sh_x1, sh_y1), (sh_x2, sh_y2), (0, 100, 255), -1)

    # Blend overlay with 32% opacity
    cv2.addWeighted(overlay, 0.32, crop, 0.68, 0, crop)

    # Draw sharp borders
    cv2.rectangle(crop, (rx, ry), (rx + bw, ry + bh), (0, 240, 255), 2)
    cv2.rectangle(crop, (hl_x1, hl_y1), (hl_x2, hl_y2), (0, 255, 128), 1)
    cv2.rectangle(crop, (sh_x1, sh_y1), (sh_x2, sh_y2), (0, 100, 255), 1)

    # Draw acoustic propagation beam arrow
    cv2.arrowedLine(crop, arrow_start, arrow_end, (0, 240, 255), 2, tipLength=0.2)

    # Draw Nadir track if within crop context
    rel_nadir_x = nadir_x - crop_x1
    if 0 <= rel_nadir_x < cw:
        cv2.line(crop, (rel_nadir_x, 0), (rel_nadir_x, ch), (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(crop, "NADIR TRACKLINE", (rel_nadir_x + 4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)

    # Top HUD Banner
    hud_h = 42
    hud_bg = np.zeros((hud_h, cw, 3), dtype=np.uint8)
    hud_bg[:] = (15, 23, 42)  # Slate-900
    
    cls_text = f"TARGET: {detection.predicted_class.upper()} [{detection.confidence_score:.1f}%]"
    phys_status = "SHADOW VERIFIED" if detection.shadow_detected else "SHADOW SUPPRESSED"
    phys_color = (0, 255, 128) if detection.shadow_detected else (0, 100, 255)
    
    cv2.putText(hud_bg, cls_text, (8, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 240, 255), 1, cv2.LINE_AA)
    cv2.putText(hud_bg, f"PHYSICS: {phys_status} | {side_label} (PROPAGATION: {expected_side})", (8, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.34, phys_color, 1, cv2.LINE_AA)
    
    score_summary = f"DET: {detection.detector_score:.0f}% | SHD: {detection.shadow_score:.0f}% | SHP: {detection.shape_score:.0f}%"
    text_size = cv2.getTextSize(score_summary, cv2.FONT_HERSHEY_SIMPLEX, 0.34, 1)[0]
    score_x = max(8, cw - text_size[0] - 10)
    cv2.putText(hud_bg, score_summary, (score_x, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (200, 200, 200), 1, cv2.LINE_AA)

    # Stack HUD on top of crop
    final_img = np.vstack([hud_bg, crop])
    return final_img


@router.get("/{survey_id}/detections/{detection_id}/explainability-image")
def get_detection_explainability_image(
    survey_id: str,
    detection_id: str,
    db: Session = Depends(get_db)
):
    """
    Generates and returns an Explainable Sonar forensic visual evidence overlay image
    showing the exact bounding box, highlight region, expected acoustic cast shadow,
    and nadir trackline propagation vector.
    """
    survey = crud.get_survey(db, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found.")

    detection = db.query(models.Detection).filter(
        models.Detection.id == detection_id,
        models.Detection.survey_id == survey_id
    ).first()

    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found.")

    if not os.path.exists(survey.image_path):
        raise HTTPException(status_code=404, detail="Survey image file not found on disk.")

    # Load original image
    img = cv2.imread(survey.image_path)
    if img is None:
        raise HTTPException(status_code=500, detail="Failed to load survey sonar image.")

    h, w = img.shape[:2]
    nadir_x = survey.nadir_x if survey.nadir_x is not None else w // 2

    # Generate explainability overlay
    overlay_img = generate_explainability_overlay(img, detection, nadir_x)

    # Encode as PNG
    success, buffer = cv2.imencode(".png", overlay_img)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode explainability image.")

    return Response(content=buffer.tobytes(), media_type="image/png")


@router.post("/{survey_id}/detections/{detection_id}/verify", response_model=schemas.VerificationPlanResponse)
def plan_detection_verification(
    survey_id: str,
    detection_id: str,
    db: Session = Depends(get_db)
):
    """
    Evaluates verification need and generates an adaptive secondary survey
    observation plan and waypoint trajectory for a given sonar detection.
    """
    survey = crud.get_survey(db, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found.")

    detection = db.query(models.Detection).filter(
        models.Detection.id == detection_id,
        models.Detection.survey_id == survey_id
    ).first()

    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found.")

    det_dict = {
        "id": detection.id,
        "bbox": detection.bbox,
        "class": detection.predicted_class,
        "predicted_class": detection.predicted_class,
        "confidence_score": detection.confidence_score,
        "confidence_tier": detection.confidence_tier,
        "latitude": detection.latitude,
        "longitude": detection.longitude,
        "detector_score": detection.detector_score,
        "shadow_score": detection.shadow_score,
        "shape_score": detection.shape_score,
        "shadow_detected": detection.shadow_detected
    }

    nadir_x = survey.nadir_x if survey.nadir_x is not None else (survey.image_width // 2 if survey.image_width else 512)
    image_width = survey.image_width if survey.image_width else 1024
    slant_range_m = survey.slant_range_m if survey.slant_range_m else 75.0

    plan = plan_secondary_rescan(
        detection=det_dict,
        nadir_x=nadir_x,
        image_width=image_width,
        slant_range_m=slant_range_m
    )

    return {
        "survey_id": survey_id,
        "detection_id": detection_id,
        "target_info": plan["target_info"],
        "verification_need": plan["verification_need"],
        "recommended_observation": plan["recommended_observation"],
        "simulation_mode": plan["simulation_mode"],
        "geospatial_routes": plan["geospatial_routes"]
    }


@router.post("/{survey_id}/detections/{detection_id}/verify/rescan", response_model=schemas.VerificationResultResponse)
async def execute_detection_rescan(
    survey_id: str,
    detection_id: str,
    mode: str = Form("simulation"),
    scenario: str = Form("confirm"),
    rescan_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """
    Executes a virtual rescan by either processing an uploaded secondary sonar image
    or running a deterministic acoustic simulation scenario (Scenario A Confirm / Scenario B Reject).
    Passes secondary image through the AI & physics pipeline, matches target, and compares evidence.
    """
    survey = crud.get_survey(db, survey_id)
    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found.")

    detection = db.query(models.Detection).filter(
        models.Detection.id == detection_id,
        models.Detection.survey_id == survey_id
    ).first()

    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found.")

    primary_dict = {
        "id": detection.id,
        "class": detection.predicted_class,
        "predicted_class": detection.predicted_class,
        "confidence_score": detection.confidence_score,
        "confidence_tier": detection.confidence_tier,
        "detector_score": detection.detector_score,
        "shadow_score": detection.shadow_score,
        "shape_score": detection.shape_score,
        "shadow_detected": detection.shadow_detected,
        "bbox": detection.bbox
    }

    # Prepare rescan image and detections
    secondary_img = None
    secondary_detections = []

    if mode == "upload" and rescan_image and rescan_image.filename:
        # User uploaded a custom secondary sonar image
        content = await rescan_image.read()
        nparr = np.frombuffer(content, np.uint8)
        secondary_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if secondary_img is None:
            raise HTTPException(status_code=400, detail="Invalid secondary sonar image.")
        
        # Process through detection & confidence filter pipeline
        try:
            from ai_pipeline.detection import SonarDetector
            detector = SonarDetector(confidence_threshold=0.20)
            raw_dets = detector.detect(secondary_img)
        except Exception:
            raw_dets = []
        
        sec_h, sec_w = secondary_img.shape[:2]
        sec_nadir_x = sec_w // 2
        
        for d in raw_dets:
            conf_eval = evaluate_detection_confidence(
                image=secondary_img,
                bbox=d["bbox"],
                yolo_confidence=d.get("confidence", 0.5),
                nadir_x=sec_nadir_x
            )
            secondary_detections.append({
                "class": d["class"],
                "predicted_class": d["class"],
                "confidence": round(conf_eval.final_score / 100.0, 3),
                "confidence_score": conf_eval.final_score,
                "confidence_tier": conf_eval.tier,
                "detector_score": conf_eval.detector_score,
                "shadow_score": conf_eval.shadow_score,
                "shape_score": conf_eval.shape_score,
                "shadow_detected": conf_eval.shadow_detected,
                "bbox": d["bbox"]
            })
    else:
        # Simulation Mode (Scenario A: Confirm, Scenario B: Reject / False Alarm)
        secondary_img, secondary_detections = generate_synthetic_rescan_image(
            scenario=scenario,
            target_class=detection.predicted_class,
            primary_bbox=detection.bbox
        )

    # Save secondary rescan image to disk
    sec_filename = f"{survey_id}_{detection_id}_rescan.png"
    sec_save_path = settings.UPLOADS_DIR / sec_filename
    cv2.imwrite(str(sec_save_path), secondary_img)

    # Associate target deterministically
    matched_sec, match_score = match_secondary_detection(
        primary_bbox=detection.bbox,
        primary_class=detection.predicted_class,
        secondary_detections=secondary_detections,
        image_shape=secondary_img.shape[:2]
    )

    # Compare evidence
    comparison = compare_observations(
        primary_evidence=primary_dict,
        secondary_evidence=matched_sec,
        match_score=match_score
    )

    # Build full result
    now_iso = datetime.now(timezone.utc).isoformat()
    result = {
        "survey_id": survey_id,
        "detection_id": detection_id,
        "status": comparison["status"],
        "verdict_title": comparison["verdict_title"],
        "verdict_badge": comparison["verdict_badge"],
        "verdict_color": comparison["verdict_color"],
        "summary_text": comparison["summary_text"],
        "target_associated": comparison["target_associated"],
        "match_score": comparison["match_score"],
        "class_consistent": comparison["class_consistent"],
        "confidence_delta": comparison["confidence_delta"],
        "shadow_delta": comparison["shadow_delta"],
        "shape_delta": comparison["shape_delta"],
        "detector_delta": comparison["detector_delta"],
        "evidence_strengthened": comparison["evidence_strengthened"],
        "primary": comparison["primary"],
        "secondary": comparison["secondary"],
        "scientific_notes": comparison["scientific_notes"],
        "recommended_action": comparison["recommended_action"],
        "secondary_image_url": f"/api/surveys/{survey_id}/detections/{detection_id}/verification-image",
        "created_at": now_iso
    }

    # Persist verification record in Detection model
    detection.verification_json = json.dumps(result)
    db.commit()

    return result


@router.get("/{survey_id}/detections/{detection_id}/verification", response_model=schemas.VerificationResultResponse)
def get_detection_verification(
    survey_id: str,
    detection_id: str,
    db: Session = Depends(get_db)
):
    """
    Retrieves stored active verification record for a given detection.
    """
    detection = db.query(models.Detection).filter(
        models.Detection.id == detection_id,
        models.Detection.survey_id == survey_id
    ).first()

    if not detection:
        raise HTTPException(status_code=404, detail="Detection not found.")

    if not detection.verification_record:
        raise HTTPException(status_code=404, detail="No active verification record found for this detection.")

    return detection.verification_record


@router.get("/{survey_id}/detections/{detection_id}/verification-image")
def get_detection_verification_image(
    survey_id: str,
    detection_id: str,
    db: Session = Depends(get_db)
):
    """
    Serves the secondary rescan sonar image.
    """
    sec_filename = f"{survey_id}_{detection_id}_rescan.png"
    sec_save_path = settings.UPLOADS_DIR / sec_filename

    if not os.path.exists(sec_save_path):
        raise HTTPException(status_code=404, detail="Secondary rescan image not found on disk.")

    img = cv2.imread(str(sec_save_path))
    if img is None:
        raise HTTPException(status_code=500, detail="Failed to load secondary rescan image.")

    success, buffer = cv2.imencode(".png", img)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to encode secondary rescan image.")

    return Response(content=buffer.tobytes(), media_type="image/png")


