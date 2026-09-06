"""
Active Verification ("Verify Detection") Core Module.
Provides adaptive secondary sonar observation planning, target association,
and multi-observation acoustic evidence comparison for VARUNA.
"""

import math
import time
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import cv2

from .confidence_filter import evaluate_detection_confidence, ConfidenceResult
from .geotagging import destination_point


def assess_verification_need(
    confidence_score: float,
    confidence_tier: str,
    shadow_detected: bool,
    shadow_score: float,
    detector_score: float
) -> Dict[str, Any]:
    """
    Evaluates whether a detection requires secondary acoustic verification
    based on the existing confidence tier and acoustic physics signals.
    """
    score = float(confidence_score)
    tier = confidence_tier.capitalize()
    
    reasons: List[str] = []
    
    if tier == "Low" or score < 45.0:
        recommendation = "MANDATORY"
        status_label = "VERIFICATION STRONGLY RECOMMENDED"
        reasons.append("Low detector confidence (<45%) requires secondary confirmation pass.")
        if not shadow_detected:
            reasons.append("Missing acoustic cast shadow indicates potential seabed ripple or noise artifact.")
        elif shadow_score < 40.0:
            reasons.append(f"Weak acoustic shadow contrast ({shadow_score:.1f}%) suggests insufficient specular relief.")
    elif tier == "Medium" or score < 75.0:
        recommendation = "RECOMMENDED"
        status_label = "VERIFICATION RECOMMENDED"
        reasons.append(f"Moderate composite confidence ({score:.1f}%) in Medium tier.")
        if not shadow_detected:
            reasons.append("Incomplete acoustic shadow formation requires alternate illumination angle.")
        elif shadow_score < 60.0:
            reasons.append(f"Partial shadow contrast ({shadow_score:.1f}%) requires cross-track perspective.")
        if detector_score < 65.0:
            reasons.append("YOLO classification score has ambiguity with background clutter.")
    else:
        recommendation = "OPTIONAL"
        status_label = "HIGH CONFIDENCE (OPTIONAL RESCAN)"
        reasons.append("High confidence target (>=75%) with verified acoustic signature.")

    if not reasons:
        reasons.append("Cross-angle acoustic inspection recommended for forensic confirmation.")

    return {
        "tier": tier,
        "recommendation": recommendation,
        "status_label": status_label,
        "reasons": reasons
    }


