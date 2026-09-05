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
    "/intelligence",
    "/mission-planner",
    "/threat-prediction",
    "/watchlist",
  ];
  const authPages = ["/auth/login", "/auth/register"];

  const isProtectedRoute = protectedRoutes.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );
  const isAuthPage = authPages.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`),
  );

  if (isProtectedRoute && !authToken) {
    return NextResponse.redirect(new URL("/try", request.url));
  }

  if (isAuthPage && authToken) {
    return NextResponse.redirect(new URL("/profile", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|robots.txt|sitemap.xml).*)"],
};

