import { NextRequest, NextResponse } from "next/server"
import { runPythonCommand } from "@/lib/python-runner"
import { writeFile, mkdir } from "fs/promises"
import { join } from "path"
import { existsSync } from "fs"
import { generateSafeUploadFilename } from "@/lib/path-security"

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData()
    const action = (formData.get("action") as string) || "plan" // "plan" or "rescan"
    const detectionRaw = formData.get("detection") as string
    const scenario = (formData.get("scenario") as string) || "confirm"
    const file = formData.get("file") as File | null

    if (!detectionRaw) {
      return NextResponse.json({ error: "Detection payload is required" }, { status: 400 })
    }

    let detection: any = {}
    try {
      detection = JSON.parse(detectionRaw)
    } catch {
      return NextResponse.json({ error: "Invalid detection JSON" }, { status: 400 })
    }

    const tempDir = join(process.cwd(), "temp")
    if (!existsSync(tempDir)) {
      await mkdir(tempDir, { recursive: true })
    }

    // Prepare uploaded file if mode is upload
    let inputImagePath = ""
    if (file && file.size > 0) {
      const fileBuffer = await file.arrayBuffer()
      const fileName = generateSafeUploadFilename(file.name, "verify")
      inputImagePath = join(tempDir, fileName)
      await writeFile(inputImagePath, Buffer.from(fileBuffer))
    }

    const escapedImagePath = inputImagePath.replace(/\\/g, "/").replace(/'/g, "\\'")
    const escapedDetectionJson = JSON.stringify(detection).replace(/\\/g, "\\\\").replace(/'/g, "\\'")

    const pythonScript = `
import sys
import os
import json
import numpy as np
import cv2

# Add root directory to python path
sys.path.insert(0, os.getcwd())

from backend.ai_pipeline.active_verification import (
    assess_verification_need,
    plan_secondary_rescan,
    match_secondary_detection,
    compare_observations,
    generate_synthetic_rescan_image
)
from backend.ai_pipeline.confidence_filter import evaluate_detection_confidence

action = "${action}"
scenario = "${scenario}"
raw_det = json.loads('${escapedDetectionJson}')
uploaded_img_path = r"${escapedImagePath}"

if action == "plan":
    plan = plan_secondary_rescan(
        detection=raw_det,
        nadir_x=512,
        image_width=1024,
        slant_range_m=75.0
    )
    print(json.dumps({"success": True, "plan": plan}))

elif action == "rescan":
    target_class = raw_det.get("class", raw_det.get("predicted_class", "ghost_net"))
    primary_bbox = raw_det.get("bbox", [300, 200, 80, 60])
    
    sec_img = None
    sec_dets = []
    
    if uploaded_img_path and os.path.exists(uploaded_img_path):
        sec_img = cv2.imread(uploaded_img_path)
        if sec_img is not None:
            sec_h, sec_w = sec_img.shape[:2]
            nadir_x = sec_w // 2
            
            # Run detection or candidate extraction
            try:
                from threat_detector import ThreatDetector
                td = ThreatDetector(model_path=None, confidence_threshold=0.20, verbose=False)
                res = td.detect_threats(uploaded_img_path)
                for t in res.get("threats", []):
                    bbox = t["bounding_box"]
                    sec_dets.append({
                        "class": t["class"],
                        "confidence": t["confidence"],
                        "confidence_score": t["confidence"] * 100.0,
                        "detector_score": t.get("detector_score", t["confidence"] * 100.0),
                        "shadow_score": t.get("shadow_score", 60.0),
                        "shape_score": t.get("shape_score", 65.0),
                        "shadow_detected": True,
                        "bbox": [bbox["x1"], bbox["y1"], bbox["width"], bbox["height"]]
                    })
            except Exception:
                pass
                
            # If no threats extracted, evaluate crop at primary location as candidate
            if not sec_dets:
                conf_eval = evaluate_detection_confidence(sec_img, tuple(primary_bbox), yolo_confidence=0.45, nadir_x=nadir_x)
                sec_dets.append({
                    "class": target_class,
                    "confidence": conf_eval.final_score / 100.0,
                    "confidence_score": conf_eval.final_score,
                    "detector_score": conf_eval.detector_score,
                    "shadow_score": conf_eval.shadow_score,
                    "shape_score": conf_eval.shape_score,
                    "shadow_detected": conf_eval.shadow_detected,
                    "bbox": primary_bbox
                })
    else:
        # Generate deterministic synthetic rescan image
        sec_img, sec_dets = generate_synthetic_rescan_image(
            scenario=scenario,
            target_class=target_class,
            primary_bbox=primary_bbox
        )

    # Convert rescan image to base64 for direct browser rendering
    _, buffer = cv2.imencode(".png", sec_img)
    import base64
    img_b64 = "data:image/png;base64," + base64.b64encode(buffer).decode("utf-8")

    # Match target deterministically
    matched_sec, match_score = match_secondary_detection(
        primary_bbox=primary_bbox,
        primary_class=target_class,
        secondary_detections=sec_dets,
        image_shape=sec_img.shape[:2]
    )

    # Compare observations
    comparison = compare_observations(
        primary_evidence=raw_det,
        secondary_evidence=matched_sec,
        match_score=match_score
    )

    result_payload = {
        "success": True,
        "scenario": scenario,
        "comparison": comparison,
        "secondary_image": img_b64,
        "matched_detection": matched_sec,
        "all_secondary_detections": sec_dets
    }
    print(json.dumps(result_payload))
`

    const scriptPath = join(tempDir, `active_verify_${Date.now()}.py`)
    await writeFile(scriptPath, pythonScript)

    const pyResult = await runPythonCommand([scriptPath], process.cwd())

    // Clean up temporary script
    try {
      const { unlink } = await import("fs/promises")
      await unlink(scriptPath)
    } catch {}

    if (pyResult.code !== 0) {
      console.error("Active Verification Python Error:", pyResult.stderr)
      return NextResponse.json(
        { error: "Verification processing failed", details: pyResult.stderr },
        { status: 500 }
      )
    }

    const stdoutLines = pyResult.stdout.trim().split("\n")
    const lastLine = stdoutLines[stdoutLines.length - 1]
    const parsed = JSON.parse(lastLine)

    return NextResponse.json(parsed)
  } catch (err) {
    console.error("Active verification endpoint error:", err)
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Internal Server Error" },
      { status: 500 }
    )
  }
}