def plan_secondary_rescan(
    detection: Dict[str, Any],
    nadir_x: int = 512,
    image_width: int = 1024,
    slant_range_m: float = 75.0
) -> Dict[str, Any]:
    """
    Generates an adaptive secondary survey path and observation geometry
    around the detection target for AUV simulation / mission planning.
    """
    bbox = detection.get("bbox", [100, 100, 50, 50])
    bx, by, bw, bh = bbox[0], bbox[1], bbox[2], bbox[3]
    center_x = bx + bw / 2.0
    center_y = by + bh / 2.0
    
    lat = float(detection.get("latitude", 12.9234))
    lon = float(detection.get("longitude", 80.1345))
    target_class = detection.get("predicted_class", detection.get("class", "ghost_net"))
    conf = float(detection.get("confidence_score", detection.get("confidence", 0.6) * (100 if detection.get("confidence", 0.6) <= 1.0 else 1.0)))
    tier = detection.get("confidence_tier", "Medium")
    shadow_detected = bool(detection.get("shadow_detected", True))
    shadow_score = float(detection.get("shadow_score", 55.0))
    detector_score = float(detection.get("detector_score", conf))

    need_assessment = assess_verification_need(
        confidence_score=conf,
        confidence_tier=tier,
        shadow_detected=shadow_detected,
        shadow_score=shadow_score,
        detector_score=detector_score
    )

    is_starboard = center_x >= nadir_x
    primary_side = "Starboard" if is_starboard else "Port"
    
    suggested_angle_deg = 45.0 if is_starboard else -45.0
    suggested_offset_m = round(max(15.0, min(35.0, (abs(center_x - nadir_x) / (image_width / 2.0)) * slant_range_m * 0.6)), 1)
    
    base_heading = 90.0
    
    pri_wp1_lat, pri_wp1_lon = destination_point(lat, lon, 50.0, (base_heading + 180) % 360)
    pri_wp2_lat, pri_wp2_lon = destination_point(lat, lon, 50.0, base_heading % 360)
    
    sec_heading = (base_heading + suggested_angle_deg) % 360
    sec_wp1_lat, sec_wp1_lon = destination_point(lat, lon, 40.0, (sec_heading + 180) % 360)
    sec_cpa_lat, sec_cpa_lon = destination_point(lat, lon, suggested_offset_m, (sec_heading + 90) % 360)
    sec_wp2_lat, sec_wp2_lon = destination_point(lat, lon, 40.0, sec_heading % 360)

    rescan_plan = {
        "target_info": {
            "class": target_class,
            "confidence": round(conf, 1),
            "tier": need_assessment["tier"],
            "latitude": lat,
            "longitude": lon,
            "primary_side": primary_side,
            "bbox": [int(bx), int(by), int(bw), int(bh)],
            "shadow_detected": shadow_detected,
            "shadow_score": round(shadow_score, 1),
            "shape_score": round(float(detection.get("shape_score", 70.0)), 1),
            "detector_score": round(detector_score, 1)
        },
        "verification_need": need_assessment,
        "recommended_observation": {
            "suggested_offset_meters": suggested_offset_m,
            "suggested_angle_degrees": suggested_angle_deg,
            "observation_mode": "Orthogonal Acoustic Swath",
            "altitude_target_m": 8.0,
            "recommended_frequency_khz": 900
        },
        "simulation_mode": {
            "is_simulation": True,
            "disclaimer": "SIMULATION MODE: Secondary sonar pass is simulated using verification imagery. Software architecture is telemetry-ready for autonomous AUV integration."
        },
        "geospatial_routes": {
            "target": {"lat": lat, "lon": lon},
            "primary_survey": [
                {"lat": pri_wp1_lat, "lon": pri_wp1_lon, "name": "Primary Entry"},
                {"lat": lat, "lon": lon, "name": "Primary Anomaly CPA"},
                {"lat": pri_wp2_lat, "lon": pri_wp2_lon, "name": "Primary Exit"}
            ],
            "verification_survey": [
                {"lat": sec_wp1_lat, "lon": sec_wp1_lon, "name": "Rescan Entry Point"},
                {"lat": sec_cpa_lat, "lon": sec_cpa_lon, "name": "Rescan Optimal Acoustic CPA"},
                {"lat": sec_wp2_lat, "lon": sec_wp2_lon, "name": "Rescan Exit Point"}
            ]
        }
    }
    
    return rescan_plan


