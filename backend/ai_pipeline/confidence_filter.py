"""
Classical Physics-Based Confidence Scoring & Noise-Filtering Module.
Validates side-scan sonar detections by analyzing acoustic specular highlights,
physics-consistent acoustic shadow formation (relative to nadir angle),
and morphological/texture descriptors.
"""

from dataclasses import dataclass
from typing import Dict, Any, Tuple, Optional
import numpy as np
import cv2


@dataclass
class ConfidenceResult:
    final_score: float         # 0.0 to 100.0
    tier: str                  # "Low", "Medium", "High"
    shadow_score: float        # 0.0 to 100.0
    shape_score: float         # 0.0 to 100.0
    detector_score: float      # 0.0 to 100.0
    shadow_detected: bool
    details: Dict[str, Any]


def analyze_acoustic_shadow(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],  # x, y, w, h
    nadir_x: int
) -> Tuple[float, bool, Dict[str, Any]]:
    """
    Evaluates acoustic shadow consistency for a detection ROI:
    1. Determines acoustic propagation direction based on nadir position.
    2. Identifies highlight vs expected shadow region.
    3. Calculates shadow contrast ratio relative to local background.
    4. Evaluates directional alignment (shadow must be positioned AWAY from nadir).
    """
    img_h, img_w = image.shape[:2]
    x, y, w, h = bbox
    
    # Bound crop to image limits
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = max(4, min(w, img_w - x))
    h = max(4, min(h, img_h - y))
    
    roi = image[y:y+h, x:x+w]
    if roi.size == 0:
        return 0.0, False, {"error": "Empty ROI"}

    det_center_x = x + w / 2.0
    # Determine which side of nadir the detection is on
    # If Starboard (x > nadir_x): Sound travels Left -> Right. Shadow must be on RIGHT side.
    # If Port (x < nadir_x): Sound travels Right -> Left. Shadow must be on LEFT side.
    is_starboard = det_center_x >= nadir_x
    expected_shadow_side = "right" if is_starboard else "left"

    # Contextual background: sample local ring around ROI
    pad_x = max(8, int(w * 0.4))
    pad_y = max(8, int(h * 0.4))
    ctx_x1 = max(0, x - pad_x)
    ctx_y1 = max(0, y - pad_y)
    ctx_x2 = min(img_w, x + w + pad_x)
    ctx_y2 = min(img_h, y + h + pad_y)
    
    context_roi = image[ctx_y1:ctx_y2, ctx_x1:ctx_x2]
    local_bg_mean = float(np.median(context_roi)) if context_roi.size > 0 else 110.0
    if local_bg_mean < 30.0:
        local_bg_mean = 110.0

    # Split ROI horizontally into inner half (facing nadir) and outer half (away from nadir)
    half_w = max(2, w // 2)
    if is_starboard:
        # Starboard: inner is left half, outer is right half
        inner_region = roi[:, :half_w]
        outer_region = roi[:, half_w:]
    else:
        # Port: inner is right half, outer is left half
        inner_region = roi[:, half_w:]
        outer_region = roi[:, :half_w]

    inner_mean = float(np.mean(inner_region)) if inner_region.size > 0 else 100.0
    outer_mean = float(np.mean(outer_region)) if outer_region.size > 0 else 100.0
    
    # 1. Highlight intensity (90th percentile in ROI)
    highlight_val = float(np.percentile(roi, 92))
    # 2. Shadow intensity (10th percentile in outer region + adjacent shadow zone)
    shadow_val = float(np.percentile(outer_region, 12)) if outer_region.size > 0 else float(np.percentile(roi, 10))

    # Shadow contrast ratio: how dark is shadow compared to background?
    # Expected: shadow_val significantly below local_bg_mean
    shadow_depth = max(0.0, (local_bg_mean - shadow_val) / (local_bg_mean + 1e-5))
    
    # Highlight contrast: how bright is highlight compared to background?
    highlight_contrast = max(0.0, (highlight_val - local_bg_mean) / (255.0 - local_bg_mean + 1e-5))

    # Directional consistency check:
    # Highlight should be on inner side, shadow on outer side
    # Thus inner_mean should generally be noticeably higher than outer_mean
    directional_diff = (inner_mean - outer_mean) / (local_bg_mean + 1e-5)
    
    # Has a valid shadow if shadow_depth > 0.40 and outer region is darker than background
    has_shadow = (shadow_depth > 0.35) and (outer_mean < local_bg_mean * 0.85)

    # Calculate shadow score 0 to 100
    if has_shadow:
        raw_shadow_score = (shadow_depth * 65.0) + (highlight_contrast * 25.0) + (max(0.0, directional_diff) * 15.0)
        shadow_score = float(np.clip(raw_shadow_score * 100.0 / 85.0, 0.0, 100.0))
    else:
        # Penalize missing shadow
        raw_shadow_score = (shadow_depth * 30.0) + (highlight_contrast * 15.0)
        shadow_score = float(np.clip(raw_shadow_score, 0.0, 35.0))

    details = {
        "expected_shadow_side": expected_shadow_side,
        "local_bg_mean": round(local_bg_mean, 2),
        "highlight_val": round(highlight_val, 2),
        "shadow_val": round(shadow_val, 2),
        "shadow_depth": round(shadow_depth, 3),
        "directional_diff": round(directional_diff, 3),
        "has_shadow": bool(has_shadow)
    }

    return shadow_score, has_shadow, details


def analyze_shape_and_texture(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int]
) -> Tuple[float, Dict[str, Any]]:
    """
    Computes morphological compactness, aspect ratio, and texture contrast.
    """
    img_h, img_w = image.shape[:2]
    x, y, w, h = bbox
    
    x = max(0, min(x, img_w - 1))
    y = max(0, min(y, img_h - 1))
    w = max(4, min(w, img_w - x))
    h = max(4, min(h, img_h - y))
    
    roi = image[y:y+h, x:x+w]
    if roi.size == 0:
        return 50.0, {}

    # Aspect ratio & elongation
    aspect_ratio = max(w, h) / (min(w, h) + 1e-5)
    
    # Texture contrast via standard deviation
    roi_std = float(np.std(roi))
    
    # Otsu thresholding to find highlight blob morphology
    _, binary = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    solidity = 0.5
    if contours:
        largest_c = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_c)
        hull = cv2.convexHull(largest_c)
        hull_area = cv2.contourArea(hull)
        if hull_area > 0:
            solidity = area / hull_area

    # Shape score combines texture variance, aspect ratio, and solidity
    shape_score = float(np.clip((roi_std / 50.0) * 40.0 + (solidity * 35.0) + (min(aspect_ratio, 4.0) / 4.0) * 25.0, 0.0, 100.0))
    
    details = {
        "aspect_ratio": round(aspect_ratio, 2),
        "roi_std": round(roi_std, 2),
        "solidity": round(solidity, 2)
    }
    
    return shape_score, details


