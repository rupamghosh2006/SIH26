import { NextResponse } from 'next/server'

export async function GET() {
  const backendUrl =
    process.env.FASTAPI_BASE_URL &&
    !process.env.FASTAPI_BASE_URL.includes("127.0.0.1") &&
    !process.env.FASTAPI_BASE_URL.includes("localhost")
      ? process.env.FASTAPI_BASE_URL
      : "https://varuna-sonar-backend.onrender.com";

  let backendStatus: any = { connected: false, url: backendUrl };

  try {
    const res = await fetch(`${backendUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      backendStatus = {
        connected: true,
        url: backendUrl,
        response: data,
      };
    } else {
      backendStatus = {
        connected: false,
        url: backendUrl,
        status: res.status,
      };
    }
  } catch (err: any) {
    backendStatus = {
      connected: false,
      url: backendUrl,
      error: err?.message || String(err),
    };
  }

  try {
    return NextResponse.json({
      status: "healthy",
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      environment: process.env.NODE_ENV || "development",
      version: process.env.npm_package_version || "1.0.0",
      backend: backendStatus,
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: "unhealthy",
        error: error instanceof Error ? error.message : "Unknown error",
        timestamp: new Date().toISOString(),
        backend: backendStatus,
      },
      { status: 500 }
    );
  }
}