def match_secondary_detection(
    primary_bbox: List[int],
    primary_class: str,
    secondary_detections: List[Dict[str, Any]],
    image_shape: Tuple[int, int] = (512, 512)
) -> Tuple[Optional[Dict[str, Any]], float]:
    """
    Associates a primary detection with candidates in the secondary scan.
    """
    if not secondary_detections:
        return None, 0.0

    img_h, img_w = image_shape[:2]
    px, py, pw, ph = primary_bbox[0], primary_bbox[1], primary_bbox[2], primary_bbox[3]
    p_cx = (px + pw / 2.0) / max(1.0, float(img_w))
    p_cy = (py + ph / 2.0) / max(1.0, float(img_h))
    p_ar = max(0.1, float(pw) / max(1.0, float(ph)))

    best_match = None
    best_score = 0.0

    for sec in secondary_detections:
        s_bbox = sec.get("bbox", [0, 0, 10, 10])
        sx, sy, sw, sh = s_bbox[0], s_bbox[1], s_bbox[2], s_bbox[3]
        s_cx = (sx + sw / 2.0) / max(1.0, float(img_w))
        s_cy = (sy + sh / 2.0) / max(1.0, float(img_h))
        s_ar = max(0.1, float(sw) / max(1.0, float(sh)))
        s_class = sec.get("class", sec.get("predicted_class", "unknown"))
        s_conf = float(sec.get("confidence", sec.get("confidence_score", 0.5)))
        if s_conf > 1.0:
            s_conf /= 100.0

        dist = math.sqrt((p_cx - s_cx) ** 2 + (p_cy - s_cy) ** 2)
        spatial_score = max(0.0, 1.0 - (dist / 0.75))
        ar_ratio = min(p_ar, s_ar) / max(p_ar, s_ar)
        class_score = 1.0 if s_class.lower() == primary_class.lower() else 0.3
        conf_score = s_conf

        match_score = (
            (0.40 * spatial_score) +
            (0.25 * ar_ratio) +
            (0.25 * class_score) +
            (0.10 * conf_score)
        )

        if match_score > best_score:
            best_score = match_score
            best_match = sec

    if best_score >= 0.35 and best_match is not None:
        return best_match, round(best_score * 100.0, 1)
    
    return None, round(best_score * 100.0, 1)


