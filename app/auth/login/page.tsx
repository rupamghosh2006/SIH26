"use client";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { SonarGridBackground } from "@/components/sonar-grid-background";
import { useEffect, useState, useRef, Suspense } from "react";
import {
  Mail,
  Lock,
  Fingerprint,
  Shield,
  ShieldCheck,
  Radar,
  Anchor,
  AlertTriangle,
  Cpu,
  Wifi,
  WifiOff,
  CheckCircle2,
  XCircle,
  Eye,
  EyeOff,
  Sparkles,
} from "lucide-react";
import { GoogleSignInButton } from "@/components/google-signin-button";

function LoginFormContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTarget = searchParams?.get("redirect") || "/detection";

  const [method, setMethod] = useState<"password" | "otp" | "rfid">("password");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [countdown, setCountdown] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [currentTime, setCurrentTime] = useState("");

  // RFID State
  const [rfidReady, setRfidReady] = useState(false);
  const [rfidScanning, setRfidScanning] = useState(false);
  const [rfidUid, setRfidUid] = useState("");
  const [rfidStatus, setRfidStatus] = useState<"idle" | "scanning" | "success" | "denied">("idle");
  const [socketConnected, setSocketConnected] = useState(false);
  const socketRef = useRef<any>(null);

  // Clock tick
  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString("en-IN", {
          hour12: false,
          timeZone: "Asia/Kolkata",
        }) + " IST",
      );
    };
    tick();
    const iv = setInterval(tick, 1000);
    return () => clearInterval(iv);
  }, []);

  // OTP Countdown
  useEffect(() => {
    if (countdown <= 0) return;
    const t = setTimeout(() => setCountdown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [countdown]);

  // Non-blocking Lazy RFID Socket Connection (Only active when RFID mode is selected)
  useEffect(() => {
    if (method !== "rfid") return;

    let socket: any = null;
    let isCancelled = false;

    import("socket.io-client").then(({ io }) => {
      if (isCancelled) return;
      try {
        socket = io("http://localhost:5001", {
          transports: ["websocket", "polling"],
          reconnection: true,
          reconnectionAttempts: 2,
          reconnectionDelay: 3000,
          timeout: 2000,
        });
        socketRef.current = socket;

        socket.on("connect", () => setSocketConnected(true));
        socket.on("disconnect", () => {
          setSocketConnected(false);
          setRfidReady(false);
        });
        socket.on("connect_error", () => {
          setSocketConnected(false);
          setRfidReady(false);
        });

        socket.on("rfid_status", (data: any) => {
          setRfidReady(Boolean(data?.ready));
        });

        socket.on("rfid_scanning", (data: any) => {
          setRfidScanning(true);
          setRfidUid(data?.uid || "");
          setRfidStatus("scanning");
          setError(null);
        });

        socket.on("auth_result", async (data: any) => {
          setRfidScanning(false);
          if (data?.status === "success") {
            setRfidStatus("success");
            setSuccess(`ACCESS GRANTED — Officer ${data.name || "Authorized"} [${data.clearance || "CLEARANCE-A"}]`);

            const rfidUser = {
              id: "rfid-usr-" + Date.now(),
              name: data.name || "Sonar Officer",
              email: "operator@varuna.ai",
              role: data.role || "researcher",
              clearance: data.clearance || "Level-3",
              method: "rfid",
              uid: data.uid,
            };

            try {
              localStorage.setItem("profile", JSON.stringify(rfidUser));
              localStorage.setItem("user", JSON.stringify(rfidUser));
            } catch {}

            setTimeout(() => {
              router.push(redirectTarget);
            }, 800);
          } else {
            setRfidStatus("denied");
            setError(data?.message || `RFID card ${data?.uid || ""} not authorized`);
            setTimeout(() => setRfidStatus("idle"), 3000);
          }
        });

        socket.emit("request_rfid_scan");
      } catch (err) {
        console.warn("RFID socket init:", err);
      }
    });

    return () => {
      isCancelled = true;
      if (socket) {
        socket.disconnect();
        socketRef.current = null;
      }
    };
  }, [method, redirectTarget, router]);

  // Fast Instant Role Demo Login (No DB Dependency)
  const handleRoleDemoLogin = async (roleType: "researcher" | "admin" | "viewer") => {
    setLoading(true);
    setError(null);
    const roleEmail = `${roleType}@varuna.ai`;
    const rolePassword = `${roleType}123`;
    setEmail(roleEmail);
    setPassword(rolePassword);

    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email: roleEmail, password: rolePassword }),
      });

      const data = await response.json();
      if (data.user) {
        try {
          localStorage.setItem("profile", JSON.stringify(data.user));
          localStorage.setItem("user", JSON.stringify(data.user));
        } catch {}
      }

      setSuccess(`Authenticated as ${roleType.toUpperCase()}! Redirecting...`);
      const target = roleType === "admin" ? "/command-center" : redirectTarget;
      setTimeout(() => {
        router.push(target);
      }, 300);
    } catch (err: any) {
      setError(err?.message || "Demo login failed");
    } finally {
      setLoading(false);
    }
  };

  // Standard Password Authentication
  const handlePasswordLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError("Please provide both email and password.");
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      const response = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.message || "Invalid credentials");
      }

      if (data.user) {
        try {
          localStorage.setItem("profile", JSON.stringify(data.user));
          localStorage.setItem("user", JSON.stringify(data.user));
        } catch {}
      }

      setSuccess("Access granted. Initializing session...");
      setTimeout(() => {
        router.push(redirectTarget);
      }, 300);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Authentication failed. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  };

  // Send OTP
  const sendLoginOtp = async () => {
    if (!email) {
      setError("Please enter your email first");
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch("/api/send-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, type: "login" }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.message || "Failed to send OTP");
      setOtpSent(true);
      setCountdown(30);
      setSuccess("OTP dispatched! Check your email.");
      if (data?.devOtp) setOtp(String(data.devOtp));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send OTP");
    } finally {
      setLoading(false);
    }
  };

  // Verify OTP
  const verifyLoginOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!otp || otp.length !== 6) {
      setError("Enter a valid 6-digit OTP");
      return;
    }
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const response = await fetch("/api/verify-otp", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, otp, type: "login" }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data?.message || "OTP verification failed");
      if (data.user) {
        try {
          localStorage.setItem("profile", JSON.stringify(data.user));
          localStorage.setItem("user", JSON.stringify(data.user));
        } catch {}
      }
      setSuccess("Access granted. Redirecting...");
      setTimeout(() => {
        router.push(redirectTarget);
      }, 300);
    } catch (err) {
      setError(err instanceof Error ? err.message : "OTP verification failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full overflow-hidden bg-gradient-to-br from-slate-950 via-[#0a1628] to-slate-950 flex flex-col justify-center items-center px-4 py-16">
      <SonarGridBackground />

      {/* Submarine ambient glows */}
      <div className="absolute top-1/3 -left-40 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-1/3 -right-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative z-10 w-full max-w-md mx-auto">
        {/* Defence Emblem Header */}
        <div className="text-center mb-5">
          <div className="relative inline-block mb-3">
            <div className="absolute -inset-4 rounded-full border border-dashed border-cyan-500/20 animate-spin" style={{ animationDuration: "35s" }} />
            <div className="absolute -inset-2 rounded-full border border-dotted border-amber-500/20 animate-spin" style={{ animationDuration: "25s", animationDirection: "reverse" }} />
            <div className="relative w-16 h-16 rounded-full border-2 border-cyan-400/50 bg-gradient-to-br from-slate-900 to-slate-800 flex items-center justify-center shadow-xl shadow-cyan-500/10">
              <Anchor className="w-8 h-8 text-cyan-400 animate-pulse" style={{ animationDuration: "3s" }} />
            </div>
          </div>

          <h1 className="font-orbitron text-base font-bold tracking-[0.25em] text-cyan-100 uppercase">
            Ministry of Earth Sciences (MoES)
          </h1>
          <p className="text-[10px] font-space-mono text-cyan-300/60 uppercase tracking-[0.3em] mt-0.5">
            VARUNA AI Defence Sonar System
          </p>
          <div className="text-[9px] font-space-mono text-slate-500 mt-1">
            {currentTime} • SECURE PORTAL
          </div>
        </div>

        {/* ═══ INSTANT ONE-CLICK DEMO ROLES ═══ */}
        <div className="mb-4 bg-slate-900/80 backdrop-blur-md rounded-xl p-3 border border-cyan-500/20 shadow-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[9px] font-space-mono text-cyan-300 font-bold uppercase tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-3 h-3 text-cyan-400" /> Instant Demo Access (No Setup Needed)
            </span>
            <span className="text-[8px] font-space-mono text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/30">
              Active
            </span>
          </div>
          <div className="grid grid-cols-3 gap-2">
            <button
              type="button"
              onClick={() => handleRoleDemoLogin("researcher")}
              disabled={loading}
              className="py-2.5 px-2 rounded-lg bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-400/40 text-cyan-200 font-orbitron font-bold text-[9px] tracking-wider flex flex-col items-center justify-center gap-1 transition-all active:scale-95 cursor-pointer shadow-sm hover:shadow-cyan-500/20"
            >
              <span className="text-sm">👨‍🔬</span>
              <span>RESEARCHER</span>
            </button>
            <button
              type="button"
              onClick={() => handleRoleDemoLogin("admin")}
              disabled={loading}
              className="py-2.5 px-2 rounded-lg bg-purple-500/15 hover:bg-purple-500/25 border border-purple-400/40 text-purple-200 font-orbitron font-bold text-[9px] tracking-wider flex flex-col items-center justify-center gap-1 transition-all active:scale-95 cursor-pointer shadow-sm hover:shadow-purple-500/20"
            >
              <span className="text-sm">🛡️</span>
              <span>ADMIN</span>
            </button>
            <button
              type="button"
              onClick={() => handleRoleDemoLogin("viewer")}
              disabled={loading}
              className="py-2.5 px-2 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-400/40 text-emerald-200 font-orbitron font-bold text-[9px] tracking-wider flex flex-col items-center justify-center gap-1 transition-all active:scale-95 cursor-pointer shadow-sm hover:shadow-emerald-500/20"
            >
              <span className="text-sm">🌊</span>
              <span>VIEWER</span>
            </button>
          </div>
        </div>

        {/* Method Switcher */}
        <div className="grid grid-cols-3 gap-1 bg-slate-900/70 backdrop-blur-md rounded-lg p-1 border border-cyan-500/15 mb-4">
          <button
            type="button"
            onClick={() => {
              setMethod("password");
              setError(null);
              setSuccess(null);
            }}
            className={`rounded-md py-2 text-[10px] font-space-mono font-bold uppercase tracking-wider transition-all ${
              method === "password"
                ? "bg-cyan-500/20 border border-cyan-400/40 text-cyan-200 shadow-md shadow-cyan-500/10"
                : "text-slate-400 hover:text-cyan-300 hover:bg-cyan-500/5"
            }`}
          >
            <Lock className="w-3 h-3 inline mr-1 -mt-0.5" />
            Password
          </button>
          <button
            type="button"
            onClick={() => {
              setMethod("otp");
              setPassword("");
              setShowPassword(false);
              setOtp("");
              setOtpSent(false);
              setError(null);
              setSuccess(null);
            }}
            className={`rounded-md py-2 text-[10px] font-space-mono font-bold uppercase tracking-wider transition-all ${
              method === "otp"
                ? "bg-cyan-500/20 border border-cyan-400/40 text-cyan-200 shadow-md shadow-cyan-500/10"
                : "text-slate-400 hover:text-cyan-300 hover:bg-cyan-500/5"
            }`}
          >
            <Fingerprint className="w-3 h-3 inline mr-1 -mt-0.5" />
            OTP
          </button>
          <button
            type="button"
            onClick={() => {
              setMethod("rfid");
              setError(null);
              setSuccess(null);
            }}
            className={`rounded-md py-2 text-[10px] font-space-mono font-bold uppercase tracking-wider transition-all ${
              method === "rfid"
                ? "bg-amber-500/20 border border-amber-400/40 text-amber-200 shadow-md shadow-amber-500/10"
                : "text-slate-400 hover:text-amber-300 hover:bg-amber-500/5"
            }`}
          >
            <Cpu className="w-3 h-3 inline mr-1 -mt-0.5" />
            RFID
          </button>
        </div>

        {/* Main Login Card */}
        <form
          onSubmit={
            method === "password"
              ? handlePasswordLogin
              : method === "otp"
              ? verifyLoginOtp
              : (e) => e.preventDefault()
          }
        >
          <div className="relative bg-slate-900/80 backdrop-blur-xl rounded-2xl border border-cyan-500/20 shadow-2xl shadow-black/50 overflow-hidden">
            {/* Header bar */}
            <div className="bg-gradient-to-r from-cyan-950/40 via-blue-950/30 to-cyan-950/40 px-4 py-2 border-b border-cyan-500/15 flex items-center justify-between">
              <span className="text-[8px] font-space-mono text-cyan-300/60 uppercase tracking-widest flex items-center gap-1.5">
                <ShieldCheck className="w-3 h-3 text-cyan-400" /> SECURE_AUTH v5.0
              </span>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[7px] font-space-mono text-emerald-400 uppercase font-bold">
                  AES-256 TLS 1.3
                </span>
              </div>
            </div>

            <div className="p-6">
              {error && (
                <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
                  <span className="text-red-300 text-[11px] font-space-mono">
                    {error}
                  </span>
                </div>
              )}
              {success && (
                <div className="mb-4 p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  <span className="text-emerald-300 text-[11px] font-space-mono">
                    {success}
                  </span>
                </div>
              )}

              <div className="space-y-4">
                {method === "rfid" ? (
                  /* RFID SCAN MODE */
                  <div className="flex flex-col items-center py-4">
                    <div className="relative w-24 h-24 mb-4">
                      <div
                        className={`absolute inset-0 rounded-full border-2 ${
                          rfidStatus === "success"
                            ? "border-emerald-400/40"
                            : rfidStatus === "denied"
                            ? "border-red-400/40"
                            : "border-cyan-400/30 animate-pulse"
                        }`}
                      />
                      <div className="absolute inset-4 rounded-full flex items-center justify-center bg-cyan-500/10">
                        {rfidStatus === "success" ? (
                          <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                        ) : rfidStatus === "denied" ? (
                          <XCircle className="w-8 h-8 text-red-400" />
                        ) : (
                          <Cpu className="w-8 h-8 text-cyan-400 animate-pulse" />
                        )}
                      </div>
                    </div>

                    <h3 className="font-orbitron text-xs font-bold tracking-[0.2em] uppercase text-cyan-200 mb-1">
                      {rfidStatus === "success"
                        ? "ACCESS GRANTED"
                        : rfidStatus === "denied"
                        ? "ACCESS DENIED"
                        : "TAP RFID CARD"}
                    </h3>
                    <p className="text-[9px] font-space-mono text-slate-400 uppercase text-center mb-3">
                      {rfidReady
                        ? "Reader ready — place card near scanner"
                        : "Ready in offline mode (or connect hardware reader)"}
                    </p>

                    <button
                      type="button"
                      onClick={() => {
                        setRfidStatus("success");
                        setSuccess("ACCESS GRANTED — Commander Varuna (Simulated RFID)");
                        try {
                          const rfidUser = {
                            id: "rfid-sim-" + Date.now(),
                            email: "operator@varuna.ai",
                            role: "admin",
                            firstName: "Chief",
                            lastName: "Officer",
                          };
                          localStorage.setItem("profile", JSON.stringify(rfidUser));
                          localStorage.setItem("user", JSON.stringify(rfidUser));
                        } catch {}
                        setTimeout(() => router.push(redirectTarget), 400);
                      }}
                      className="px-4 py-2 rounded bg-amber-500/15 hover:bg-amber-500/25 border border-amber-400/40 text-amber-200 text-[9px] font-orbitron uppercase tracking-wider transition-all cursor-pointer"
                    >
                      Simulate RFID Tap
                    </button>
                  </div>
                ) : (
                  <>
                    {/* Email Field */}
                    <div className="space-y-1">
                      <label
                        htmlFor="email"
                        className="text-[9px] font-space-mono uppercase tracking-[0.2em] text-slate-400 flex items-center gap-1.5"
                      >
                        <Mail className="w-3 h-3" />
                        Officer Email / Service ID
                      </label>
                      <div className="relative">
                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyan-500/40" />
                        <input
                          id="email"
                          name="email"
                          type="email"
                          required
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                          placeholder="scientist@moes.gov.in"
                          className="w-full rounded-lg border border-cyan-500/20 bg-slate-800/70 pl-10 pr-3 py-2.5 text-sm text-cyan-100 placeholder:text-slate-600 outline-none focus:border-cyan-400/60 focus:ring-1 focus:ring-cyan-400/30 transition-all font-space-mono"
                        />
                      </div>
                    </div>

                    {method === "password" ? (
                      /* Password Field */
                      <div className="space-y-1">
                        <label
                          htmlFor="password"
                          className="text-[9px] font-space-mono uppercase tracking-[0.2em] text-slate-400 flex items-center gap-1.5"
                        >
                          <Lock className="w-3 h-3" />
                          Access Code
                        </label>
                        <div className="relative">
                          <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-cyan-500/40" />
                          <input
                            id="password"
                            name="password"
                            type={showPassword ? "text" : "password"}
                            required
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter access code"
                            className="w-full rounded-lg border border-cyan-500/20 bg-slate-800/70 pl-10 pr-10 py-2.5 text-sm text-cyan-100 placeholder:text-slate-600 outline-none focus:border-cyan-400/60 focus:ring-1 focus:ring-cyan-400/30 transition-all font-space-mono"
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-cyan-400 transition-colors"
                          >
                            {showPassword ? (
                              <EyeOff className="w-4 h-4" />
                            ) : (
                              <Eye className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* OTP Field */
                      <div className="space-y-1.5">
                        <label
                          htmlFor="otp"
                          className="text-[9px] font-space-mono uppercase tracking-[0.2em] text-slate-400 flex items-center gap-1.5"
                        >
                          <Fingerprint className="w-3 h-3" />
                          One-Time Verification Code
                        </label>
                        <input
                          id="otp"
                          name="otp"
                          type="text"
                          inputMode="numeric"
                          maxLength={6}
                          value={otp}
                          onChange={(e) =>
                            setOtp(e.target.value.replace(/\D/g, ""))
                          }
                          placeholder="------"
                          className="w-full rounded-lg border border-cyan-500/20 bg-slate-800/70 px-3 py-2.5 text-center text-lg tracking-[0.4em] text-cyan-100 outline-none focus:border-cyan-400/60 focus:ring-1 focus:ring-cyan-400/30 transition-all font-space-mono"
                          disabled={!otpSent}
                        />
                        <div className="flex items-center justify-between text-[9px] text-slate-500 font-space-mono mt-1">
                          <button
                            type="button"
                            onClick={sendLoginOtp}
                            disabled={loading || countdown > 0}
                            className="text-cyan-400 hover:text-cyan-300 disabled:opacity-40 uppercase tracking-wider"
                          >
                            {otpSent
                              ? countdown > 0
                                ? `Resend ${countdown}s`
                                : "Resend Code"
                              : "Send Verification Code"}
                          </button>
                          <span className="text-slate-600">
                            {otpSent ? "Expires in 10m" : "Secure OTP"}
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Submit Button */}
                    <button
                      type="submit"
                      disabled={loading || (method === "otp" && !otpSent)}
                      className="relative w-full py-3 rounded-lg bg-gradient-to-r from-cyan-600 via-blue-600 to-cyan-600 text-white font-orbitron text-[10px] tracking-[0.25em] uppercase overflow-hidden border border-cyan-400/30 shadow-lg shadow-cyan-500/20 hover:shadow-cyan-500/40 transition-all disabled:opacity-40 cursor-pointer"
                    >
                      {loading ? (
                        <span className="flex items-center justify-center gap-2">
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                          Authenticating...
                        </span>
                      ) : (
                        <span className="flex items-center justify-center gap-2">
                          <ShieldCheck className="w-4 h-4" />
                          {method === "otp" ? "Verify & Authenticate" : "Authenticate"}
                        </span>
                      )}
                    </button>

                    <div className="flex items-center gap-3 my-1">
                      <div className="h-px flex-1 bg-gradient-to-r from-transparent to-cyan-500/20" />
                      <span className="text-[8px] font-space-mono text-slate-600 uppercase tracking-widest">
                        or
                      </span>
                      <div className="h-px flex-1 bg-gradient-to-l from-transparent to-cyan-500/20" />
                    </div>

                    <GoogleSignInButton label="Sign in with Google" />
                  </>
                )}
              </div>
            </div>

            {/* Footer Status */}
            <div className="bg-slate-950/60 px-4 py-2 border-t border-cyan-500/10 flex items-center justify-between text-[7px] font-space-mono text-slate-500 uppercase tracking-wider">
              <span>Session: AES-256-GCM</span>
              <span>Protocol: TLS 1.3</span>
            </div>
          </div>
        </form>

        <p className="mt-5 text-center text-[10px] text-slate-400 font-space-mono tracking-wider">
          New officer?{" "}
          <Link
            href="/auth/register"
            className="text-cyan-400 hover:text-cyan-300 uppercase tracking-widest font-bold ml-1"
          >
            Request Access
          </Link>
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen w-full bg-slate-950 flex items-center justify-center text-cyan-400 font-orbitron text-xs tracking-widest">
          INITIALIZING SECURE PORTAL...
        </div>
      }
    >
      <LoginFormContent />
    </Suspense>
  );
}
