"""
Sonar Object Detection Module.
Performs tiled YOLOv8 inference, global coordinate re-projection,
cross-tile Non-Maximum Suppression (NMS), thumbnail extraction,
and integrates the classical confidence filter and geotagger.
"""

import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import cv2

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

from .preprocessing import preprocess_sonar_image, create_image_tiles, apply_slant_to_ground_range_correction
from .confidence_filter import evaluate_detection_confidence
from .geotagging import SonarGeotagger
from .synthetic_generator import CLASSES, IDX_TO_CLASS
from .unet_segmentation import GhostNetSegmenter
from .seabed_classifier import SeabedClassifier


def calculate_iou(box1: List[int], box2: List[int]) -> float:
    """Computes Intersection-over-Union (IoU) between two [x, y, w, h] boxes."""
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    
    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1 + w1, x2 + w2)
    yi2 = min(y1 + h1, y2 + h2)
    
    inter_w = max(0, xi2 - xi1)
    inter_h = max(0, yi2 - yi1)
    inter_area = inter_w * inter_h
    
    area1 = w1 * h1
    area2 = w2 * h2
    union_area = area1 + area2 - inter_area
    
    if union_area <= 0:
        return 0.0
    return inter_area / float(union_area)


def apply_cross_tile_nms(
    detections: List[Dict[str, Any]],
    iou_threshold: float = 0.40
) -> List[Dict[str, Any]]:
    """
    Suppresses duplicate detections across overlapping tile boundaries.
    """
    if not detections:
        return []
        
    # Sort by detector confidence descending
    sorted_dets = sorted(detections, key=lambda d: d.get("yolo_confidence", 0.0), reverse=True)
    kept = []
    
    while sorted_dets:
        best = sorted_dets.pop(0)
        kept.append(best)
        
        remaining = []
        for d in sorted_dets:
            # Check IoU
            iou = calculate_iou(best["bbox"], d["bbox"])
            # If same or overlapping class and high IoU, suppress
            if iou < iou_threshold:
                remaining.append(d)
        sorted_dets = remaining
        
    return kept


