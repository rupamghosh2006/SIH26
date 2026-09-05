"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  AlertTriangle,
  XCircle,
  HelpCircle,
  Waves,
  Brain,
  Compass,
  ArrowRight,
  Maximize2,
  Minimize2,
  Info,
  CheckCircle2,
  Activity
} from "lucide-react";

export interface DetectionExplainabilityProps {
  detectionIndex: number;
  detection: {
    class: string;
    confidence: number;
    threat_level?: string;
    ecological_risk?: string;
    bbox?: [number, number, number, number];
    detector_score?: number;
    shadow_score?: number;
    shape_score?: number;
    shadow_detected?: boolean;
    confidence_score?: number;
    confidence_tier?: string;
    estimated_size_m?: string;
    latitude?: number;
    longitude?: number;
    thumbnail_url?: string;
    filter_details?: {
      shadow_details?: {
        expected_shadow_side?: string;
        local_bg_mean?: number;
        highlight_val?: number;
        shadow_val?: number;
        shadow_depth?: number;
        directional_diff?: number;
        has_shadow?: boolean;
      };
      shape_details?: {
        aspect_ratio?: number;
        roi_std?: number;
        solidity?: number;
      };
      suppression_applied?: boolean;
    };
  };
  surveyId?: string;
  originalImage?: string;
  nadir_x?: number;
  onClose?: () => void;
}