def evaluate_detection_confidence(
    image: np.ndarray,
    bbox: Tuple[int, int, int, int],
    yolo_confidence: float,
    nadir_x: int,
    seabed_classifier: Optional[Any] = None
) -> ConfidenceResult:
    """
    Blends YOLO detector confidence with physics-based acoustic shadow consistency,
    morphological shape metrics, and seabed geological interference suppression.
    
    Formula:
    Score = 0.50 * detector_score + 0.35 * shadow_score + 0.15 * shape_score
    If no acoustic shadow is detected, applies a heavy suppression factor (0.48x).
    If seabed geological interference is detected (e.g. natural rock reef or sand ripple crest),
    applies targeted geological suppression.
    """
    detector_score = float(np.clip(yolo_confidence * 100.0, 0.0, 100.0))
    
    shadow_score, has_shadow, shadow_details = analyze_acoustic_shadow(image, bbox, nadir_x)
    shape_score, shape_details = analyze_shape_and_texture(image, bbox)
    
    # Weighted composite score
    composite = (0.50 * detector_score) + (0.35 * shadow_score) + (0.15 * shape_score)
    
    # If acoustic shadow is missing for a candidate, heavily suppress confidence
    if not has_shadow:
        composite = composite * 0.48

    # Geological Interference Suppression (GLCM Haralick + Sand Ripple Harmonics)
    geo_details = None
    if seabed_classifier is not None:
        try:
            geo_details = seabed_classifier.evaluate_geological_interference(
                image,
                bbox,
                has_shadow=has_shadow,
                shadow_score=shadow_score / 100.0,
                shape_score=shape_score / 100.0
            )
            if geo_details.get("is_geological_risk", False):
                penalty = float(geo_details.get("penalty", 0.0))
                composite = composite * (1.0 - penalty)
        except Exception as e:
            geo_details = {"error": str(e)}

    final_score = float(np.clip(round(composite, 1), 0.0, 100.0))
    
    # Tier assignment
    if final_score >= 75.0:
        tier = "High"
    elif final_score >= 45.0:
        tier = "Medium"
    else:
        tier = "Low"

    details = {
        "shadow_details": shadow_details,
        "shape_details": shape_details,
        "suppression_applied": not has_shadow,
        "geological_analysis": geo_details
    }

    return ConfidenceResult(
        final_score=final_score,
        tier=tier,
        shadow_score=round(shadow_score, 1),
        shape_score=round(shape_score, 1),
        detector_score=round(detector_score, 1),
        shadow_detected=has_shadow,
        details=details
    )