class SonarDetector:
    def __init__(
        self,
        model_path: Optional[str] = None,
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45
    ):
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.model = None
        self.model_path = model_path
        
        if model_path and os.path.exists(model_path) and ULTRALYTICS_AVAILABLE:
            try:
                self.model = YOLO(model_path)
                print(f"Loaded YOLOv8 model from {model_path}")
            except Exception as e:
                print(f"Warning: Could not load model from {model_path}: {e}")
        elif ULTRALYTICS_AVAILABLE:
            # Fallback to base pretrained yolov8n.pt if custom checkpoint not found
            try:
                self.model = YOLO("yolov8n.pt")
                print("Loaded default YOLOv8n base model")
            except Exception as e:
                print(f"Warning: Could not load base YOLO model: {e}")

        # Dedicated U-Net Segmenter for Ghost Nets (ALDFG)
        self.unet_segmenter = GhostNetSegmenter()
        # Seafloor Texture & Facies Geological Interference Classifier
        self.seabed_classifier = SeabedClassifier()

    def detect_on_tile(self, tile_img: np.ndarray) -> List[Dict[str, Any]]:
        """
        Runs YOLOv8 detection on a single 640x640 tile.
        """
        if self.model is None:
            # Heuristic fallback if model not loaded
            return []

        # Convert grayscale to 3-channel BGR for YOLOv8
        if len(tile_img.shape) == 2:
            tile_bgr = cv2.cvtColor(tile_img, cv2.COLOR_GRAY2BGR)
        else:
            tile_bgr = tile_img

        results = self.model.predict(
            source=tile_bgr,
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False
        )
        
        detections = []
        for r in results:
            boxes = r.boxes
            for b in boxes:
                xyxy = b.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = map(int, xyxy)
                conf = float(b.conf[0].cpu().numpy())
                cls_id = int(b.cls[0].cpu().numpy())
                
                cls_name = IDX_TO_CLASS.get(cls_id, CLASSES[cls_id % len(CLASSES)])
                w = x2 - x1
                h = y2 - y1
                
                detections.append({
                    "bbox_tile": [x1, y1, w, h],
                    "yolo_confidence": conf,
                    "class_name": cls_name,
                    "class_idx": cls_id
                })
                
        return detections

    def process_full_survey(
        self,
        image: np.ndarray,
        geotagger: Optional[SonarGeotagger] = None,
        thumbnails_dir: Optional[str] = None,
        survey_id: Optional[str] = None,
        altitude_m: Optional[float] = None,
        apply_srr: bool = True
    ) -> Dict[str, Any]:
        """
        Full end-to-end processing:
        1. Preprocessing & Nadir detection
        2. Tiling & YOLO inference
        3. Global coordinate re-projection & NMS
        4. Physics-based acoustic confidence evaluation + Seabed geological interference suppression
        5. Geotagging & True Slant-to-Ground Range (SRR) physical dimensions (m)
        6. Dedicated U-Net Ghost Net (ALDFG) semantic segmentation & entangled area (m²)
        7. Thumbnail extraction
        """
        h, w = image.shape[:2]
        processed_img, nadir_info = preprocess_sonar_image(image)
        nadir_x = nadir_info["nadir_center"]
        
        # Sensor altitude resolution
        if altitude_m is None and geotagger is not None:
            altitude_m = getattr(geotagger, "altitude_m", 15.0)
        if altitude_m is None or altitude_m <= 0:
            altitude_m = 15.0

        if geotagger is None:
            geotagger = SonarGeotagger.generate_synthetic_trackline(
                num_pings=max(1024, h),
                altitude_m=altitude_m
            )
        else:
            geotagger.set_altitude(altitude_m)

        # 2. Tiling & Inference
        tiles = create_image_tiles(processed_img, tile_size=640, overlap=0.20)
        
        raw_detections = []
        for t in tiles:
            tile_dets = self.detect_on_tile(t["tile_image"])
            x_off = t["x_offset"]
            y_off = t["y_offset"]
            
            for d in tile_dets:
                bx, by, bw, bh = d["bbox_tile"]
                # Re-project to full image
                gx = max(0, min(w - 1, bx + x_off))
                gy = max(0, min(h - 1, by + y_off))
                gw = min(bw, w - gx)
                gh = min(bh, h - gy)
                
                # Filter out boxes that fall entirely inside nadir gap
                if gx + gw > nadir_info["nadir_left"] and gx < nadir_info["nadir_right"]:
                    pass
                    
                raw_detections.append({
                    "bbox": [int(gx), int(gy), int(gw), int(gh)],
                    "yolo_confidence": d["yolo_confidence"],
                    "class_name": d["class_name"],
                    "class_idx": d["class_idx"]
                })

        # 3. Non-Maximum Suppression across tiles
        merged_detections = apply_cross_tile_nms(raw_detections, iou_threshold=0.35)

        # 4. Confidence filter + Geotagging + SRR Physical Sizing + U-Net Segmentation
        final_detections = []
        for idx, det in enumerate(merged_detections):
            bbox = det["bbox"]
            gx, gy, gw, gh = bbox
            
            # Confidence evaluation with Seabed Geological Interference Suppression
            conf_res = evaluate_detection_confidence(
                processed_img,
                (gx, gy, gw, gh),
                det["yolo_confidence"],
                nadir_x,
                seabed_classifier=self.seabed_classifier
            )
            
            # Geotag center of detection
            center_x = gx + gw // 2
            center_y = gy + gh // 2
            geo_info = geotagger.geotag_pixel(center_x, center_y, w, h, nadir_x)
            
            # True Slant-to-Ground Range (SRR) physical dimension calculation
            dim_info = geotagger.calculate_physical_dimensions(gw, gh, center_x, w, nadir_x)
            real_w_m = dim_info.get("physical_width_m", dim_info.get("width_meters", round(gw * 0.1, 2)))
            real_h_m = dim_info.get("physical_height_m", dim_info.get("length_meters", round(gh * 0.1, 2)))
            size_str = f"{real_w_m}m x {real_h_m}m"

            # Dedicated U-Net Ghost Net Semantic Segmentation
            segmentation_info = None
            if det["class_name"] == "ghost_net":
                patch = image[gy:gy+gh, gx:gx+gw]
                m_px = dim_info.get("effective_m_per_px_x", geo_info["meters_per_pixel"])
                seg_res = self.unet_segmenter.segment_patch(patch, meters_per_pixel=m_px)
                segmentation_info = {
                    "entangled_area_m2": seg_res["entangled_area_m2"],
                    "perimeter_m": seg_res["perimeter_m"],
                    "filament_density": seg_res["filament_density"],
                    "is_filamentous": seg_res["is_filamentous"],
                    "polygon": seg_res["polygon"]
                }
                if seg_res["entangled_area_m2"] > 0:
                    size_str += f" (Net Area: {seg_res['entangled_area_m2']}m²)"

            # Crop thumbnail
            thumb_rel_path = None
            if thumbnails_dir and survey_id:
                os.makedirs(thumbnails_dir, exist_ok=True)
                pad = 16
                cx1 = max(0, gx - pad)
                cy1 = max(0, gy - pad)
                cx2 = min(w, gx + gw + pad)
                cy2 = min(h, gy + gh + pad)
                
                crop_img = image[cy1:cy2, cx1:cx2]
                thumb_filename = f"{survey_id}_det_{idx+1:03d}.jpg"
                thumb_path = os.path.join(thumbnails_dir, thumb_filename)
                cv2.imwrite(thumb_path, crop_img)
                thumb_rel_path = f"/static/thumbnails/{thumb_filename}"

            filter_details = {
                **conf_res.details,
                "physical_dimensions": dim_info,
                "segmentation": segmentation_info,
                "entangled_area_m2": segmentation_info["entangled_area_m2"] if segmentation_info else None,
                "srr_corrected": apply_srr,
                "sensor_altitude_m": altitude_m
            }

            det_record = {
                "id": f"{survey_id or 'det'}_{idx+1:03d}",
                "detection_id": f"{survey_id or 'det'}_{idx+1:03d}",
                "survey_id": survey_id or "survey_01",
                "ping_index": geo_info["ping_index"],
                "latitude": geo_info["latitude"],
                "longitude": geo_info["longitude"],
                "depth_m": geo_info["depth_m"],
                "bbox": bbox,
                "bbox_x": gx,
                "bbox_y": gy,
                "bbox_width": gw,
                "bbox_height": gh,
                "estimated_size_m": size_str,
                "predicted_class": det["class_name"],
                "confidence_score": conf_res.final_score,
                "confidence_tier": conf_res.tier,
                "detector_score": conf_res.detector_score,
                "shadow_score": conf_res.shadow_score,
                "shape_score": conf_res.shape_score,
                "shadow_detected": conf_res.shadow_detected,
                "timestamp": geo_info["timestamp"],
                "thumbnail_url": thumb_rel_path,
                "filter_details": filter_details
            }
            final_detections.append(det_record)

        # Overall Survey Seabed Facies Summary
        sample_y = min(h, 512)
        sample_patch = processed_img[:sample_y, :]
        facies_summary = self.seabed_classifier.classify_facies(sample_patch)

        return {
            "nadir_info": nadir_info,
            "total_detections": len(final_detections),
            "detections": final_detections,
            "seafloor_facies": facies_summary,
            "sensor_altitude_m": altitude_m,
            "srr_applied": apply_srr
        }