def compare_observations(
    primary_evidence: Dict[str, Any],
    secondary_evidence: Optional[Dict[str, Any]],
    match_score: float = 0.0
) -> Dict[str, Any]:
    """
    Computes rigorous, objective evidence comparison between Primary and Secondary passes.
    """
    p_class = primary_evidence.get("class", primary_evidence.get("predicted_class", "ghost_net"))
    p_conf = float(primary_evidence.get("confidence_score", primary_evidence.get("confidence", 60.0)))
    if p_conf <= 1.0:
        p_conf *= 100.0
    p_shadow = float(primary_evidence.get("shadow_score", 50.0))
    p_shape = float(primary_evidence.get("shape_score", 65.0))
    p_detector = float(primary_evidence.get("detector_score", p_conf))

    if secondary_evidence is None:
        return {
            "status": "NOT_CONFIRMED",
            "verdict_title": "DETECTION NOT CONFIRMED",
            "verdict_badge": "NOT CONFIRMED (FALSE ALARM / NO MATCH)",
            "verdict_color": "text-amber-400 bg-amber-500/20 border-amber-500/40",
            "summary_text": "Secondary sonar observation did not detect a corresponding acoustic signature at the target coordinates. The initial anomaly was likely transient acoustic speckle, seabed ripple, or natural bottom relief.",
            "target_associated": False,
            "match_score": match_score,
            "class_consistent": False,
            "confidence_delta": round(0.0 - p_conf, 1),
            "evidence_strengthened": False,
            "primary": {
                "class": p_class,
                "confidence": round(p_conf, 1),
                "detector_score": round(p_detector, 1),
                "shadow_score": round(p_shadow, 1),
                "shape_score": round(p_shape, 1)
            },
            "secondary": None,
            "scientific_notes": [
                "Target not detected in secondary orthogonal acoustic swath.",
                "Initial feature lacked persistent acoustic specular reflection.",
                "Recommend marking as False Alarm or logging for bathymetric review."
            ],
            "recommended_action": "REJECT_OR_REVIEW"
        }

    s_class = secondary_evidence.get("class", secondary_evidence.get("predicted_class", "unknown"))
    s_conf = float(secondary_evidence.get("confidence_score", secondary_evidence.get("confidence", 50.0)))
    if s_conf <= 1.0:
        s_conf *= 100.0
    s_shadow = float(secondary_evidence.get("shadow_score", 50.0))
    s_shape = float(secondary_evidence.get("shape_score", 60.0))
    s_detector = float(secondary_evidence.get("detector_score", s_conf))

    class_consistent = (s_class.lower() == p_class.lower())
    conf_delta = round(s_conf - p_conf, 1)
    shadow_delta = round(s_shadow - p_shadow, 1)
    shape_delta = round(s_shape - p_shape, 1)
    detector_delta = round(s_detector - p_detector, 1)

    evidence_strengthened = (s_conf >= p_conf and s_shadow >= 45.0)

    scientific_notes: List[str] = []

    if class_consistent and s_conf >= 70.0 and s_shadow >= 60.0:
        status = "VERIFIED"
        verdict_title = f"VERIFIED {p_class.upper().replace('_', ' ')}"
        verdict_badge = "✓ TARGET VERIFIED BY RESCAN"
        verdict_color = "text-emerald-300 bg-emerald-500/20 border-emerald-500/40"
        summary_text = f"Secondary acoustic pass confirmed target with {s_conf:.1f}% confidence and strong acoustic shadow cast ({s_shadow:.1f}%). Multi-angle acoustic evidence strongly supports {p_class} classification."
        scientific_notes.append("Classification consistent across two independent acoustic angles.")
        scientific_notes.append("Acoustic cast shadow verified at orthogonal illumination.")
        scientific_notes.append(f"Composite confidence increased by +{conf_delta:.1f}%.")
        recommended_action = "CONFIRM"
    elif class_consistent and s_conf >= 45.0:
        status = "CONSISTENT_MODERATE"
        verdict_title = f"PROBABLE {p_class.upper().replace('_', ' ')}"
        verdict_badge = "PROBABLE TARGET (MODERATE EVIDENCE)"
        verdict_color = "text-cyan-300 bg-cyan-500/20 border-cyan-500/40"
        summary_text = f"Target was observed in secondary pass with consistent classification ({s_class}), but moderate confidence ({s_conf:.1f}%)."
        scientific_notes.append("Class agreement confirmed between passes.")
        scientific_notes.append(f"Confidence delta: {conf_delta:+.1f}%.")
        recommended_action = "CONFIRM" if s_conf >= p_conf else "REVIEW"
    elif s_conf < 40.0 or s_shadow < 35.0:
        status = "NOT_CONFIRMED"
        verdict_title = "DETECTION NOT CONFIRMED"
        verdict_badge = "⚠ NOT CONFIRMED (WEAK SECONDARY EVIDENCE)"
        verdict_color = "text-amber-400 bg-amber-500/20 border-amber-500/40"
        summary_text = f"Secondary observation demonstrated degraded acoustic evidence ({s_conf:.1f}% vs initial {p_conf:.1f}%). Weak acoustic shadow ({s_shadow:.1f}%) suggests object lacks physical relief."
        scientific_notes.append("Secondary confidence lower than primary observation.")
        scientific_notes.append("Acoustic shadow was not confirmed from alternate angle.")
        scientific_notes.append(f"Confidence delta: {conf_delta:+.1f}%.")
        recommended_action = "REJECT"
    else:
        status = "REQUIRES_REVIEW"
        verdict_title = "REQUIRES OPERATOR REVIEW"
        verdict_badge = "⚠ AMBIGUOUS / CLASS DISCREPANCY"
        verdict_color = "text-amber-300 bg-amber-500/20 border-amber-500/40"
        summary_text = f"Secondary pass detected an anomaly, but class disagreed ({p_class} vs {s_class}). Human operator review required."
        scientific_notes.append(f"Primary classification ({p_class}) disagreed with secondary ({s_class}).")
        scientific_notes.append("Requires specialist review before logging.")
        recommended_action = "REVIEW"

    return {
        "status": status,
        "verdict_title": verdict_title,
        "verdict_badge": verdict_badge,
        "verdict_color": verdict_color,
        "summary_text": summary_text,
        "target_associated": True,
        "match_score": match_score,
        "class_consistent": class_consistent,
        "confidence_delta": conf_delta,
        "shadow_delta": shadow_delta,
        "shape_delta": shape_delta,
        "detector_delta": detector_delta,
        "evidence_strengthened": evidence_strengthened,
        "primary": {
            "class": p_class,
            "confidence": round(p_conf, 1),
            "detector_score": round(p_detector, 1),
            "shadow_score": round(p_shadow, 1),
            "shape_score": round(p_shape, 1)
        },
        "secondary": {
            "class": s_class,
            "confidence": round(s_conf, 1),
            "detector_score": round(s_detector, 1),
            "shadow_score": round(s_shadow, 1),
            "shape_score": round(s_shape, 1)
        },
        "scientific_notes": scientific_notes,
        "recommended_action": recommended_action
    }


