import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const pathname = request.nextUrl.pathname;
  const authToken = request.cookies.get("auth_token")?.value;

  const protectedRoutes = [
    "/profile",
    "/command-center",
    "/detection",
    "/cnn",
    "/analytics",
    "/watchlist",
  ];

  const isProtectedRoute = protectedRoutes.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );

  // If visiting protected route without an auth token, redirect smoothly to login
  if (isProtectedRoute && !authToken) {
    const loginUrl = new URL("/auth/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml|public|logos|docs).*)"],
};
