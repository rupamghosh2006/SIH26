"use client";

import { useEffect, useState } from "react";

interface SecurityClassifiedBarProps {
  level?: "TOP SECRET" | "SECRET" | "CLASSIFIED" | "RESTRICTED" | string;
  showTimer?: boolean;
}

export function SecurityClassifiedBar({
  showTimer = true,
}: SecurityClassifiedBarProps) {
  const [time, setTime] = useState("");
  const [surveyId, setSurveyId] = useState("");

  useEffect(() => {
    setSurveyId(
      `SURV-${Math.random().toString(36).substr(2, 8).toUpperCase()}`,
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
      {/* Top MoES hydrographic bar */}
      <div className="classified-bar bg-cyan-950 text-cyan-300 font-mono tracking-widest text-[11px] py-1 text-center border-b border-cyan-500/30">
        MINISTRY OF EARTH SCIENCES (MoES) • NATIONAL INSTITUTE OF OCEAN TECHNOLOGY (NIOT) • BENTHIC SURVEY PORTAL • SIH26057
      </div>

      {/* Hydrographic acoustic telemetry strip below */}
      <div className="bg-slate-950/95 border-b border-cyan-500/20 px-4 py-1.5 flex items-center justify-between text-[9px] font-space-mono tracking-widest relative z-50">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-cyan-400 font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block" />
            SONAR: DUAL-FREQ (455 / 800 kHz)
          </span>
          <span className="text-cyan-500/70 hidden sm:inline">SWATH: 150m (75m PORT / 75m STBD)</span>
          <span className="text-cyan-500/50 hidden md:inline">SURVEY REF: {surveyId}</span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-cyan-500/60 hidden lg:inline">DATUM: WGS-84 / UTM-43N</span>
          {showTimer && (
            <span className="text-cyan-400/80 font-orbitron">{time}</span>
          )}
        </div>
      </div>
    </>
  );
}

export function SecurityWatermark() {
  return null;
}

export function SecurityPerimeter() {
  return <div className="security-perimeter" aria-hidden="true" />;
}

export function SecurityFooter() {
  return (
    <div className="relative z-20 border-t border-cyan-500/20 bg-slate-950/90 backdrop-blur-md">
      <div className="classified-bar bg-cyan-950/60 text-cyan-400/80 text-[10px] py-0.5 text-center font-mono">
        HYDROGRAPHIC ACOUSTIC RESEARCH // SIH26057 • VARUNA PLATFORM // UNDERWATER SONAR DEBRIS INTELLIGENCE
      </div>
      <div className="max-w-7xl mx-auto px-4 py-4 flex flex-col sm:flex-row items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500/30 to-blue-500/30 flex items-center justify-center border border-cyan-500/50">
            <span className="text-cyan-300 text-xs font-orbitron font-black">
              ⚓
            </span>
          </div>
          <div>
            <p className="text-[10px] text-cyan-300/80 font-space-mono uppercase tracking-wider">
              Ministry of Earth Sciences (MoES) • Netaji Subhash Engineering College, Kolkata • Varuna Platform
            </p>
            <p className="text-[8px] text-cyan-500/60 font-space-mono">
              SIH26057: Automated Underwater Marine Debris and Anomaly Detection System
            </p>
          </div>
        </div>
        <div className="flex items-center gap-4 mt-2 sm:mt-0">
          <span className="security-badge flex items-center gap-1 text-xs text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            Acoustic Pipeline Online
          </span>
          <span className="text-[8px] text-cyan-500/40 font-space-mono">
            v2.4.0-MoES
          </span>
        </div>
      </div>
    </div>
  );
}
