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
    return NextResponse.json(
      { error: "Failed to reach FastAPI backend", details: err.message },
      { status: 502 }
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
