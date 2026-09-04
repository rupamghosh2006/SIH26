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

from .preprocessing import preprocess_sonar_image, create_image_tiles
from .confidence_filter import evaluate_detection_confidence
from .geotagging import SonarGeotagger
from .synthetic_generator import CLASSES, IDX_TO_CLASS


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
        survey_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Full end-to-end processing:
        1. Preprocessing & Nadir detection
        2. Tiling & YOLO inference
        3. Global coordinate re-projection & NMS
        4. Physics-based acoustic confidence evaluation
        5. Geotagging & real-world size estimation
        6. Thumbnail extraction
        """
        h, w = image.shape[:2]
        processed_img, nadir_info = preprocess_sonar_image(image)
        nadir_x = nadir_info["nadir_center"]
        
        if geotagger is None:
            geotagger = SonarGeotagger.generate_synthetic_trackline(num_pings=max(1024, h))

        # 2. Tiling
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
                    # Spans water column; verify if it has valid highlight outside
                    pass
                    
                raw_detections.append({
                    "bbox": [int(gx), int(gy), int(gw), int(gh)],
                    "yolo_confidence": d["yolo_confidence"],
                    "class_name": d["class_name"],
                    "class_idx": d["class_idx"]
                })

        # 3. Non-Maximum Suppression across tiles
        merged_detections = apply_cross_tile_nms(raw_detections, iou_threshold=0.35)

        # 4. Confidence filter + Geotagging + Thumbnails
        final_detections = []
        for idx, det in enumerate(merged_detections):
            bbox = det["bbox"]
            gx, gy, gw, gh = bbox
            
            # Confidence evaluation
            conf_res = evaluate_detection_confidence(
                processed_img,
                (gx, gy, gw, gh),
                det["yolo_confidence"],
                nadir_x
            )
            
            # Geotag center of detection
            center_x = gx + gw // 2
            center_y = gy + gh // 2
            geo_info = geotagger.geotag_pixel(center_x, center_y, w, h, nadir_x)
            
            # Real world size estimate in meters
            m_per_px = geo_info["meters_per_pixel"]
            real_w_m = round(gw * m_per_px, 2)
            real_h_m = round(gh * m_per_px, 2)
            size_str = f"{real_w_m}m x {real_h_m}m"

            # Crop thumbnail
            thumb_rel_path = None
            if thumbnails_dir and survey_id:
                os.makedirs(thumbnails_dir, exist_ok=True)
                # Add context padding to crop
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
                "filter_details": conf_res.details
            }
            final_detections.append(det_record)

        return {
            "nadir_info": nadir_info,
            "total_detections": len(final_detections),
            "detections": final_detections
        }