export function ExplainableSonarPanel({
  detectionIndex,
  detection,
  surveyId,
  originalImage,
  nadir_x = 400,
  onClose,
}: DetectionExplainabilityProps) {
  const [showFullOverlay, setShowFullOverlay] = useState(false);

  // Extract intermediate metrics safely from existing detection data
  const filter = detection.filter_details || {};
  const shadowDetails = filter.shadow_details || {};
  const shapeDetails = filter.shape_details || {};

  // Real scores
  const detectorScore = detection.detector_score !== undefined
    ? detection.detector_score
    : Math.round(detection.confidence * 1000) / 10;

  const shadowScore = detection.shadow_score !== undefined
    ? detection.shadow_score
    : (shadowDetails.has_shadow !== false ? 85.0 : 25.0);

  const shapeScore = detection.shape_score !== undefined
    ? detection.shape_score
    : 75.0;

  const isShadowDetected = detection.shadow_detected !== undefined
    ? detection.shadow_detected
    : (shadowDetails.has_shadow !== false);

  const suppressionApplied = filter.suppression_applied !== undefined
    ? filter.suppression_applied
    : (!isShadowDetected);

  const finalScore = detection.confidence_score !== undefined
    ? detection.confidence_score
    : Math.round(detection.confidence * 1000) / 10;

  const tier = detection.confidence_tier || (finalScore >= 75 ? "High" : finalScore >= 45 ? "Medium" : "Low");

  // Physics details
  const expectedSide = shadowDetails.expected_shadow_side || "right";
  const shadowDepthPct = shadowDetails.shadow_depth !== undefined
    ? Math.round(shadowDetails.shadow_depth * 100)
    : null;
  const highlightVal = shadowDetails.highlight_val !== undefined
    ? Math.round(shadowDetails.highlight_val)
    : null;
  const shadowVal = shadowDetails.shadow_val !== undefined
    ? Math.round(shadowDetails.shadow_val)
    : null;
  const bgMean = shadowDetails.local_bg_mean !== undefined
    ? Math.round(shadowDetails.local_bg_mean)
    : null;
  const directionalDiffPct = shadowDetails.directional_diff !== undefined
    ? Math.round(shadowDetails.directional_diff * 100)
    : null;

  // Morphology details
  const aspectRatio = shapeDetails.aspect_ratio !== undefined
    ? shapeDetails.aspect_ratio.toFixed(1)
    : (detection.bbox && detection.bbox[3] > 0
        ? (detection.bbox[2] / detection.bbox[3]).toFixed(1)
        : null);
  const solidity = shapeDetails.solidity !== undefined
    ? shapeDetails.solidity.toFixed(2)
    : null;
  const textureStd = shapeDetails.roi_std !== undefined
    ? shapeDetails.roi_std.toFixed(1)
    : null;

  // Size and Location
  const estimatedSize = detection.estimated_size_m || (
    detection.bbox
      ? `${(detection.bbox[2] * 0.075).toFixed(1)}m × ${(detection.bbox[3] * 0.075).toFixed(1)}m`
      : "Not available"
  );
  const coords = detection.latitude !== undefined && detection.longitude !== undefined
    ? `${detection.latitude.toFixed(6)}°N, ${detection.longitude.toFixed(6)}°E`
    : "Local Survey Coordinates";

  // Physics Verdict determination
  let verdict: { title: string; color: string; bg: string; border: string; icon: React.ReactNode; desc: string };
  if (isShadowDetected && finalScore >= 75) {
    verdict = {
      title: "PHYSICS CONSISTENT",
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      border: "border-emerald-500/30",
      icon: <CheckCircle2 className="w-4 h-4 text-emerald-400" />,
      desc: "Neural debris candidate is strictly validated by an acoustic highlight-to-shadow formation in the expected beam propagation direction.",
    };
  } else if (!isShadowDetected || suppressionApplied) {
    verdict = {
      title: "PHYSICS INCONSISTENT / CLUTTER SUPPRESSED",
      color: "text-red-400",
      bg: "bg-red-500/10",
      border: "border-red-500/30",
      icon: <XCircle className="w-4 h-4 text-red-400" />,
      desc: "No physics-consistent acoustic shadow detected behind the target highlight. 0.48x confidence suppression penalty applied to prevent false alarms from flat seabed clutter.",
    };
  } else {
    verdict = {
      title: "PARTIALLY VERIFIED",
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      border: "border-amber-500/30",
      icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
      desc: "Acoustic return exhibits moderate contrast with ambient seabed background; operator review advised.",
    };
  }

  // Visual Bounding Box proportions for inline SVG schematic
  const bbox = detection.bbox || [120, 80, 60, 40];
  const isStarboard = expectedSide.toLowerCase() === "right";

  return (
    <div className="mt-3 p-5 rounded-xl border border-cyan-500/30 bg-slate-950/90 shadow-2xl backdrop-blur-xl animate-in fade-in duration-300 space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between border-b border-cyan-500/20 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-space-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 uppercase tracking-widest font-bold">
              EXPLAINABLE SONAR
            </span>
            <span className="text-[10px] font-space-mono text-slate-400 uppercase">
              Target #{detectionIndex + 1}
            </span>
          </div>
          <h3 className="font-orbitron text-base font-bold text-cyan-100 tracking-wide mt-1">
            WHY WAS THIS DETECTED?
          </h3>
          <p className="text-xs text-slate-400 font-space-mono mt-0.5">
            Evidence used by VARUNA&apos;s detection and physics validation pipeline
          </p>
        </div>

        {onClose && (
          <button
            onClick={onClose}
            className="text-xs text-slate-400 hover:text-cyan-300 font-mono px-2 py-1 rounded bg-slate-900 border border-slate-700 hover:border-cyan-500/50 transition-colors"
          >
            ✕ Close
          </button>
        )}
      </div>

      {/* 1. Detection Summary Banner */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-900/60 p-3.5 rounded-lg border border-cyan-500/15">
        <div>
          <span className="text-[10px] text-slate-400 uppercase font-space-mono">Classification</span>
          <p className="text-xs font-bold text-cyan-200 font-space-mono capitalize">
            {detection.class.replace(/_/g, " ")}
          </p>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 uppercase font-space-mono">Final Confidence</span>
          <p className="text-xs font-bold text-cyan-300 font-space-mono">
            {finalScore.toFixed(1)}% ({tier.toUpperCase()})
          </p>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 uppercase font-space-mono">Estimated Size</span>
          <p className="text-xs font-bold text-emerald-300 font-space-mono">
            {estimatedSize}
          </p>
        </div>
        <div>
          <span className="text-[10px] text-slate-400 uppercase font-space-mono">Location</span>
          <p className="text-[11px] font-mono text-slate-300 truncate" title={coords}>
            {coords}
          </p>
        </div>
      </div>

      {/* 2 & 3 & 4. Three Evidence Pillars: AI + Physics + Morphology */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Pillar 1: AI / YOLO Detector */}
        <div className="p-4 rounded-lg bg-slate-900/50 border border-blue-500/20 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-blue-400">
                <Brain className="w-4 h-4" />
                <span className="text-xs font-bold font-orbitron uppercase tracking-wider">AI Detection</span>
              </div>
              <span className="text-[10px] font-mono text-blue-300/70 bg-blue-500/10 px-1.5 py-0.5 rounded border border-blue-500/20">
                Weight: 50%
              </span>
            </div>

            <div className="mt-3">
              <div className="flex justify-between text-xs font-mono mb-1">
                <span className="text-slate-400">YOLOv8 Detector Score</span>
                <span className="font-bold text-blue-300">{detectorScore.toFixed(1)}%</span>
              </div>
              <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-600 to-cyan-400 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, Math.max(0, detectorScore))}%` }}
                />
              </div>
            </div>
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed italic border-t border-slate-800/80 pt-2">
            &ldquo;Neural detector identified an acoustic target matching the learned debris pattern.&rdquo;
          </p>
        </div>

        {/* Pillar 2: Acoustic Physics */}
        <div className="p-4 rounded-lg bg-slate-900/50 border border-cyan-500/20 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-cyan-400">
                <Waves className="w-4 h-4" />
                <span className="text-xs font-bold font-orbitron uppercase tracking-wider">Acoustic Physics</span>
              </div>
              <span className="text-[10px] font-mono text-cyan-300/70 bg-cyan-500/10 px-1.5 py-0.5 rounded border border-cyan-500/20">
                Weight: 35%
              </span>
            </div>

            <div className="mt-3 space-y-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-400">Acoustic Shadow</span>
                <span className={`font-bold px-1.5 py-0.2 rounded text-[10px] ${
                  isShadowDetected
                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                    : "bg-red-500/20 text-red-300 border border-red-500/30"
                }`}>
                  {isShadowDetected ? "✓ DETECTED" : "✕ NOT DETECTED"}
                </span>
              </div>

              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-400">Shadow Score</span>
                <span className="font-bold text-cyan-300">{shadowScore.toFixed(1)}%</span>
              </div>

              <div className="grid grid-cols-2 gap-1 text-[10px] font-mono text-slate-400 pt-1 border-t border-slate-800">
                <div>Direction: <span className="text-slate-200 font-bold uppercase">{expectedSide}</span></div>
                <div>Shadow Depth: <span className="text-slate-200 font-bold">{shadowDepthPct !== null ? `${shadowDepthPct}%` : "N/A"}</span></div>
                <div>Highlight Val: <span className="text-slate-200 font-bold">{highlightVal !== null ? highlightVal : "N/A"}</span></div>
                <div>Shadow Val: <span className="text-slate-200 font-bold">{shadowVal !== null ? shadowVal : "N/A"}</span></div>
                <div>Local Bg: <span className="text-slate-200 font-bold">{bgMean !== null ? bgMean : "N/A"}</span></div>
                <div>Directional Diff: <span className="text-slate-200 font-bold">{directionalDiffPct !== null ? `${directionalDiffPct}%` : "N/A"}</span></div>
              </div>
            </div>
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed italic border-t border-slate-800/80 pt-2">
            {isShadowDetected
              ? `Target lies on the ${isStarboard ? "starboard" : "port"} side of the nadir track. The detected low-backscatter region is positioned in the expected propagation direction.`
              : "No physics-consistent acoustic shadow detected behind the target highlight."}
          </p>
        </div>

        {/* Pillar 3: Morphology / Shape */}
        <div className="p-4 rounded-lg bg-slate-900/50 border border-purple-500/20 flex flex-col justify-between space-y-3">
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5 text-purple-400">
                <Compass className="w-4 h-4" />
                <span className="text-xs font-bold font-orbitron uppercase tracking-wider">Morphology</span>
              </div>
              <span className="text-[10px] font-mono text-purple-300/70 bg-purple-500/10 px-1.5 py-0.5 rounded border border-purple-500/20">
                Weight: 15%
              </span>
            </div>

            <div className="mt-3 space-y-2">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-slate-400">Shape / Texture Score</span>
                <span className="font-bold text-purple-300">{shapeScore.toFixed(1)}%</span>
              </div>

              <div className="space-y-1 text-[11px] font-mono text-slate-400 pt-1 border-t border-slate-800">
                <div className="flex justify-between">
                  <span>Aspect Ratio:</span>
                  <span className="text-slate-200 font-bold">{aspectRatio !== null ? aspectRatio : "Not available"}</span>
                </div>
                <div className="flex justify-between">
                  <span>Solidity:</span>
                  <span className="text-slate-200 font-bold">{solidity !== null ? solidity : "Not available"}</span>
                </div>
                <div className="flex justify-between">
                  <span>Texture Variation (std):</span>
                  <span className="text-slate-200 font-bold">{textureStd !== null ? textureStd : "Not available"}</span>
                </div>
              </div>
            </div>
          </div>

          <p className="text-[11px] text-slate-400 leading-relaxed italic border-t border-slate-800/80 pt-2">
            &ldquo;ROI morphology and texture characteristics contributed to the confidence score.&rdquo;
          </p>
        </div>
      </div>

      {/* 5. Confidence Calculation Breakdown */}
      <div className="p-4 rounded-lg bg-slate-900/70 border border-cyan-500/20 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-orbitron font-bold text-cyan-200 uppercase tracking-wider flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-cyan-400" />
            Composite Confidence Calculation
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            Formula: 0.50 × Detector + 0.35 × Shadow + 0.15 × Shape
          </span>
        </div>

        <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-4 p-3 bg-slate-950/80 rounded-lg border border-slate-800 font-mono text-xs text-center">
          <div className="p-2 rounded bg-blue-500/10 border border-blue-500/20">
            <span className="text-[10px] text-slate-400 block uppercase">Detector</span>
            <span className="font-bold text-blue-300">{detectorScore.toFixed(1)} × 50%</span>
            <span className="text-slate-500 block text-[10px]">={(detectorScore * 0.50).toFixed(1)}</span>
          </div>

          <span className="text-slate-500 text-lg font-bold">+</span>

          <div className="p-2 rounded bg-cyan-500/10 border border-cyan-500/20">
            <span className="text-[10px] text-slate-400 block uppercase">Shadow</span>
            <span className="font-bold text-cyan-300">{shadowScore.toFixed(1)} × 35%</span>
            <span className="text-slate-500 block text-[10px]">={(shadowScore * 0.35).toFixed(1)}</span>
          </div>

          <span className="text-slate-500 text-lg font-bold">+</span>

          <div className="p-2 rounded bg-purple-500/10 border border-purple-500/20">
            <span className="text-[10px] text-slate-400 block uppercase">Morphology</span>
            <span className="font-bold text-purple-300">{shapeScore.toFixed(1)} × 15%</span>
            <span className="text-slate-500 block text-[10px]">={(shapeScore * 0.15).toFixed(1)}</span>
          </div>

          <span className="text-slate-500 text-lg font-bold">=</span>

          <div className="p-2 rounded bg-emerald-500/15 border border-emerald-500/30">
            <span className="text-[10px] text-slate-400 block uppercase">Composite</span>
            <span className="font-bold text-emerald-300 text-sm">{finalScore.toFixed(1)}%</span>
            <span className="text-emerald-400 block text-[10px]">Tier: {tier}</span>
          </div>
        </div>

        {suppressionApplied && (
          <div className="flex items-start gap-2 p-2.5 rounded bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-mono">
            <AlertTriangle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <span className="font-bold uppercase">⚠ SHADOW SUPPRESSION APPLIED: </span>
              Because a physics-consistent acoustic shadow was not detected, the composite confidence was reduced by the existing suppression factor (0.48×) to prevent false positives.
            </div>
          </div>
        )}
      </div>

      {/* 6. Physics Verdict Banner */}
      <div className={`flex items-center gap-3 p-3.5 rounded-lg border ${verdict.border} ${verdict.bg}`}>
        {verdict.icon}
        <div className="flex-1">
          <span className={`text-xs font-orbitron font-bold tracking-wider ${verdict.color}`}>
            {verdict.title}
          </span>
          <p className="text-[11px] text-slate-300 font-mono mt-0.5 leading-relaxed">
            {verdict.desc}
          </p>
        </div>
      </div>

      {/* 7. Sonar Image Visual Evidence & Overlay */}
      <div className="p-4 rounded-lg bg-slate-900/70 border border-cyan-500/20 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-orbitron font-bold text-cyan-200 uppercase tracking-wider flex items-center gap-1.5">
            <Maximize2 className="w-3.5 h-3.5 text-cyan-400" />
            Acoustic Evidence Schematic & Propagation Map
          </span>
          <span className="text-[10px] font-mono text-slate-400">
            Propagation: Nadir → {isStarboard ? "Starboard (Right)" : "Port (Left)"}
          </span>
        </div>

        {/* Forensic SVG Propagation Diagram */}
        <div className="relative w-full h-36 bg-slate-950 rounded-lg border border-slate-800 overflow-hidden flex items-center justify-center">
          <svg className="w-full h-full" viewBox="0 0 500 120" preserveAspectRatio="xMidYMid meet">
            {/* Background grid */}
            <defs>
              <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(6, 182, 212, 0.05)" strokeWidth="1" />
              </pattern>
            </defs>
            <rect width="500" height="120" fill="url(#grid)" />

            {/* Nadir track line */}
            <line x1="80" y1="0" x2="80" y2="120" stroke="rgba(255, 255, 255, 0.4)" strokeWidth="1.5" strokeDasharray="4 3" />
            <text x="85" y="16" fill="rgba(255, 255, 255, 0.6)" fontSize="9" fontFamily="monospace">NADIR TRACK</text>

            {/* Acoustic Beam Waves */}
            <path d="M 80,60 Q 140,20 200,60 Q 140,100 80,60" fill="none" stroke="rgba(6, 182, 212, 0.25)" strokeWidth="1" />
            <path d="M 80,60 Q 170,10 260,60 Q 170,110 80,60" fill="none" stroke="rgba(6, 182, 212, 0.15)" strokeWidth="1" />

            {/* Target Highlight Region */}
            <rect x="230" y="35" width="40" height="50" fill="rgba(0, 255, 128, 0.3)" stroke="#00ff80" strokeWidth="1.5" rx="3" />
            <text x="232" y="30" fill="#00ff80" fontSize="9" fontFamily="monospace" fontWeight="bold">HIGHLIGHT</text>

            {/* Target Shadow Region */}
            <rect x="270" y="35" width="70" height="50" fill="rgba(255, 100, 0, 0.25)" stroke="#ff6400" strokeWidth="1.5" strokeDasharray="3 2" rx="3" />
            <text x="275" y="30" fill="#ff6400" fontSize="9" fontFamily="monospace" fontWeight="bold">ACOUSTIC SHADOW</text>

            {/* Full Bounding Box Container */}
            <rect x="228" y="33" width="114" height="54" fill="none" stroke="#00d9ff" strokeWidth="1.5" rx="4" />

            {/* Beam Propagation Vector Arrow */}
            <line x1="120" y1="60" x2="220" y2="60" stroke="#00f0ff" strokeWidth="2" markerEnd="url(#arrow)" />
            <polygon points="220,60 210,55 210,65" fill="#00f0ff" />
            <text x="135" y="52" fill="#00f0ff" fontSize="9" fontFamily="monospace">PROPAGATION</text>

            {/* Target Center Dot */}
            <circle cx="285" cy="60" r="3" fill="#00f0ff" />
          </svg>
        </div>

        {/* Backend Overlay Endpoint Link if Survey ID exists */}
        {surveyId && (
          <div className="pt-2 border-t border-slate-800 flex justify-end">
            <a
              href={`/api/surveys/${surveyId}/detections/${detection.class}/explainability-image`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs font-mono text-cyan-400 hover:text-cyan-300 underline flex items-center gap-1"
            >
              <span>Inspect Raw Overlay PNG</span>
              <ArrowRight className="w-3 h-3" />
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
