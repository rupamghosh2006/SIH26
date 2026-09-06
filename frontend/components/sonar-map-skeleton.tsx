"use client";

import React from "react";
import { Radar, Layers, Plus, Minus, Waves } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface SonarMapSkeletonProps {
  className?: string;
}

export default function SonarMapSkeleton({ className = "" }: SonarMapSkeletonProps) {
  return (
    <div
      className={`relative w-full h-[420px] bg-slate-950/95 border-2 border-cyan-500/30 rounded-xl overflow-hidden select-none font-space-mono shadow-inner shadow-cyan-950/50 ${className}`}
    >
      {/* Hydrographic Grid Background */}
      <div
        className="absolute inset-0 opacity-20 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(6, 182, 212, 0.2) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(6, 182, 212, 0.2) 1px, transparent 1px)
          `,
          backgroundSize: "40px 40px",
        }}
      />

      {/* Bathymetric Depth Contour Shimmer */}
      <div className="absolute inset-0 bg-gradient-to-tr from-cyan-950/40 via-blue-950/20 to-slate-950/60 animate-pulse pointer-events-none" />

      {/* Concentric Sonar Range Rings & Crosshairs */}
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        {/* Outer Ring - 500m */}
        <div className="relative w-[460px] h-[460px] rounded-full border border-cyan-500/15 flex items-center justify-center">
          <span className="absolute -top-3 text-[9px] text-cyan-400/50 bg-slate-950 px-1 font-space-mono">
            500m SWATH
          </span>

          {/* Middle Ring - 250m */}
          <div className="relative w-[300px] h-[300px] rounded-full border border-cyan-500/25 flex items-center justify-center">
            <span className="absolute -top-3 text-[9px] text-cyan-400/60 bg-slate-950 px-1 font-space-mono">
              250m RANGE
            </span>

            {/* Inner Ring - 100m */}
            <div className="relative w-[150px] h-[150px] rounded-full border border-cyan-400/40 flex items-center justify-center">
              <span className="absolute -top-3 text-[9px] text-cyan-300/80 bg-slate-950 px-1 font-space-mono">
                100m NADIR
              </span>
              <div className="w-2 h-2 rounded-full bg-cyan-400/60 animate-ping" />
            </div>
          </div>
        </div>

        {/* Crosshair Axes */}
        <div className="absolute inset-x-0 h-px border-b border-dashed border-cyan-500/20" />
        <div className="absolute inset-y-0 w-px border-r border-dashed border-cyan-500/20" />

        {/* Compass Cardinal Points */}
        <span className="absolute top-2 text-[10px] font-orbitron font-bold text-cyan-400/60 tracking-wider">
          000° N
        </span>
        <span className="absolute bottom-2 text-[10px] font-orbitron font-bold text-cyan-400/60 tracking-wider">
          180° S
        </span>
        <span className="absolute right-2 text-[10px] font-orbitron font-bold text-cyan-400/60 tracking-wider">
          090° E
        </span>
        <span className="absolute left-2 text-[10px] font-orbitron font-bold text-cyan-400/60 tracking-wider">
          270° W
        </span>

        {/* Rotating Sonar Sweep Beam */}
        <div
          className="absolute w-[460px] h-[460px] rounded-full pointer-events-none"
          style={{
            background:
              "conic-gradient(from 0deg at 50% 50%, rgba(6, 182, 212, 0.25) 0deg, rgba(6, 182, 212, 0.05) 45deg, transparent 90deg, transparent 360deg)",
            animation: "spin 5s linear infinite",
          }}
        />
      </div>

      {/* Simulated Anomaly Target Pings with Skeletons */}
      {/* Target 1 - Top Right */}
      <div className="absolute top-[28%] right-[32%] z-10 flex items-center gap-2 pointer-events-none">
        <div className="relative flex items-center justify-center">
          <span className="animate-ping absolute inline-flex h-4 w-4 rounded-full bg-cyan-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-300" />
        </div>
        <div className="space-y-1 bg-slate-900/80 border border-cyan-500/30 p-1.5 rounded backdrop-blur-sm shadow-md">
          <Skeleton className="h-2.5 w-24 bg-cyan-500/20" />
          <Skeleton className="h-2 w-16 bg-cyan-500/10" />
        </div>
      </div>

      {/* Target 2 - Bottom Left */}
      <div className="absolute bottom-[24%] left-[28%] z-10 flex items-center gap-2 pointer-events-none">
        <div className="relative flex items-center justify-center">
          <span className="animate-ping absolute inline-flex h-4 w-4 rounded-full bg-amber-400 opacity-75" />
          <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-300" />
        </div>
        <div className="space-y-1 bg-slate-900/80 border border-amber-500/30 p-1.5 rounded backdrop-blur-sm shadow-md">
          <Skeleton className="h-2.5 w-28 bg-amber-500/20" />
          <Skeleton className="h-2 w-20 bg-amber-500/10" />
        </div>
      </div>

      {/* Target 3 - Center Right */}
      <div className="absolute top-[58%] right-[22%] z-10 flex items-center gap-2 pointer-events-none">
        <div className="relative flex items-center justify-center">
          <span className="animate-ping absolute inline-flex h-4 w-4 rounded-full bg-cyan-400 opacity-60" />
          <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-cyan-400" />
        </div>
        <div className="space-y-1 bg-slate-900/80 border border-cyan-500/25 p-1 rounded backdrop-blur-sm">
          <Skeleton className="h-2 w-20 bg-cyan-500/20" />
        </div>
      </div>

      {/* Top Left: Map Controls Skeleton */}
      <div className="absolute top-4 left-4 z-20 flex flex-col gap-2">
        <div className="bg-slate-900/80 border border-cyan-500/30 rounded-lg p-1 flex flex-col gap-1 shadow-lg backdrop-blur-sm">
          <div className="w-7 h-7 rounded bg-cyan-950/60 border border-cyan-500/20 flex items-center justify-center text-cyan-400/50">
            <Plus className="w-3.5 h-3.5" />
          </div>
          <div className="w-7 h-7 rounded bg-cyan-950/60 border border-cyan-500/20 flex items-center justify-center text-cyan-400/50">
            <Minus className="w-3.5 h-3.5" />
          </div>
        </div>

        <div className="bg-slate-900/80 border border-cyan-500/30 rounded-lg px-2.5 py-1.5 flex items-center gap-2 shadow-lg backdrop-blur-sm">
          <Layers className="w-3.5 h-3.5 text-cyan-400/60" />
          <Skeleton className="h-3 w-16 bg-cyan-500/20" />
        </div>
      </div>

      {/* Top Right: Telemetry & Geo Coordinates Skeleton */}
      <div className="absolute top-4 right-4 z-20 bg-slate-900/85 border border-cyan-500/30 rounded-lg p-2.5 shadow-lg backdrop-blur-sm space-y-1.5">
        <div className="flex items-center gap-2">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 animate-pulse" />
          <span className="text-[10px] text-cyan-300 font-semibold tracking-wider uppercase font-orbitron">
            GIS Bathymetric Matrix
          </span>
        </div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-[9px] text-cyan-400/60">LAT:</span>
            <Skeleton className="h-2.5 w-24 bg-cyan-500/20" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[9px] text-cyan-400/60">LON:</span>
            <Skeleton className="h-2.5 w-24 bg-cyan-500/20" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[9px] text-cyan-400/60">RES:</span>
            <Skeleton className="h-2.5 w-14 bg-cyan-500/20" />
          </div>
        </div>
      </div>

      {/* Center HUD: Tactical Processing Status */}
      <div className="absolute inset-0 flex items-center justify-center z-20 pointer-events-none">
        <div className="bg-slate-950/90 border border-cyan-400/40 rounded-xl p-5 shadow-2xl shadow-cyan-500/20 backdrop-blur-md max-w-sm w-full mx-4 text-center space-y-3">
          <div className="relative flex items-center justify-center mx-auto w-12 h-12">
            <div className="w-12 h-12 rounded-full border-2 border-cyan-400/30 border-t-cyan-400 animate-spin" />
            <Radar className="w-5 h-5 text-cyan-300 absolute animate-pulse" />
          </div>

          <div>
            <div className="text-cyan-300 font-orbitron text-xs sm:text-sm font-bold tracking-wider animate-pulse flex items-center justify-center gap-2">
              <span>SYNTHESIZING GIS SONAR OVERLAY</span>
            </div>
            <p className="text-[11px] text-slate-400 font-space-mono mt-1">
              Georeferencing acoustic swath • Slant-to-ground range correction
            </p>
          </div>

          {/* Shimmering Progress Bar */}
          <div className="w-full h-1.5 rounded-full bg-cyan-950/60 border border-cyan-500/30 overflow-hidden relative">
            <div className="h-full bg-gradient-to-r from-transparent via-cyan-400 to-transparent w-2/3 animate-[shimmer_1.5s_infinite] -translate-x-full" />
          </div>

          <div className="flex items-center justify-between text-[9px] text-cyan-400/70 font-space-mono">
            <span>Acoustic Shadow Verification</span>
            <span className="animate-pulse text-cyan-300">Computing...</span>
          </div>
        </div>
      </div>

      {/* Bottom Left: Hydrographic Scale & Sensor Spec */}
      <div className="absolute bottom-4 left-4 z-20 flex items-center gap-3">
        <div className="bg-slate-900/80 border border-cyan-500/30 rounded-lg px-2.5 py-1.5 shadow-lg backdrop-blur-sm flex items-center gap-2">
          <Waves className="w-3.5 h-3.5 text-cyan-400/70" />
          <Skeleton className="h-3 w-28 bg-cyan-500/20" />
        </div>
        <div className="hidden sm:flex bg-slate-900/80 border border-cyan-500/25 rounded-lg px-2 py-1 items-center gap-1.5 text-[9px] text-cyan-400/60">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>SRR Dynamic Pipeline</span>
        </div>
      </div>

      {/* Bottom Right: Target Classification Filter Skeleton */}
      <div className="absolute bottom-4 right-4 z-20 hidden md:flex items-center gap-2 bg-slate-900/80 border border-cyan-500/30 rounded-lg p-1.5 shadow-lg backdrop-blur-sm">
        <Skeleton className="h-3 w-14 bg-cyan-500/20" />
        <Skeleton className="h-3 w-14 bg-cyan-500/20" />
        <Skeleton className="h-3 w-14 bg-cyan-500/20" />
      </div>
    </div>
  );
}
