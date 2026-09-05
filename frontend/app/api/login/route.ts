import { NextRequest, NextResponse } from "next/server"
import { getUserCollection } from "@/dbCollections"
import * as bcrypt from "bcryptjs"
import * as jwt from "jsonwebtoken"

const JWT_SECRET = process.env.JWT_SECRET || "supersecret"
const TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 30 // 30 days - extended session

function dbConfigError(err: unknown) {
  const msg = err instanceof Error ? err.message : String(err)
  return msg.toLowerCase().includes("mongodb_uri is not set")
}

export async function POST(req: NextRequest) {
  try {
    const { email, password } = await req.json()

    if (!email || !password) {
      return NextResponse.json({ message: "Missing email or password" }, { status: 400 })
    }

    // ═══ VARUNA RBAC ROLE / DEMO BYPASS ═══
    const lowerEmail = email.toLowerCase().trim();
    const isDemoAccount = 
      (lowerEmail === "operator@varuna.ai" || 
       lowerEmail === "researcher@varuna.ai" ||
       lowerEmail === "admin@varuna.ai" || 
       lowerEmail === "viewer@varuna.ai" ||
       lowerEmail === "demo@varuna.ai");

    if (isDemoAccount) {
      const demoId = "varuna-usr-" + Date.now();
      const role = lowerEmail.includes("admin") 
        ? "admin" 
        : lowerEmail.includes("viewer") 
          ? "viewer" 
          : "researcher";

      const firstName = lowerEmail.includes("admin")
        ? "Chief"
        : lowerEmail.includes("viewer")
          ? "Marine"
          : "Sonar";

      const lastName = lowerEmail.includes("admin")
        ? "Admin"
        : lowerEmail.includes("viewer")
          ? "Ecologist"
          : "Researcher";

      const token = jwt.sign(
        { id: demoId, email: lowerEmail, role },
        JWT_SECRET,
        { expiresIn: TOKEN_MAX_AGE_SECONDS }
      );

      const response = NextResponse.json({
        message: "Login successful",
        user: {
          id: demoId,
          email: lowerEmail,
          role,
          firstName,
          lastName,
          avatar: "/placeholder-user.jpg",
        }
      }, { status: 200 });

      response.cookies.set("auth_token", token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        maxAge: TOKEN_MAX_AGE_SECONDS,
        path: "/",
        expires: new Date(Date.now() + TOKEN_MAX_AGE_SECONDS * 1000)
      });

      return response;
    }
    // ═══ END DEMO BYPASS ═══

    let users;
    try {
      users = await getUserCollection();
    } catch (dbErr) {
      console.warn("MongoDB unavailable, falling back to instant session login:", dbErr);
      const fallbackId = "fallback-user-" + Date.now();
      const token = jwt.sign({ id: fallbackId, email }, JWT_SECRET, { expiresIn: TOKEN_MAX_AGE_SECONDS });
      const response = NextResponse.json({
        message: "Login successful (Demo Mode)",
        user: {
          id: fallbackId,
          email,
          firstName: email.split("@")[0],
          lastName: "User",
          avatar: null,
        }
      }, { status: 200 });
      response.cookies.set("auth_token", token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        maxAge: TOKEN_MAX_AGE_SECONDS,
        path: "/",
        expires: new Date(Date.now() + TOKEN_MAX_AGE_SECONDS * 1000)
      });
      return response;
    }

    const user = await users.findOne({ email })

    if (!user) {
      return NextResponse.json({ message: "Invalid credentials" }, { status: 401 })
    }

    const isPasswordValid = await bcrypt.compare(password, user.password)
    if (!isPasswordValid) {
      return NextResponse.json({ message: "Invalid credentials" }, { status: 401 })
    }

    const token = jwt.sign(
      { 
        id: user._id.toString(),
        email: user.email 
      },
      JWT_SECRET,
      { expiresIn: TOKEN_MAX_AGE_SECONDS }
    )

    const response = NextResponse.json({ 
      message: "Login successful",
      user: {
        id: user._id.toString(),
        email: user.email,
        firstName: user.firstName || user.username,
        lastName: user.lastName || "",
        dob: user.dob,
        avatar: user.avatar,
      }
    }, { status: 200 })

    response.cookies.set("auth_token", token, {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      sameSite: "lax",
      maxAge: TOKEN_MAX_AGE_SECONDS,
      path: "/",
      expires: new Date(Date.now() + TOKEN_MAX_AGE_SECONDS * 1000)
    })

    return response
  } catch (error) {
    console.error("Login error:", error)
    if (dbConfigError(error)) {
      return NextResponse.json(
        { message: "Database not configured. Set MONGODB_URI in .env.local (see ENVIRONMENT_SETUP.md)." },
        { status: 500 }
      )
    }
    return NextResponse.json({ message: "Internal server error" }, { status: 500 })
  }
}
