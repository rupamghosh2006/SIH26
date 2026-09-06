import { NextRequest, NextResponse } from "next/server";
import jwt from "jsonwebtoken";
import { getUserCollection } from "@/dbCollections";
import { exchangeCodeForTokens, fetchGoogleUserProfile, getBaseUrlFromRequest } from "@/lib/google-oauth";

const JWT_SECRET = process.env.JWT_SECRET || "supersecret";

export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const code = searchParams.get("code");
  const error = searchParams.get("error");

  if (error) {
    return NextResponse.redirect(new URL(`/auth/login?error=${encodeURIComponent(error)}`, req.url));
  }

  if (!code) {
    return NextResponse.redirect(new URL(`/auth/login?error=${encodeURIComponent("Missing code")}`, req.url));
  }

  try {
    const baseUrl = getBaseUrlFromRequest(req);
    const tokenResponse = await exchangeCodeForTokens(code, baseUrl);
    const profile = await fetchGoogleUserProfile(tokenResponse.access_token);

    const email = profile.email?.toLowerCase();
    const googleId = profile.sub;

    if (!email) {
      return NextResponse.redirect(new URL(`/auth/login?error=${encodeURIComponent("Email not available from Google")}`, req.url));
    }

    let userId = "google-usr-" + Date.now();
    const firstName = profile.given_name || profile.name?.split(" ")[0] || "Officer";
    const lastName = profile.family_name || profile.name?.split(" ").slice(1).join(" ") || "Google";
    const role = "researcher";

    try {
      const users = await getUserCollection();
      const updateDoc = {
        $setOnInsert: {
          username: profile.name || email.split("@")[0],
          createdAt: new Date(),
        },
        $set: {
          email,
          firstName,
          lastName,
          avatar: profile.picture || "",
          googleId,
          role,
          emailVerified: Boolean(profile.email_verified),
          updatedAt: new Date(),
        },
      };

      const result = await users.findOneAndUpdate(
        { $or: [{ email }, { googleId }] },
        updateDoc,
        { upsert: true, returnDocument: "after" }
      );

      const user = result?.value || (await users.findOne({ email }));
      if (user?._id) {
        userId = user._id.toString();
      }
    } catch (dbErr) {
      console.warn("MongoDB unavailable during Google OAuth, proceeding with token session:", dbErr);
    }

    const token = jwt.sign(
      {
        id: userId,
        email,
        role,
        firstName,
        lastName,
        avatar: profile.picture || "",
      },
      JWT_SECRET,
      { expiresIn: "30d" }
    );

    const response = NextResponse.redirect(new URL("/detection", req.url));
    response.cookies.set("auth_token", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: 60 * 60 * 24 * 30,
      path: "/",
      expires: new Date(Date.now() + 60 * 60 * 24 * 30 * 1000)
    });

    return response;
  } catch (e) {
    console.error("Google OAuth callback error:", e);
    return NextResponse.redirect(new URL(`/auth/login?error=${encodeURIComponent("Google sign-in failed")}`, req.url));
  }
}
