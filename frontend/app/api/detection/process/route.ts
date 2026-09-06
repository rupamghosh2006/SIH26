import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
  const startTime = Date.now();
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File | null;
    const type = (formData.get("type") as string) || "image";

    if (!file) {
      return NextResponse.json({ error: "No file provided" }, { status: 400 });
    }

    const fastApiBaseUrl = process.env.FASTAPI_BASE_URL || "http://127.0.0.1:8000";

    // Build multipart/form-data for FastAPI /api/surveys/upload
    const uploadData = new FormData();
    uploadData.append("image_file", file, file.name);
    uploadData.append("title", `Sonar Survey - ${file.name}`);
    uploadData.append("slant_range_m", "75.0");
    uploadData.append("auto_process", "true");

    console.log(`[Next.js Detection API] Forwarding upload to FastAPI at ${fastApiBaseUrl}/api/surveys/upload`);

    let uploadRes: Response;
    try {
      uploadRes = await fetch(`${fastApiBaseUrl}/api/surveys/upload`, {
        method: "POST",
        body: uploadData,
      });
    } catch (netErr: any) {
      console.error("[Next.js Detection API] Failed to connect to FastAPI backend:", netErr);
      return NextResponse.json(
        {
          error: "Could not connect to Varuna AI FastAPI backend service at " + fastApiBaseUrl,
          details: netErr.message || String(netErr),
        },
        { status: 502 }
      );
    }

    if (!uploadRes.ok) {
      const errText = await uploadRes.text();
      console.error("[Next.js Detection API] FastAPI upload returned error:", uploadRes.status, errText);
      return NextResponse.json(
        { error: `FastAPI upload error (${uploadRes.status}): ${errText}` },
        { status: uploadRes.status }
      );
    }

    const surveySummary = await uploadRes.json();
    const surveyId = surveySummary.id;
    console.log(`[Next.js Detection API] Survey created: ${surveyId}. Polling for completion...`);

    // Poll survey until processing completes (up to 30s)
    let surveyDetail: any = null;
    const maxPolls = 60;
    const pollIntervalMs = 500;

    for (let i = 0; i < maxPolls; i++) {
      await new Promise((r) => setTimeout(r, pollIntervalMs));
      try {
        const detailRes = await fetch(`${fastApiBaseUrl}/api/surveys/${surveyId}`);
        if (detailRes.ok) {
          const data = await detailRes.json();
          if (data.status === "done" || data.status === "completed" || data.status === "failed") {
            surveyDetail = data;
            break;
          }
        }
      } catch (pollErr) {
        console.warn("[Next.js Detection API] Poll iteration error:", pollErr);
      }
    }

    if (!surveyDetail) {
      return NextResponse.json(
        { error: "Survey processing timed out in backend pipeline." },
        { status: 504 }
      );
    }

    if (surveyDetail.status === "failed") {
      return NextResponse.json(
        { error: surveyDetail.error_message || "Survey processing failed in backend pipeline." },
        { status: 500 }
      );
    }

    // Map detections to frontend contract
    const rawDetections = surveyDetail.detections || [];
    const detections = rawDetections.map((d: any, idx: number) => {
      const confTier = d.confidence_tier || "Low";
      const confScore = typeof d.confidence_score === "number" ? d.confidence_score : 50.0;
      const shadowVerified = Boolean(
        d.filter_details?.shadow_verified ??
        d.filter_details?.shadow_details?.has_shadow ??
        false
      );

      return {
        id: d.id || `det_${idx + 1}`,
        class: d.predicted_class || "debris",
        class_name: d.predicted_class || "debris",
        name: d.predicted_class || "debris",
        confidence: Number((confScore / 100.0).toFixed(3)),
        confidence_score: Number(confScore.toFixed(1)),
        confidence_tier: confTier,
        threat_level: confTier === "High" ? "CRITICAL" : (confTier === "Medium" ? "HIGH" : "MEDIUM"),
        bbox: d.bbox || [0, 0, 0, 0],
        lat: d.latitude,
        latitude: d.latitude,
        lon: d.longitude,
        longitude: d.longitude,
        depth_m: d.depth_m,
        dimensions: d.estimated_size_m || "Unknown",
        physical_size_m: d.estimated_size_m || "Unknown",
        estimated_size_m: d.estimated_size_m || "Unknown",
        color: confTier === "High" ? "#ef4444" : (confTier === "Medium" ? "#f97316" : "#06b6d4"),
        seabed_facies: d.filter_details?.seabed_facies || "flat_sand",
        srr_corrected: true,
        acoustic_shadow_verified: shadowVerified,
        shadow_verified: shadowVerified,
        filter_details: d.filter_details || {},
      };
    });

    const elapsedSec = Number(((Date.now() - startTime) / 1000).toFixed(2));
    const totalDets = detections.length;
    const avgScore = totalDets > 0
      ? Number((detections.reduce((acc: number, cur: any) => acc + cur.confidence_score, 0) / totalDets).toFixed(1))
      : 0;

    let overallThreatLevel = "NONE";
    if (surveyDetail.high_tier_count > 0) overallThreatLevel = "CRITICAL";
    else if (surveyDetail.medium_tier_count > 0) overallThreatLevel = "HIGH";
    else if (totalDets > 0) overallThreatLevel = "MEDIUM";

    // Fetch base64 of annotated image or fallback image from FastAPI static
    const imageEndpoint = surveyDetail.annotated_image_url || surveyDetail.image_url;
    let detectedImageBase64 = "";

    if (imageEndpoint) {
      try {
        const fullImgUrl = `${fastApiBaseUrl}${imageEndpoint}`;
        const imgRes = await fetch(fullImgUrl);
        if (imgRes.ok) {
          const imgBuffer = await imgRes.arrayBuffer();
          const base64Data = Buffer.from(imgBuffer).toString("base64");
          const contentType = imgRes.headers.get("content-type") || "image/jpeg";
          detectedImageBase64 = `data:${contentType};base64,${base64Data}`;
        }
      } catch (imgErr) {
        console.warn("[Next.js Detection API] Could not fetch image as base64:", imgErr);
      }
    }

    return NextResponse.json({
      success: true,
      surveyId: surveyId,
      id: surveyId,
      type: type,
      originalFileName: file.name,
      detectedImage: detectedImageBase64 || `${fastApiBaseUrl}${imageEndpoint}`,
      annotatedImage: detectedImageBase64 || `${fastApiBaseUrl}${imageEndpoint}`,
      annotated_image_url: `${fastApiBaseUrl}${imageEndpoint}`,
      imageUrl: `${fastApiBaseUrl}${imageEndpoint}`,
      detections: detections,
      totalObjects: totalDets,
      overallThreatLevel: overallThreatLevel,
      overallThreatScore: avgScore,
      threatCount: totalDets,
      seafloorFacies: detections[0]?.seabed_facies || "flat_sand",
      srrApplied: true,
      processingTime: elapsedSec,
      nadir_x: surveyDetail.nadir_x,
      latitude: detections[0]?.latitude,
      longitude: detections[0]?.longitude,
      lat: detections[0]?.latitude,
      lon: detections[0]?.longitude,
    });
  } catch (error: any) {
    console.error("[Next.js Detection API] Internal server error:", error);
    return NextResponse.json(
      { error: "Internal server error", details: error?.message || String(error) },
      { status: 500 }
    );
  }
}
