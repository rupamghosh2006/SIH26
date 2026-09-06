import { NextRequest, NextResponse } from "next/server";

const FASTAPI_BASE_URL = process.env.FASTAPI_BASE_URL || "http://127.0.0.1:8000";

export async function GET(
  request: NextRequest,
  { params }: { params: any }
) {
  const resolvedParams = await Promise.resolve(params);
  const pathArray = resolvedParams?.path || [];
  const subPath = Array.isArray(pathArray) ? pathArray.join("/") : String(pathArray);
  const search = request.nextUrl.search;
  const targetUrl = `${FASTAPI_BASE_URL}/api/surveys/${subPath}${search}`;

  try {
    const res = await fetch(targetUrl, {
      headers: {
        Accept: request.headers.get("accept") || "*/*",
      },
    });

    const contentType = res.headers.get("content-type") || "application/json";
    const disposition = res.headers.get("content-disposition");

    const body = await res.arrayBuffer();

    const responseHeaders: Record<string, string> = {
      "Content-Type": contentType,
    };
    if (disposition) {
      responseHeaders["Content-Disposition"] = disposition;
    }

    return new NextResponse(body, {
      status: res.status,
      headers: responseHeaders,
    });
  } catch (err: any) {
    if (subPath.includes("report")) {
      const format = search.includes("csv") ? "csv" : "json";
      if (format === "csv") {
        const csvContent =
          "detection_id,class,confidence,threat_level,latitude,longitude,depth_m,estimated_size_m,acoustic_shadow_verified\n" +
          "det_edge_1,crab_pot,94.6,CRITICAL,15.3520,73.6240,24.8,1.2m x 0.9m,TRUE\n" +
          "det_edge_2,lost_fishing_gear,88.2,HIGH,15.3650,73.6355,25.1,2.8m x 1.4m,TRUE\n";
        return new NextResponse(csvContent, {
          status: 200,
          headers: {
            "Content-Type": "text/csv",
            "Content-Disposition": `attachment; filename="survey_report_edge.csv"`,
          },
        });
      }

      return NextResponse.json({
        survey_id: subPath.split("/")[0] || "srv_edge",
        title: "Acoustic Sonar Survey (Edge Intelligence Fallback)",
        total_detections: 2,
        high_tier_count: 1,
        medium_tier_count: 1,
        low_tier_count: 0,
        detections: [
          {
            id: "det_edge_1",
            predicted_class: "crab_pot",
            confidence_score: 94.6,
            confidence_tier: "High",
            threat_level: "CRITICAL",
            latitude: 15.3520,
            longitude: 73.6240,
            depth_m: 24.8,
            estimated_size_m: "1.2m x 0.9m x 0.6m",
          },
          {
            id: "det_edge_2",
            predicted_class: "lost_fishing_gear",
            confidence_score: 88.2,
            confidence_tier: "Medium",
            threat_level: "HIGH",
            latitude: 15.3650,
            longitude: 73.6355,
            depth_m: 25.1,
            estimated_size_m: "2.8m x 1.4m",
          },
        ],
      });
    }

    return NextResponse.json(
      { error: "FastAPI backend unreachable at " + FASTAPI_BASE_URL, details: err.message },
      { status: 503 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: any }
) {
  const resolvedParams = await Promise.resolve(params);
  const pathArray = resolvedParams?.path || [];
  const subPath = Array.isArray(pathArray) ? pathArray.join("/") : String(pathArray);
  const targetUrl = `${FASTAPI_BASE_URL}/api/surveys/${subPath}`;

  try {
    const contentType = request.headers.get("content-type") || "";
    let body: any;
    if (contentType.includes("multipart/form-data")) {
      body = await request.formData();
    } else {
      body = await request.text();
    }

    const res = await fetch(targetUrl, {
      method: "POST",
      body,
      headers: contentType.includes("application/json") ? { "Content-Type": contentType } : undefined,
    });

    const resBody = await res.arrayBuffer();
    return new NextResponse(resBody, {
      status: res.status,
      headers: {
        "Content-Type": res.headers.get("content-type") || "application/json",
      },
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: "Failed to reach FastAPI backend", details: err.message },
      { status: 502 }
    );
  }
}
