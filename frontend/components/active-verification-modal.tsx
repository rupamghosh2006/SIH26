"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  ShieldAlert,
  Compass,
  Layers,
  Sparkles,
  Upload,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  RotateCw,
  Eye,
  Crosshair,
  ArrowRight,
  TrendingUp,
  TrendingDown,
  Info,
  X,
  FileCheck2,
  Activity,
  Sliders,
  Maximize2
} from "lucide-react";

interface ActiveVerificationModalProps {
  isOpen: boolean;
  onClose: () => void;
  detection: any;
  detectionIndex: number;
  originalImage?: string;
  onConfirmVerification?: (status: "confirmed" | "rejected" | "review", verificationData: any) => void;
}

export function ActiveVerificationModal({
  isOpen,
  onClose,
  detection,
  detectionIndex,
  originalImage,
  onConfirmVerification
}: ActiveVerificationModalProps) {
  const [loadingPlan, setLoadingPlan] = useState<boolean>(true);
  const [plan, setPlan] = useState<any>(null);
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [processingStatus, setProcessingStatus] = useState<string>("");
  const [verificationResult, setVerificationResult] = useState<any>(null);
  const [secondaryImage, setSecondaryImage] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<"confirm" | "reject">("confirm");
  const [activeTab, setActiveTab] = useState<"overview" | "evidence" | "radar">("overview");
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen && detection) {
      fetchVerificationPlan();
    }
  }, [isOpen, detection]);

  const fetchVerificationPlan = async () => {
    setLoadingPlan(true);
    setVerificationResult(detection.verification_record || null);
    if (detection.verification_record?.secondary_image_url) {
      setSecondaryImage(detection.verification_record.secondary_image_url);
    }
    try {
      const formData = new FormData();
      formData.append("action", "plan");
      formData.append("detection", JSON.stringify(detection));

      const res = await fetch("/api/detection/verify", {
        method: "POST",
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        if (data.success && data.plan) {
          setPlan(data.plan);
        }
      }
    } catch (err) {
      console.error("Failed fetching verification plan:", err);
    } finally {
      setLoadingPlan(false);
    }
  };

  const handleSimulateRescan = async (scenarioType: "confirm" | "reject") => {
    setSelectedScenario(scenarioType);
    setIsProcessing(true);
    setProcessingStatus(
      scenarioType === "confirm"
        ? "Simulating orthogonal secondary sonar swath (Angle: +45°)..."
        : "Simulating cross-track verification swath (Angle: -45°)..."
    );

    try {
      // Step 1: Simulated telemetry acquisition delay
      await new Promise((resolve) => setTimeout(resolve, 800));
      setProcessingStatus("Extracting acoustic highlight & shadow ROI matrices...");

      await new Promise((resolve) => setTimeout(resolve, 600));
      setProcessingStatus("Executing YOLOv8 inference & physics confidence validation...");

      const formData = new FormData();
      formData.append("action", "rescan");
      formData.append("scenario", scenarioType);
      formData.append("detection", JSON.stringify(detection));

      const res = await fetch("/api/detection/verify", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        throw new Error("Rescan request failed");
      }

      const data = await res.json();
      if (data.success && data.comparison) {
        setVerificationResult(data.comparison);
        setSecondaryImage(data.secondary_image);
        setActiveTab("evidence");
      }
    } catch (err) {
      console.error("Simulation error:", err);
    } finally {
      setIsProcessing(false);
      setProcessingStatus("");
    }
  };

  const handleUploadRescan = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    setProcessingStatus(`Ingesting verification sonar scan '${file.name}'...`);

    try {
      const formData = new FormData();
      formData.append("action", "rescan");
      formData.append("file", file);
      formData.append("detection", JSON.stringify(detection));

      const res = await fetch("/api/detection/verify", {
        method: "POST",
        body: formData
      });

      if (!res.ok) {
        throw new Error("Uploaded rescan failed");
      }

      const data = await res.json();
      if (data.success && data.comparison) {
        setVerificationResult(data.comparison);
        setSecondaryImage(data.secondary_image);
        setActiveTab("evidence");
      }
    } catch (err) {
      console.error("Upload error:", err);
    } finally {
      setIsProcessing(false);
      setProcessingStatus("");
    }
  };

  const handleOperatorAction = (status: "confirmed" | "rejected" | "review") => {
    if (onConfirmVerification) {
      onConfirmVerification(status, verificationResult);
    }
    onClose();
  };

  if (!isOpen || !detection) return null;

  const confPct = Math.round(detection.confidence * 100);
  const tier = detection.confidence_tier || (confPct >= 75 ? "High" : confPct >= 45 ? "Medium" : "Low");
  const targetName = (detection.class || "Debris Target").replace(/_/g, " ").toUpperCase();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/85 backdrop-blur-md overflow-y-auto animate-in fade-in duration-200">
      <div className="relative w-full max-w-5xl bg-slate-900 border-2 border-cyan-500/40 rounded-2xl shadow-2xl shadow-cyan-950/80 overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Header Bar */}
        <div className="flex items-center justify-between px-6 py-4 bg-slate-950 border-b border-cyan-500/30 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
              <Crosshair className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base sm:text-lg font-black font-orbitron text-cyan-300 tracking-wider">
                  ACTIVE VERIFICATION CONSOLE
                </h3>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                  SIMULATION MODE
                </span>
              </div>
              <p className="text-xs text-slate-400 font-space-mono">
                Target #{detectionIndex + 1}: <span className="text-white font-bold">{targetName}</span> • Initial Confidence: <span className="text-cyan-300 font-bold">{confPct}%</span> [{tier.toUpperCase()}]
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Prototype Disclaimer Banner */}
        <div className="bg-gradient-to-r from-blue-950/90 via-slate-900 to-cyan-950/90 px-6 py-2 border-b border-cyan-500/20 flex items-center justify-between text-xs text-slate-300 font-space-mono">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <span>
              <strong>VIRTUAL RESCAN ACTIVE:</strong> Secondary sonar pass simulated using verification imagery. Software architecture is telemetry-ready for autonomous AUV integration.
            </span>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-800 bg-slate-950/50 px-6 pt-2 gap-2 text-xs font-space-mono flex-shrink-0">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2 rounded-t-lg font-bold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === "overview"
                ? "bg-slate-900 border-t-2 border-x border-cyan-400 text-cyan-300"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            <span>1. Verification Need & Geometry</span>
          </button>
          <button
            onClick={() => setActiveTab("radar")}
            className={`px-4 py-2 rounded-t-lg font-bold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === "radar"
                ? "bg-slate-900 border-t-2 border-x border-cyan-400 text-cyan-300"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>2. Tactical Swath Path</span>
          </button>
          <button
            onClick={() => setActiveTab("evidence")}
            className={`px-4 py-2 rounded-t-lg font-bold transition-all cursor-pointer flex items-center gap-2 ${
              activeTab === "evidence"
                ? "bg-slate-900 border-t-2 border-x border-cyan-400 text-cyan-300"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Activity className="w-3.5 h-3.5" />
            <span>3. Multi-Pass Evidence Analysis {verificationResult && "✓"}</span>
          </button>
        </div>

        {/* Scrollable Content Body */}
        <div className="p-6 space-y-6 overflow-y-auto flex-1">
          
          {/* TAB 1: OVERVIEW & RESCAN PLANNING */}
          {activeTab === "overview" && (
            <div className="space-y-6 animate-in fade-in duration-150">
              
              {/* Uncertainty Reason Box */}
              <div className="p-4 rounded-xl border border-amber-500/30 bg-amber-500/10 space-y-2">
                <div className="flex items-center gap-2 text-amber-300 font-bold font-orbitron text-sm">
                  <AlertTriangle className="w-4 h-4" />
                  <span>REASON FOR ACTIVE VERIFICATION</span>
                </div>
                <ul className="list-disc list-inside space-y-1 text-xs text-slate-300 font-space-mono">
                  {plan?.verification_need?.reasons?.map((reason: string, idx: number) => (
                    <li key={idx}>{reason}</li>
                  )) || (
                    <>
                      <li>Initial confidence ({confPct}%) falls in {tier.toUpperCase()} uncertainty bracket.</li>
                      <li>Partial acoustic shadow formation requires orthogonal observation angle.</li>
                      <li>Adaptive cross-track observation recommended before final operator confirmation.</li>
                    </>
                  )}
                </ul>
              </div>

              {/* Recommended Observation Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-space-mono">
                <div className="p-4 rounded-xl bg-slate-950 border border-cyan-500/20 space-y-1">
                  <p className="text-[11px] text-slate-400 uppercase">Suggested Offset</p>
                  <p className="text-xl font-bold text-cyan-300 font-orbitron">
                    {plan?.recommended_observation?.suggested_offset_meters || 18.5} m
                  </p>
                  <p className="text-[10px] text-slate-500">Cross-track CPA separation</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-cyan-500/20 space-y-1">
                  <p className="text-[11px] text-slate-400 uppercase">Suggested Angle</p>
                  <p className="text-xl font-bold text-cyan-300 font-orbitron">
                    {plan?.recommended_observation?.suggested_angle_degrees > 0 ? "+" : ""}
                    {plan?.recommended_observation?.suggested_angle_degrees || 45.0}°
                  </p>
                  <p className="text-[10px] text-slate-500">Orthogonal shadow illumination</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-cyan-500/20 space-y-1">
                  <p className="text-[11px] text-slate-400 uppercase">Observation Mode</p>
                  <p className="text-base font-bold text-cyan-300 font-orbitron">
                    {plan?.recommended_observation?.observation_mode || "Orthogonal Swath"}
                  </p>
                  <p className="text-[10px] text-slate-500">Altitude: 8.0m | 900 kHz CHIRP</p>
                </div>
              </div>

              {/* Action Trigger Box */}
              <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-950 via-slate-900 to-cyan-950/40 border-2 border-cyan-500/30 space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h4 className="text-sm font-bold text-cyan-200 font-orbitron">
                      EXECUTE VIRTUAL SECONDARY RESCAN
                    </h4>
                    <p className="text-xs text-slate-400 font-space-mono">
                      Simulate or upload an independent secondary sonar observation to test evidence consistency.
                    </p>
                  </div>
                  <span className="text-[11px] font-mono text-cyan-400">
                    Dual Verification Scenarios Ready
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  {/* Scenario A: Confirm */}
                  <button
                    onClick={() => handleSimulateRescan("confirm")}
                    disabled={isProcessing}
                    className="p-4 rounded-xl bg-gradient-to-r from-emerald-600/30 to-cyan-600/30 border border-emerald-500/50 hover:border-emerald-400 text-emerald-300 hover:text-white font-orbitron text-xs font-bold transition-all flex flex-col items-center justify-center gap-2 cursor-pointer shadow-lg shadow-emerald-950/40 group"
                  >
                    <Sparkles className="w-5 h-5 text-emerald-400 group-hover:scale-110 transition-transform" />
                    <span className="text-center">SCENARIO A:<br />CONFIRMATION PASS</span>
                    <span className="text-[10px] font-space-mono text-emerald-400/80 font-normal">
                      High shadow contrast (+45°)
                    </span>
                  </button>

                  {/* Scenario B: Reject */}
                  <button
                    onClick={() => handleSimulateRescan("reject")}
                    disabled={isProcessing}
                    className="p-4 rounded-xl bg-gradient-to-r from-amber-600/30 to-red-600/30 border border-amber-500/50 hover:border-amber-400 text-amber-300 hover:text-white font-orbitron text-xs font-bold transition-all flex flex-col items-center justify-center gap-2 cursor-pointer shadow-lg shadow-amber-950/40 group"
                  >
                    <AlertTriangle className="w-5 h-5 text-amber-400 group-hover:scale-110 transition-transform" />
                    <span className="text-center">SCENARIO B:<br />FALSE ALARM PASS</span>
                    <span className="text-[10px] font-space-mono text-amber-400/80 font-normal">
                      Flat ripple / no relief
                    </span>
                  </button>

                  {/* Upload Custom */}
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isProcessing}
                    className="p-4 rounded-xl bg-slate-950 border border-cyan-500/40 hover:border-cyan-400 text-cyan-300 hover:text-white font-orbitron text-xs font-bold transition-all flex flex-col items-center justify-center gap-2 cursor-pointer shadow-lg shadow-cyan-950/40 group"
                  >
                    <Upload className="w-5 h-5 text-cyan-400 group-hover:scale-110 transition-transform" />
                    <span className="text-center">UPLOAD SCAN:<br />CUSTOM SONAR ROI</span>
                    <span className="text-[10px] font-space-mono text-slate-400 font-normal">
                      PNG / JPG Secondary Scan
                    </span>
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleUploadRescan}
                    className="hidden"
                  />
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: TACTICAL SWATH MAP VISUALIZATION */}
          {activeTab === "radar" && (
            <div className="space-y-4 animate-in fade-in duration-150">
              <div className="p-4 rounded-2xl bg-slate-950 border border-cyan-500/30 space-y-3">
                <div className="flex items-center justify-between text-xs font-space-mono">
                  <span className="text-cyan-300 font-bold flex items-center gap-2">
                    <Compass className="w-4 h-4 text-cyan-400" />
                    SECONDARY ADAPTIVE SWATH TRAJECTORY
                  </span>
                  <span className="text-slate-400">
                    Target: [{detection.latitude?.toFixed(4) || "12.9234"}°N, {detection.longitude?.toFixed(4) || "80.1345"}°E]
                  </span>
                </div>

                {/* SVG Tactical Radar & Route Map */}
                <div className="relative w-full h-[320px] rounded-xl bg-slate-950 border border-cyan-500/20 overflow-hidden flex items-center justify-center">
                  <svg className="w-full h-full" viewBox="0 0 600 320">
                    <defs>
                      <radialGradient id="radarGrid" cx="50%" cy="50%" r="50%">
                        <stop offset="0%" stopColor="#083344" stopOpacity="0.4" />
                        <stop offset="100%" stopColor="#020617" stopOpacity="0.9" />
                      </radialGradient>
                      <linearGradient id="primaryBeam" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.2" />
                        <stop offset="50%" stopColor="#38bdf8" stopOpacity="0.8" />
                        <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.2" />
                      </linearGradient>
                      <linearGradient id="rescanBeam" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.3" />
                        <stop offset="50%" stopColor="#f59e0b" stopOpacity="0.9" />
                        <stop offset="100%" stopColor="#10b981" stopOpacity="0.9" />
                      </linearGradient>
                    </defs>

                    {/* Radar Range Rings */}
                    <rect width="600" height="320" fill="url(#radarGrid)" />
                    <circle cx="300" cy="160" r="140" fill="none" stroke="#0e7490" strokeWidth="1" strokeDasharray="3 3" opacity="0.4" />
                    <circle cx="300" cy="160" r="90" fill="none" stroke="#0e7490" strokeWidth="1" strokeDasharray="3 3" opacity="0.5" />
                    <circle cx="300" cy="160" r="40" fill="none" stroke="#0e7490" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
                    
                    {/* Crosshairs */}
                    <line x1="0" y1="160" x2="600" y2="160" stroke="#083344" strokeWidth="1" />
                    <line x1="300" y1="0" x2="300" y2="320" stroke="#083344" strokeWidth="1" />

                    {/* PRIMARY SURVEY TRACK (Horizontal) */}
                    <path
                      d="M 60 160 L 260 160 L 540 160"
                      fill="none"
                      stroke="#0284c7"
                      strokeWidth="3"
                      strokeDasharray="6 4"
                    />
                    <text x="70" y="148" fill="#38bdf8" fontSize="10" fontFamily="monospace">PRIMARY SURVEY TRACKLINE (090° E)</text>
                    
                    {/* Primary Waypoint Nodes */}
                    <circle cx="80" cy="160" r="4" fill="#38bdf8" />
                    <circle cx="520" cy="160" r="4" fill="#38bdf8" />

                    {/* TARGET ANOMALY POSITION */}
                    <circle cx="300" cy="130" r="14" fill="#ef4444" fillOpacity="0.25" className="animate-ping" />
                    <circle cx="300" cy="130" r="6" fill="#ef4444" stroke="#ffffff" strokeWidth="1.5" />
                    <text x="315" y="134" fill="#f87171" fontSize="11" fontWeight="bold" fontFamily="monospace">
                      TARGET ANOMALY #{detectionIndex + 1}
                    </text>

                    {/* SECONDARY VERIFICATION SWATH (45° Orthogonal Approach) */}
                    <path
                      d="M 120 270 L 300 190 L 480 60"
                      fill="none"
                      stroke="url(#rescanBeam)"
                      strokeWidth="3"
                    />
                    <polygon points="480,60 460,65 472,78" fill="#10b981" />
                    
                    {/* Rescan Waypoints */}
                    <circle cx="120" cy="270" r="5" fill="#f59e0b" stroke="#ffffff" strokeWidth="1" />
                    <text x="130" y="285" fill="#fbbf24" fontSize="10" fontFamily="monospace">WP-1: Rescan Entry</text>

                    <circle cx="300" cy="190" r="6" fill="#10b981" stroke="#ffffff" strokeWidth="1.5" />
                    <text x="312" y="200" fill="#34d399" fontSize="10" fontWeight="bold" fontFamily="monospace">
                      WP-2: Optimal CPA (+{plan?.recommended_observation?.suggested_offset_meters || 18.5}m)
                    </text>

                    <circle cx="480" cy="60" r="5" fill="#10b981" stroke="#ffffff" strokeWidth="1" />
                    <text x="440" y="45" fill="#34d399" fontSize="10" fontFamily="monospace">WP-3: Rescan Exit</text>
                  </svg>

                  {/* Legend Overlay */}
                  <div className="absolute bottom-3 left-3 bg-slate-900/90 border border-slate-800 rounded-lg p-2 flex items-center gap-4 text-[10px] font-space-mono">
                    <div className="flex items-center gap-1.5">
                      <div className="w-3 h-1 bg-cyan-400 rounded" />
                      <span className="text-slate-300">Primary Track</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-3 h-1 bg-emerald-400 rounded" />
                      <span className="text-slate-300">Verification Swath (45°)</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
                      <span className="text-slate-300">Target</span>
                    </div>
                  </div>
                </div>

                {/* Waypoint Coordinates Table */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] font-space-mono text-slate-300">
                  {plan?.geospatial_routes?.verification_survey?.map((wp: any, i: number) => (
                    <div key={i} className="p-2 rounded-lg bg-slate-900 border border-slate-800 flex justify-between">
                      <span className="text-cyan-400 font-bold">{wp.name}</span>
                      <span>{wp.lat?.toFixed(5)}°N, {wp.lon?.toFixed(5)}°E</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: MULTI-PASS EVIDENCE COMPARISON */}
          {activeTab === "evidence" && (
            <div className="space-y-6 animate-in fade-in duration-150">
              
              {/* Verdict Header Banner */}
              {verificationResult ? (
                <div className={`p-5 rounded-2xl border-2 ${verificationResult.verdict_color} space-y-2`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {verificationResult.status === "VERIFIED" ? (
                        <CheckCircle2 className="w-6 h-6 text-emerald-400 flex-shrink-0" />
                      ) : (
                        <AlertTriangle className="w-6 h-6 text-amber-400 flex-shrink-0" />
                      )}
                      <h4 className="text-lg font-black font-orbitron tracking-wider">
                        {verificationResult.verdict_title}
                      </h4>
                    </div>
                    <span className="text-xs font-mono font-bold px-3 py-1 rounded-full bg-slate-950/80 border border-current">
                      {verificationResult.verdict_badge}
                    </span>
                  </div>
                  <p className="text-xs text-slate-200 font-space-mono leading-relaxed">
                    {verificationResult.summary_text}
                  </p>
                </div>
              ) : (
                <div className="p-8 rounded-2xl bg-slate-950 border border-dashed border-slate-700 text-center space-y-3">
                  <Activity className="w-8 h-8 text-cyan-400 mx-auto animate-pulse" />
                  <p className="text-sm font-orbitron text-cyan-200">NO SECONDARY OBSERVATION RECORDED YET</p>
                  <p className="text-xs text-slate-400 font-space-mono max-w-md mx-auto">
                    Click "Scenario A" or "Scenario B" in the Overview tab to simulate a secondary sonar pass and view live multi-angle evidence breakdown.
                  </p>
                  <button
                    onClick={() => handleSimulateRescan("confirm")}
                    className="px-4 py-2 rounded-xl bg-cyan-500 text-slate-950 font-bold text-xs font-orbitron cursor-pointer hover:bg-cyan-400 transition-colors"
                  >
                    Run Confirmation Rescan Now
                  </button>
                </div>
              )}

              {/* Side-by-Side Sonar Imagery */}
              {verificationResult && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Primary Observation Card */}
                  <div className="p-4 rounded-xl bg-slate-950 border border-cyan-500/30 space-y-3">
                    <div className="flex items-center justify-between text-xs font-space-mono">
                      <span className="text-cyan-300 font-bold">1. PRIMARY OBSERVATION (090°)</span>
                      <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-mono">
                        Conf: {verificationResult.primary?.confidence || confPct}%
                      </span>
                    </div>
                    <div className="relative rounded-lg overflow-hidden bg-black/40 border border-slate-800 flex items-center justify-center max-h-[220px]">
                      <img
                        src={originalImage || "/placeholder.svg"}
                        alt="Primary Sonar"
                        className="w-full h-full object-contain max-h-[220px]"
                      />
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-center text-xs font-space-mono pt-1">
                      <div className="p-2 rounded bg-slate-900 border border-slate-800">
                        <p className="text-[10px] text-slate-400">YOLO Det</p>
                        <p className="font-bold text-cyan-300">{verificationResult.primary?.detector_score || confPct}%</p>
                      </div>
                      <div className="p-2 rounded bg-slate-900 border border-slate-800">
                        <p className="text-[10px] text-slate-400">Shadow</p>
                        <p className="font-bold text-amber-300">{verificationResult.primary?.shadow_score || 52}%</p>
                      </div>
                      <div className="p-2 rounded bg-slate-900 border border-slate-800">
                        <p className="text-[10px] text-slate-400">Shape</p>
                        <p className="font-bold text-slate-200">{verificationResult.primary?.shape_score || 68}%</p>
                      </div>
                    </div>
                  </div>

                  {/* Secondary Observation Card */}
                  <div className="p-4 rounded-xl bg-slate-950 border border-emerald-500/30 space-y-3">
                    <div className="flex items-center justify-between text-xs font-space-mono">
                      <span className="text-emerald-300 font-bold">2. SECONDARY RESCAN (+45°)</span>
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono">
                        Conf: {verificationResult.secondary?.confidence || 0}%
                      </span>
                    </div>
                    <div className="relative rounded-lg overflow-hidden bg-black/40 border border-slate-800 flex items-center justify-center max-h-[220px]">
                      {secondaryImage ? (
                        <img
                          src={secondaryImage}
                          alt="Secondary Sonar"
                          className="w-full h-full object-contain max-h-[220px]"
                        />
                      ) : (
                        <div className="p-12 text-slate-500 text-xs font-space-mono">No secondary imagery</div>
                      )}
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-center text-xs font-space-mono pt-1">
                      <div className="p-2 rounded bg-slate-900 border border-slate-800">
                        <p className="text-[10px] text-slate-400">YOLO Det</p>
                        <p className="font-bold text-emerald-300">{verificationResult.secondary?.detector_score || 0}%</p>
                      </div>
                      <div className="p-2 rounded bg-slate-900 border border-slate-800">
                        <p className="text-[10px] text-slate-400">Shadow</p>
                        <p className="font-bold text-emerald-300">{verificationResult.secondary?.shadow_score || 0}%</p>
                      </div>
                      <div className="p-2 rounded bg-slate-900 border border-slate-800">
                        <p className="text-[10px] text-slate-400">Shape</p>
                        <p className="font-bold text-slate-200">{verificationResult.secondary?.shape_score || 0}%</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Multi-Angle Evidence Delta Matrix */}
              {verificationResult && (
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                  <h5 className="text-xs font-bold text-cyan-300 font-orbitron uppercase">
                    EVIDENCE COMPARISON METRICS
                  </h5>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-space-mono">
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                      <p className="text-[10px] text-slate-400">Confidence Delta</p>
                      <div className="flex items-center gap-1">
                        {verificationResult.confidence_delta >= 0 ? (
                          <TrendingUp className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <TrendingDown className="w-4 h-4 text-red-400" />
                        )}
                        <span className={`text-base font-bold ${verificationResult.confidence_delta >= 0 ? 'text-emerald-300' : 'text-red-300'}`}>
                          {verificationResult.confidence_delta > 0 ? "+" : ""}
                          {verificationResult.confidence_delta}%
                        </span>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                      <p className="text-[10px] text-slate-400">Shadow Relief Delta</p>
                      <div className="flex items-center gap-1">
                        {verificationResult.shadow_delta >= 0 ? (
                          <TrendingUp className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <TrendingDown className="w-4 h-4 text-amber-400" />
                        )}
                        <span className={`text-base font-bold ${verificationResult.shadow_delta >= 0 ? 'text-emerald-300' : 'text-amber-300'}`}>
                          {verificationResult.shadow_delta > 0 ? "+" : ""}
                          {verificationResult.shadow_delta}%
                        </span>
                      </div>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                      <p className="text-[10px] text-slate-400">Class Agreement</p>
                      <span className={`text-sm font-bold ${verificationResult.class_consistent ? 'text-emerald-300' : 'text-amber-300'}`}>
                        {verificationResult.class_consistent ? "✓ 100% MATCH" : "⚠ DISCREPANCY"}
                      </span>
                    </div>

                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 space-y-1">
                      <p className="text-[10px] text-slate-400">Target Association</p>
                      <span className="text-sm font-bold text-cyan-300">
                        {verificationResult.target_associated ? `${verificationResult.match_score}% Spatial IoU` : "No Match"}
                      </span>
                    </div>
                  </div>

                  {/* Scientific Notes */}
                  {verificationResult.scientific_notes && (
                    <div className="pt-2 border-t border-slate-900 text-[11px] font-space-mono text-slate-400 space-y-1">
                      <p className="text-slate-300 font-bold">Forensic Acoustic Notes:</p>
                      {verificationResult.scientific_notes.map((note: string, idx: number) => (
                        <p key={idx}>• {note}</p>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Processing Loading Overlay */}
          {isProcessing && (
            <div className="p-8 rounded-2xl bg-cyan-950/40 border border-cyan-500/50 flex flex-col items-center justify-center gap-3 text-center animate-pulse">
              <RotateCw className="w-8 h-8 text-cyan-400 animate-spin" />
              <p className="text-sm font-orbitron font-bold text-cyan-200">
                VERIFYING SECONDARY OBSERVATION...
              </p>
              <p className="text-xs font-space-mono text-cyan-300/80">
                {processingStatus}
              </p>
            </div>
          )}
        </div>

        {/* Footer Actions (Human-in-the-loop Final Decision) */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-6 py-4 bg-slate-950 border-t border-slate-800 flex-shrink-0">
          <div className="text-xs font-space-mono text-slate-400">
            {verificationResult ? (
              <span>Recommended Action: <strong className="text-cyan-300">{verificationResult.recommended_action}</strong></span>
            ) : (
              <span>Select simulation mode or upload scan to compute verification evidence.</span>
            )}
          </div>

          <div className="flex items-center gap-2 self-end sm:self-center">
            <button
              onClick={() => handleOperatorAction("confirmed")}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-orbitron font-bold flex items-center gap-1.5 transition-colors cursor-pointer shadow-lg shadow-emerald-950/60"
            >
              <CheckCircle2 className="w-4 h-4" />
              <span>Confirm Detection</span>
            </button>
            <button
              onClick={() => handleOperatorAction("rejected")}
              className="px-4 py-2 rounded-xl bg-red-600/80 hover:bg-red-500 text-white text-xs font-orbitron font-bold flex items-center gap-1.5 transition-colors cursor-pointer shadow-lg shadow-red-950/60"
            >
              <XCircle className="w-4 h-4" />
              <span>False Alarm</span>
            </button>
            <button
              onClick={() => handleOperatorAction("review")}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-orbitron font-bold flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Mark For ROV Review</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
