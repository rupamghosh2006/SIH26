"""
Reporting Module for SeaGuard AI.
Generates structured JSON and CSV reports conforming to the standard survey detection schema.
"""

import io
import csv
import json
from typing import List, Dict, Any, Optional


REPORT_COLUMNS = [
    "detection_id",
    "survey_id",
    "ping_index",
    "latitude",
    "longitude",
    "depth_m",
    "bbox_x",
    "bbox_y",
    "bbox_width",
    "bbox_height",
    "estimated_size_m",
    "predicted_class",
    "confidence_score",
    "confidence_tier",
    "timestamp",
    "source_file"
]


def build_detection_report(
    detections: List[Dict[str, Any]],
    survey_meta: Optional[Dict[str, Any]] = None,
    output_format: str = "json"
) -> str:
    """
    Builds a downloadable detection report in CSV or JSON format.
    
    Expected detection keys:
    - detection_id (or id)
    - survey_id
    - ping_index
    - latitude
    - longitude
    - depth_m
    - bbox_x (or bbox[0])
    - bbox_y (or bbox[1])
    - bbox_width (or bbox[2])
    - bbox_height (or bbox[3])
    - estimated_size_m
    - predicted_class (or class_name)
    - confidence_score (or score)
    - confidence_tier (or tier)
    - timestamp
    - source_file
    """
    rows = []
    for d in detections:
        # Extract bbox parts if stored as array
        bbox = d.get("bbox", [0, 0, 0, 0])
        bx = d.get("bbox_x", bbox[0] if len(bbox) > 0 else 0)
        by = d.get("bbox_y", bbox[1] if len(bbox) > 1 else 0)
        bw = d.get("bbox_width", bbox[2] if len(bbox) > 2 else 0)
        bh = d.get("bbox_height", bbox[3] if len(bbox) > 3 else 0)

        # Estimated size format e.g. "3.2m x 1.1m" or numeric 3.2
        size_est = d.get("estimated_size_m")
        if size_est is None and bw and bh:
            # Assume ~0.15m per pixel if not specified
            m_per_px = d.get("meters_per_pixel", 0.15)
            size_est = f"{round(bw * m_per_px, 1)}m x {round(bh * m_per_px, 1)}m"

        row = {
            "detection_id": d.get("detection_id") or d.get("id") or "",
            "survey_id": d.get("survey_id") or (survey_meta.get("id") if survey_meta else ""),
            "ping_index": d.get("ping_index", 0),
            "latitude": round(float(d.get("latitude", 0.0)), 7),
            "longitude": round(float(d.get("longitude", 0.0)), 7),
            "depth_m": round(float(d["depth_m"]), 2) if d.get("depth_m") is not None else None,
            "bbox_x": int(bx),
            "bbox_y": int(by),
            "bbox_width": int(bw),
            "bbox_height": int(bh),
            "estimated_size_m": str(size_est) if size_est else "Unknown",
            "predicted_class": d.get("predicted_class") or d.get("class_name") or "unknown",
            "confidence_score": round(float(d.get("confidence_score") or d.get("final_score") or 0.0), 1),
            "confidence_tier": d.get("confidence_tier") or d.get("tier") or "Low",
            "timestamp": d.get("timestamp") or (survey_meta.get("created_at") if survey_meta else ""),
            "source_file": d.get("source_file") or (survey_meta.get("filename") if survey_meta else "survey_sonar.jpg")
        }
        rows.append(row)

    if output_format.lower() == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=REPORT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
        return output.getvalue()
    else:
        # Structured JSON with survey header and detection list
        payload = {
            "survey_summary": survey_meta or {},
            "total_detections": len(rows),
            "tier_counts": {
                "High": sum(1 for r in rows if r["confidence_tier"] == "High"),
                "Medium": sum(1 for r in rows if r["confidence_tier"] == "Medium"),
                "Low": sum(1 for r in rows if r["confidence_tier"] == "Low")
            },
            "class_counts": {
                cls: sum(1 for r in rows if r["predicted_class"] == cls)
                for cls in set(r["predicted_class"] for r in rows)
            },
            "detections": rows
        }
        return json.dumps(payload, indent=2)