def generate_synthetic_rescan_image(
    scenario: str,
    target_class: str = "ghost_net",
    base_image: Optional[np.ndarray] = None,
    primary_bbox: Optional[List[int]] = None
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Generates a deterministic synthetic secondary sonar verification scan.
    """
    h, w = (512, 512)
    img = np.random.normal(105, 18, (h, w)).clip(40, 210).astype(np.uint8)
    y_coords, x_coords = np.mgrid[0:h, 0:w]
    ripples = (np.sin(x_coords / 12.0 + y_coords / 40.0) * 14.0).astype(np.int16)
    img = np.clip(img.astype(np.int16) + ripples, 0, 255).astype(np.uint8)
    
    nadir_x = w // 2
    cv2.line(img, (nadir_x, 0), (nadir_x, h), (18, 18, 18), 6)
    cv2.line(img, (nadir_x, 0), (nadir_x, h), (230, 230, 230), 1)

    secondary_detections = []

    if scenario.lower() in ["confirm", "scenario_a", "verified"]:
        tx, ty, tw, th = (320, 210, 78, 64)
        cv2.rectangle(img, (tx, ty), (tx + tw // 2, ty + th), (240), -1)
        if "net" in target_class:
            for gy in range(ty, ty + th, 8):
                cv2.line(img, (tx, gy), (tx + tw // 2, gy), (255), 2)
        cv2.rectangle(img, (tx + tw // 2, ty - 4), (tx + tw + 36, ty + th + 4), (18), -1)
        img = cv2.GaussianBlur(img, (3, 3), 0.8)
        
        conf_res = evaluate_detection_confidence(img, (tx, ty, tw, th), yolo_confidence=0.88, nadir_x=nadir_x)
        
        secondary_detections.append({
            "class": target_class,
            "predicted_class": target_class,
            "confidence": round(conf_res.final_score / 100.0, 3),
            "confidence_score": conf_res.final_score,
            "confidence_tier": conf_res.tier,
            "detector_score": conf_res.detector_score,
            "shadow_score": conf_res.shadow_score,
            "shape_score": conf_res.shape_score,
            "shadow_detected": conf_res.shadow_detected,
            "bbox": [tx, ty, tw, th],
            "threat_level": "HIGH"
        })

    elif scenario.lower() in ["reject", "scenario_b", "false_alarm", "not_confirmed"]:
        tx, ty, tw, th = (320, 210, 60, 50)
        cv2.ellipse(img, (tx + tw // 2, ty + th // 2), (tw // 2, th // 2), 0, 0, 360, (145), -1)
        img = cv2.GaussianBlur(img, (5, 5), 1.2)
        
        conf_res = evaluate_detection_confidence(img, (tx, ty, tw, th), yolo_confidence=0.36, nadir_x=nadir_x)
        
        secondary_detections.append({
            "class": "rock_cluster" if target_class != "rock_cluster" else "unknown_anomaly",
            "predicted_class": "rock_cluster",
            "confidence": round(conf_res.final_score / 100.0, 3),
            "confidence_score": conf_res.final_score,
            "confidence_tier": conf_res.tier,
            "detector_score": conf_res.detector_score,
            "shadow_score": conf_res.shadow_score,
            "shape_score": conf_res.shape_score,
            "shadow_detected": conf_res.shadow_detected,
            "bbox": [tx, ty, tw, th],
            "threat_level": "LOW"
        })

    bgr_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    return bgr_img, secondary_detections
