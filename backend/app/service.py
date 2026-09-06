"""
Pipeline Orchestration Service for VARUNA AI.
Coordinates survey ingestion, async AI pipeline execution, thumbnail extraction,
and instant demo survey generation.
"""

import os
import uuid
import cv2
import numpy as np
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from .config import settings
from . import crud, models
from ai_pipeline.synthetic_generator import SyntheticSonarGenerator
from ai_pipeline.detection import SonarDetector
from ai_pipeline.geotagging import SonarGeotagger
from ai_pipeline.sonar_format_reader import SonarFormatReader

# Global detector instance cache
_detector_instance = None


def get_detector() -> SonarDetector:
    global _detector_instance
    if _detector_instance is None:
        model_p = str(settings.MODEL_PATH) if os.path.exists(settings.MODEL_PATH) else None
        _detector_instance = SonarDetector(
            model_path=model_p,
            conf_threshold=settings.CONF_THRESHOLD,
            iou_threshold=settings.IOU_THRESHOLD
        )
    return _detector_instance


def run_survey_pipeline(db: Session, survey_id: str) -> None:
    """
    Executes the full CV/AI detection pipeline on a survey record.
    """
    survey = crud.get_survey(db, survey_id)
    if not survey:
        print(f"Error: Survey {survey_id} not found.")
        return

    try:
        crud.update_survey_status(db, survey_id, status="processing")
        
        # 1. Read Image or Raw Hydrographic File (.xtf, .jsf, .sdf)
        if not os.path.exists(survey.image_path):
            raise FileNotFoundError(f"Sonar file not found at: {survey.image_path}")

        file_ext = os.path.splitext(survey.image_path)[1].lower()
        altitude_m = 15.0
        sonar_pings = None

        if file_ext in [".xtf", ".jsf", ".sdf"]:
            print(f"[VARUNA AI] Parsing raw hydrographic sonar stream: {survey.image_path}")
            sonar_data = SonarFormatReader.read_sonar_file(survey.image_path)
            image = sonar_data.waterfall_image
            if sonar_data.sensor_altitude_m > 0:
                altitude_m = sonar_data.sensor_altitude_m
            sonar_pings = sonar_data.ping_records

            # Save normalized waterfall image preview so UI can render it
            preview_filename = f"{survey.id}_waterfall.png"
            preview_path = str(settings.UPLOADS_DIR / preview_filename)
            cv2.imwrite(preview_path, image)
            survey.image_path = preview_path
            db.commit()
        else:
            image = cv2.imread(survey.image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError(f"Could not decode image at {survey.image_path}")

        h, w = image.shape[:2]

        # 2. Setup Geotagger with Sensor Altitude
        if survey.metadata_path and os.path.exists(survey.metadata_path):
            geotagger = SonarGeotagger.from_csv_or_json(
                survey.metadata_path,
                slant_range_m=survey.slant_range_m,
                altitude_m=altitude_m
            )
        elif sonar_pings and len(sonar_pings) > 0:
            geotagger = SonarGeotagger.from_ping_records(
                sonar_pings,
                slant_range_m=survey.slant_range_m,
                altitude_m=altitude_m
            )
        else:
            geotagger = SonarGeotagger.generate_synthetic_trackline(
                num_pings=max(1024, h),
                slant_range_m=survey.slant_range_m,
                altitude_m=altitude_m
            )

        # 3. Detection & Confidence Filtering
        detector = get_detector()
        results = detector.process_full_survey(
            image=image,
            geotagger=geotagger,
            thumbnails_dir=str(settings.THUMBNAILS_DIR),
            survey_id=survey_id,
            altitude_m=altitude_m,
            apply_srr=True
        )

        nadir_x = results["nadir_info"]["nadir_center"]
        detections = results["detections"]

        # 4. Save results to database
        crud.save_survey_results(
            db=db,
            survey_id=survey_id,
            detections=detections,
            nadir_x=nadir_x,
            image_width=w,
            image_height=h
        )
        print(f"[VARUNA AI] Successfully processed survey {survey_id}: {len(detections)} detections.")

    except Exception as e:
        import traceback
        traceback.print_exc()
        crud.update_survey_status(db, survey_id, status="failed", error_message=str(e))
        print(f"[VARUNA AI] Failed processing survey {survey_id}: {e}")


def create_sample_demo_survey(
    db: Session,
    title: str = "Demo Mission: Monterey Canyon Survey",
    scenario: str = "coastal",
    num_debris: int = 4
) -> models.Survey:
    """
    Generates a full synthetic survey with realistic side-scan sonar image,
    nav metadata, and immediately processes it through the pipeline.
    """
    survey_id = f"srv_{uuid.uuid4().hex[:10]}"
    image_filename = f"{survey_id}_sonar.jpg"
    image_path = str(settings.UPLOADS_DIR / image_filename)
    
    # Generate realistic waterfall image (e.g. 1024 x 1280)
    generator = SyntheticSonarGenerator(image_width=1024, image_height=1280)
    img_data, synthetic_targets = generator.generate_image_with_debris(num_objects=num_debris)
    
    cv2.imwrite(image_path, img_data)
    h, w = img_data.shape[:2]

    # Create survey in DB
    survey_data = {
        "id": survey_id,
        "title": title,
        "filename": image_filename,
        "image_path": image_path,
        "image_width": w,
        "image_height": h,
        "slant_range_m": settings.DEFAULT_SLANT_RANGE_M,
        "status": "uploaded"
    }
    db_survey = crud.create_survey(db, survey_data)

    # Process immediately
    run_survey_pipeline(db, survey_id)
    
    return crud.get_survey(db, survey_id)
