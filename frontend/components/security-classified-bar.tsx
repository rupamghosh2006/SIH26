"use client";

import { useEffect, useState } from "react";

interface SecurityClassifiedBarProps {
  level?: "TOP SECRET" | "SECRET" | "CLASSIFIED" | "RESTRICTED";
  showTimer?: boolean;
}

export function SecurityClassifiedBar({
  level = "CLASSIFIED",
  showTimer = true,
}: SecurityClassifiedBarProps) {
  const [time, setTime] = useState("");
  const [sessionId, setSessionId] = useState("");

  useEffect(() => {
    // Generate session ID
    setSessionId(
      `SES-${Math.random().toString(36).substr(2, 8).toUpperCase()}`,
    );

    const tick = () => {
      const now = new Date();
      setTime(
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

  return (
    <>
      {/* Top classified bar */}
      <div className="classified-bar">
        {level} // MINISTRY OF EARTH SCIENCES (MoES) // VARUNA AI MARINE DEBRIS DETECTION SYSTEM // {level}
      </div>

      {/* Security info strip below */}
      <div className="bg-slate-950/95 border-b border-cyan-500/20 px-4 py-1.5 flex items-center justify-between text-[9px] font-space-mono tracking-widest relative z-50">
        <div className="flex items-center gap-4">
          <span className="access-level access-level-classified">
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse inline-block" />
            CLEARANCE: LEVEL 5
          </span>
          <span className="text-cyan-500/50">SESSION: {sessionId}</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-cyan-500/50">ENCRYPTION: AES-256-GCM</span>
          {showTimer && (
            <span className="text-cyan-400/70 font-orbitron">{time}</span>
          )}
        </div>
      </div>
    </>
  );
}

export function SecurityWatermark() {
  return (
    <div className="security-watermark" aria-hidden="true">
      CLASSIFIED
    </div>
  );
}

export function SecurityPerimeter() {
  return <div className="security-perimeter" aria-hidden="true" />;
}

export function SecurityFooter() {
  return (
    <div className="relative z-20 border-t border-cyan-500/20 bg-slate-950/90 backdrop-blur-md">
      <div className="classified-bar">
        ACOUSTIC RESEARCH // SIH26057 • VARUNA AI PLATFORM // UNDERWATER SONAR DEBRIS INTELLIGENCE
      </div>
      <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500/30 to-blue-500/30 flex items-center justify-center border border-cyan-500/50">
            <span className="text-cyan-300 text-xs font-orbitron font-black">
              ⚓
            </span>
          </div>
          <div>
            <p className="text-[10px] text-cyan-300/60 font-space-mono uppercase tracking-wider">
              Ministry of Earth Sciences (MoES) • Netaji Subhash Engineering College, Kolkata • Varuna AI Platform
            </p>
            <p className="text-[8px] text-cyan-500/40 font-space-mono">
              SIH26057: Automated Underwater Marine Debris and Anomaly Detection System
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 mt-2 sm:mt-0">
          <span className="security-badge">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            System Online
          </span>
          <span className="text-[8px] text-cyan-500/40 font-space-mono">
            v2.4.0
          </span>
        </div>
      </div>
    </div>
  );
}
