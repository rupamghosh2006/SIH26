"use client";

import type React from "react";
import { useState, useRef } from "react";
import dynamic from "next/dynamic";
import {
  Upload,
  Play,
  Loader2,
  Zap,
  Eye,
  BarChart3,
  Settings,
  ImageIcon,
  Video,
  Map,
  AlertTriangle,
  Info,
  X,
} from "lucide-react";
import HolographicCard from "./holographic-card";
import RealTimeFeed from "./real-time-feed";
import TacticalStat from "./tactical-stat";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  addDetection,
  loadDetections,
  normalizeOverallThreatScore,
} from "@/lib/detection-storage";

// Dynamic import for Leaflet map to avoid SSR issues
const AdvancedLeafletMap = dynamic(() => import("./advanced-leaflet-map"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-[380px] bg-slate-950 flex items-center justify-center border-2 border-cyan-500/30 rounded-2xl">
      <div className="text-cyan-400 font-space-mono text-xs animate-pulse flex items-center gap-2">
        <div className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
        Initializing Hydrographic Map...
      </div>
    </div>
  ),
});

interface Detection {
  id?: string | number;
  class: string;
  confidence: number;
  confidence_score?: number;
  confidence_tier?: string;
  threat_level?: string;
  bbox: [number, number, number, number];
  color: string;
  physical_size_m?: string;
  estimated_size_m?: string;
  entangled_area_m2?: number;
  polygon?: number[][];
  seabed_facies?: string;
  srr_corrected?: boolean;
  latitude?: number;
  longitude?: number;
  depth_m?: number;
  acoustic_shadow_verified?: boolean;
  filter_details?: any;
}

interface DetectionResult {
  surveyId?: string;
  originalImage: string;
  detectedImage: string;
  originalFileName?: string;
  detections: Detection[];
  processingTime: number;
  totalObjects: number;
  overallThreatLevel?: string;
  overallThreatScore?: number;
  threatCount?: number;
  timestamp?: Date;
  seafloorFacies?: string;
  srrApplied?: boolean;
}

export const DEMO_SAMPLES = [
  {
    filename: "ghost_net_sample_sss_01.jpg",
    label: "Ghost Net #1",
    category: "Net / ALDFG",
    badge: "98% Conf",
    lat: "16.3520",
    lng: "84.5240",
  },
  {
    filename: "ghost_net_sample_sss_02.jpg",
    label: "Ghost Net #2",
    category: "Net / ALDFG",
    badge: "84% Conf",
    lat: "16.3650",
    lng: "84.5355",
  },
  {
    filename: "shipwreck_sample_sss_01.jpg",
    label: "Shipwreck #1",
    category: "Shipwreck Hull",
    badge: "91% Conf",
    lat: "16.3311",
    lng: "84.5082",
  },
  {
    filename: "shipwreck_sample_sss_02.jpg",
    label: "Shipwreck #2",
    category: "Shipwreck Keel",
    badge: "79% Conf",
    lat: "16.3250",
    lng: "84.4990",
  },
  {
    filename: "pipe_cylinder_sample_sss_01.jpg",
    label: "Pipeline #1",
    category: "Subsea Pipe",
    badge: "73% Conf",
    lat: "16.3850",
    lng: "84.5520",
  },
  {
    filename: "pipe_cylinder_sample_sss_02.jpg",
    label: "Pipeline #2",
    category: "Subsea Pipe",
    badge: "70% Conf",
    lat: "16.3910",
    lng: "84.5610",
  },
  {
    filename: "multi_debris_field_sample_01.jpg",
    label: "Multi-Debris",
    category: "Debris Field",
    badge: "Multi-Target",
    lat: "16.3580",
    lng: "84.5410",
  },
];

interface DetectionViewProps {
  onResultsUpdate?: (results: DetectionResult[]) => void;
}

export default function DetectionView({ onResultsUpdate }: DetectionViewProps) {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [results, setResults] = useState<DetectionResult[]>(() => {
    if (typeof window === "undefined") return [];
    const stored = loadDetections();
    return stored.map((s) => ({
      surveyId: s.surveyId,
      originalImage: s.originalImage,
      detectedImage: s.detectedImage,
      originalFileName: s.originalFileName,
      detections: s.detections,
      processingTime: s.processingTime,
      totalObjects: s.totalObjects,
      overallThreatLevel: s.overallThreatLevel,
      overallThreatScore: normalizeOverallThreatScore(s.overallThreatScore),
      threatCount: s.threatCount,
      timestamp: new Date(s.timestamp),
      seafloorFacies: s.seafloorFacies,
      srrApplied: s.srrApplied,
    }));
  });
  const [activeTab, setActiveTab] = useState("image");
  const [latitude, setLatitude] = useState<string>("");
  const [longitude, setLongitude] = useState<string>("");
  const [backendNotice, setBackendNotice] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSelectSample = async (sample: typeof DEMO_SAMPLES[0]) => {
    try {
      const response = await fetch(`/sample-sonar/${sample.filename}`);
      if (!response.ok) throw new Error("Failed to load sample image");
      const blob = await response.blob();
      const file = new File([blob], sample.filename, { type: "image/jpeg" });
      setSelectedFile(file);
      if (sample.lat) setLatitude(sample.lat);
      if (sample.lng) setLongitude(sample.lng);
    } catch (err) {
      console.error("Error loading sample image:", err);
    }
  };

  // Helper function to calculate Haversine distance (in km)
  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number) => {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a = 
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * (Math.PI / 180)) * Math.cos(lat2 * (Math.PI / 180)) * 
      Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  // Helper to store threat for the interactive map
  const storeThreatForMap = (lat: number, lng: number, threatScore: number, classification: string) => {
    try {
      if (typeof window === "undefined") return;
      
      const localLocation = localStorage.getItem('userLocation');
      const parsedLoc = localLocation ? JSON.parse(localLocation) : { lat: 21.0, lng: 88.0 };
      
      const distance = calculateDistance(parsedLoc.lat, parsedLoc.lng, lat, lng);
      
      // Determine AI Insights based on score & distance
      let vulnerability = "Medium";
      let damagePotential = "Moderate";
      
      if (threatScore > 85) {
        vulnerability = distance < 50 ? "Critical (Immediate Interception Required)" : "High (Monitor Track)";
        damagePotential = distance < 50 ? "Catastrophic damage to hull integrity" : "Significant infrastructure risk";
      } else if (threatScore > 60) {
        vulnerability = "High (Deploy Countermeasures)";
        damagePotential = "Substantial operational disruption";
      } else {
        vulnerability = "Low (Routine Observation)";
        damagePotential = "Minor superficial impact";
      }

      const newThreat = {
        id: `threat_${Date.now()}`,
        lat,
        lng,
        distance: distance.toFixed(2),
        classification,
        threatScore: Math.round(threatScore),
        timestamp: new Date().toISOString(),
        vulnerability,
        damagePotential
      };

      const existingThreats = JSON.parse(localStorage.getItem('activeThreats') || '[]');
      const updatedThreats = [newThreat, ...existingThreats].slice(0, 10); // Keep last 10
      localStorage.setItem('activeThreats', JSON.stringify(updatedThreats));
      
      // Dispatch custom event for Command Center map to refresh
      window.dispatchEvent(new CustomEvent("threatDetected", { detail: newThreat }));
    } catch (error) {
      console.error("Failed to store threat for map", error);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const updateResults = (newResults: DetectionResult[]) => {
    setResults(newResults);
    onResultsUpdate?.(newResults);
  };

  const processImage = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setProcessingProgress(0);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("type", "image");

      const progressInterval = setInterval(() => {
        setProcessingProgress((prev) => {
          if (prev >= 90) return prev;
          return prev + Math.random() * 10;
        });
      }, 500);

      const response = await fetch("/api/detection/process", {
        method: "POST",
        body: formData,
      });

      clearInterval(progressInterval);
      setProcessingProgress(100);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Detection failed");
      }

      const result = await response.json();

      if (result.success) {
        const normalizedThreatScore =
          normalizeOverallThreatScore(result.overallThreatScore) ?? 0;

        // Get location from inputs or profile
        let finalLat = latitude ? parseFloat(latitude) : null;
        let finalLng = longitude ? parseFloat(longitude) : null;
        
        if (!finalLat || !finalLng) {
          try {
            const profile = JSON.parse(localStorage.getItem("userProfile") || "{}");
            if (profile.latitude && profile.longitude) {
              finalLat = parseFloat(profile.latitude);
              finalLng = parseFloat(profile.longitude);
              if (!latitude) setLatitude(profile.latitude.toString());
              if (!longitude) setLongitude(profile.longitude.toString());
            }
          } catch (e) {}
        }

        const isRawSonar = Boolean(selectedFile.name.match(/\.(xtf|jsf|sdf)$/i));
        const detectionResult: DetectionResult = {
          surveyId: result.surveyId,
          originalImage: isRawSonar ? (result.detectedImage || URL.createObjectURL(selectedFile)) : URL.createObjectURL(selectedFile),
          detectedImage: result.detectedImage,
          originalFileName: result.originalFileName || selectedFile.name,
          detections: result.detections,
          processingTime: result.processingTime,
          totalObjects: result.detections.length,
          overallThreatLevel: result.overallThreatLevel,
          overallThreatScore: normalizedThreatScore,
          threatCount: result.threatCount,
          timestamp: new Date(),
          seafloorFacies: result.seafloorFacies || "flat_sand",
          srrApplied: true,
        };

        const primaryDet = result.detections?.[0];
        const autoLat = primaryDet?.latitude || finalLat || undefined;
        const autoLng = primaryDet?.longitude || finalLng || undefined;

        addDetection({
          surveyId: detectionResult.surveyId,
          originalImage: detectionResult.originalImage,
          detectedImage: detectionResult.detectedImage,
          originalFileName: detectionResult.originalFileName,
          detections: detectionResult.detections,
          processingTime: detectionResult.processingTime,
          totalObjects: detectionResult.totalObjects,
          overallThreatLevel: detectionResult.overallThreatLevel,
          overallThreatScore: detectionResult.overallThreatScore,
          threatCount: detectionResult.threatCount,
          seafloorFacies: detectionResult.seafloorFacies,
          srrApplied: detectionResult.srrApplied,
          lat: autoLat,
          lng: autoLng,
        });

        const newResults = [detectionResult, ...results];
        updateResults(newResults);
        
        // Auto-plot real geotagged detections on the map
        if (typeof window !== "undefined" && result.detections?.length > 0) {
          window.dispatchEvent(
            new CustomEvent("varunaSurveyLoaded", {
              detail: {
                surveyId: result.surveyId,
                detections: result.detections,
              },
            })
          );
          result.detections.forEach((d: any) => {
            const dLat = d.latitude || autoLat;
            const dLng = d.longitude || autoLng;
            if (dLat && dLng) {
              storeThreatForMap(dLat, dLng, d.confidence_score || (d.confidence * 100), d.class);
            }
          });
        }
        
        if (result.notice || result.isEdgeFallback) {
          setBackendNotice(result.notice || "Processed via Varuna Edge Sonar Pipeline (FastAPI backend service offline).");
        } else {
          setBackendNotice(null);
        }
        setErrorMessage(null);
        setSelectedFile(null);
      } else {
        throw new Error("Detection failed");
      }
    } catch (error) {
      console.error("Detection error:", error);
      const msg = error instanceof Error ? error.message : "Unknown error";
      setErrorMessage(`Detection notice: ${msg}`);
    } finally {
      setIsProcessing(false);
      setProcessingProgress(0);
    }
  };

  const processVideo = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setProcessingProgress(0);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);
      formData.append("type", "video");

      const progressInterval = setInterval(() => {
        setProcessingProgress((prev) => {
          if (prev >= 90) return prev;
          return prev + Math.random() * 5;
        });
      }, 1000);

      const response = await fetch("/api/detection/process", {
        method: "POST",
        body: formData,
      });

      clearInterval(progressInterval);
      setProcessingProgress(100);

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "Video detection failed");
      }

      const result = await response.json();

      if (result.success) {
        const normalizedThreatScore =
          normalizeOverallThreatScore(result.overallThreatScore) ?? 0;

        // Get location from inputs or profile
        let finalLat = latitude ? parseFloat(latitude) : null;
        let finalLng = longitude ? parseFloat(longitude) : null;
        
        if (!finalLat || !finalLng) {
          try {
            const profile = JSON.parse(localStorage.getItem("userProfile") || "{}");
            if (profile.latitude && profile.longitude) {
              finalLat = parseFloat(profile.latitude);
              finalLng = parseFloat(profile.longitude);
              if (!latitude) setLatitude(profile.latitude.toString());
              if (!longitude) setLongitude(profile.longitude.toString());
            }
          } catch (e) {}
        }

        const detectionResult: DetectionResult = {
          originalImage: URL.createObjectURL(selectedFile),
          detectedImage: result.detectedVideo || result.detectedImage,
          originalFileName: result.originalFileName,
          detections: result.detections,
          processingTime: result.processingTime,
          totalObjects: result.detections.length,
          overallThreatLevel: result.overallThreatLevel,
          overallThreatScore: normalizedThreatScore,
          threatCount: result.threatCount,
          timestamp: new Date(),
        };

        addDetection({
          surveyId: detectionResult.surveyId,
          originalImage: detectionResult.originalImage,
          detectedImage: detectionResult.detectedImage,
          originalFileName: detectionResult.originalFileName,
          detections: detectionResult.detections,
          processingTime: detectionResult.processingTime,
          totalObjects: detectionResult.totalObjects,
          overallThreatLevel: detectionResult.overallThreatLevel,
          overallThreatScore: detectionResult.overallThreatScore,
          threatCount: detectionResult.threatCount,
          seafloorFacies: detectionResult.seafloorFacies,
          srrApplied: detectionResult.srrApplied,
          lat: finalLat || undefined,
          lng: finalLng || undefined,
        });

        // Dispatch event for real-time command center updates
        if (typeof window !== "undefined") {
          window.dispatchEvent(new CustomEvent("detectionAdded"));
        }

        const newResults = [detectionResult, ...results];
        updateResults(newResults);
        
        // Save to map if coords provided and threat detected
        if (finalLat && finalLng && normalizedThreatScore > 0) {
          const mainClass = result.detections[0]?.class || "Unknown Contact";
          storeThreatForMap(finalLat, finalLng, normalizedThreatScore, mainClass);
        }
        
        setSelectedFile(null);
      } else {
        throw new Error("Video detection failed");
      }
    } catch (error) {
      console.error("Video detection error:", error);
      const msg = error instanceof Error ? error.message : "Unknown error";
      setErrorMessage(`Video detection notice: ${msg}`);
    } finally {
      setIsProcessing(false);
      setProcessingProgress(0);
    }
  };

  return (
    <div className="space-y-6">
      {/* Tactical Status & Diagnostics Banners */}
      {backendNotice && (
        <div className="p-3.5 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-center justify-between text-xs text-amber-300 font-space-mono shadow-md backdrop-blur-sm">
          <div className="flex items-center gap-2.5">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse flex-shrink-0" />
            <span className="font-bold text-amber-400 uppercase tracking-wider">[EDGE INTELLIGENCE ACTIVE]</span>
            <span>{backendNotice}</span>
          </div>
          <button
            onClick={() => setBackendNotice(null)}
            className="text-amber-400 hover:text-white p-1 rounded transition-colors ml-2 flex-shrink-0"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="p-3.5 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center justify-between text-xs text-red-300 font-space-mono shadow-md backdrop-blur-sm">
          <div className="flex items-center gap-2.5">
            <AlertTriangle className="w-4 h-4 text-red-400 flex-shrink-0" />
            <span className="font-bold text-red-400 uppercase tracking-wider">[SYSTEM NOTICE]</span>
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-red-400 hover:text-white p-1 rounded transition-colors ml-2 flex-shrink-0"
            title="Dismiss"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* System metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <TacticalStat
          label="Detection Speed"
          value="30+"
          unit="FPS"
          variant="primary"
          icon={<Zap className="w-4 h-4 sm:w-5 sm:h-5" />}
        />
        <TacticalStat
          label="Classification"
          value="95.9"
          unit="%"
          variant="success"
          icon={<Eye className="w-4 h-4 sm:w-5 sm:h-5" />}
        />
        <TacticalStat
          label="Target Classes"
          value="4"
          unit="types"
          variant="secondary"
          icon={<BarChart3 className="w-4 h-4 sm:w-5 sm:h-5" />}
        />
        <TacticalStat
          label="Acoustic Shadows"
          value="100%"
          unit="Active"
          variant="primary"
          icon={<Settings className="w-4 h-4 sm:w-5 sm:h-5" />}
        />
      </div>

      {/* Upload and Processing */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-slate-900/40 border border-cyan-500/20 backdrop-blur-xl">
          <TabsTrigger value="image" className="flex items-center gap-2">
            <ImageIcon className="w-4 h-4" />
            Side-Scan Sonar Imagery (SSS)
          </TabsTrigger>
          <TabsTrigger value="video" className="flex items-center gap-2">
            <Video className="w-4 h-4" />
            Sonar Waterfall Stream
          </TabsTrigger>
        </TabsList>

        <TabsContent value="image" className="mt-6 space-y-6">
          <HolographicCard>
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-cyan-300 font-orbitron mb-2">
                  Side-Scan Sonar Debris & Anomaly Detection
                </h3>
                <p className="text-sm text-slate-400">
                  Upload raw side-scan sonar waterfall logs (.png, .jpg, .tiff) for automated debris classification & ecological risk assessment.
                </p>
              </div>

              <div
                className="border-2 border-dashed border-primary/30 rounded-xl p-8 text-center hover:border-primary/50 transition-colors cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*,.xtf,.jsf,.sdf"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <Upload className="w-12 h-12 text-cyan-300 mx-auto mb-4" />
                <p className="text-foreground mb-2 font-semibold">
                  Click to upload or drag and drop SSS waterfall log or raw sonar stream
                </p>
                <p className="text-sm text-slate-400">
                  Supports Raw Hydrographic Streams (.XTF, .JSF, .SDF) and Image records (PNG, JPG, TIFF, BMP)
                </p>
                {selectedFile && (
                  <div className="mt-4 p-3 rounded-lg bg-primary/10 border border-primary/30">
                    <p className="text-sm text-foreground">
                      Selected: {selectedFile.name}
                    </p>
                    <p className="text-xs text-slate-400">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                )}
              </div>

              {/* Quick Sample Select Bar */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="inline-block w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-cyan-300 font-orbitron">
                      Quick Sample Select (Verified Benchmarks)
                    </span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-space-mono">
                    7 Curated Sonar Waterfall Captures
                  </span>
                </div>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-2">
                  {DEMO_SAMPLES.map((sample) => {
                    const isSelected = selectedFile?.name === sample.filename;
                    return (
                      <button
                        key={sample.filename}
                        type="button"
                        onClick={() => handleSelectSample(sample)}
                        className={`group relative p-2.5 rounded-lg border text-left transition-all cursor-pointer ${
                          isSelected
                            ? "bg-cyan-950/70 border-cyan-400 text-cyan-200 shadow-lg shadow-cyan-500/20 ring-1 ring-cyan-400/50"
                            : "bg-slate-900/60 border-cyan-500/20 text-slate-300 hover:border-cyan-400/50 hover:bg-slate-800/60"
                        }`}
                      >
                        <div className="text-[11px] font-medium font-orbitron truncate text-cyan-300 group-hover:text-cyan-200">
                          {sample.label}
                        </div>
                        <div className="text-[10px] text-slate-400 truncate mt-0.5">
                          {sample.category}
                        </div>
                        <div className="mt-1 flex items-center justify-between text-[9px] font-space-mono text-cyan-400/80">
                          <span>{sample.badge}</span>
                          {isSelected && (
                            <span className="text-cyan-300 font-bold">✓</span>
                          )}
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="flex justify-center">
                <div className="grid grid-cols-2 gap-4 w-full max-w-md mb-6">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-space-mono text-cyan-400 uppercase tracking-widest block">Survey Latitude (Optional)</label>
                    <input 
                      type="number" 
                      step="any"
                      placeholder="e.g. 15.3520"
                      value={latitude}
                      onChange={(e) => setLatitude(e.target.value)}
                      className="w-full bg-slate-900 border border-cyan-500/30 rounded-lg px-3 py-2 text-cyan-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400 font-space-mono text-sm"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-space-mono text-cyan-400 uppercase tracking-widest block">Survey Longitude (Optional)</label>
                    <input 
                      type="number" 
                      step="any"
                      placeholder="e.g. 73.6240"
                      value={longitude}
                      onChange={(e) => setLongitude(e.target.value)}
                      className="w-full bg-slate-900 border border-cyan-500/30 rounded-lg px-3 py-2 text-cyan-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400 font-space-mono text-sm"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-center">
                <button
                  onClick={processImage}
                  disabled={!selectedFile || isProcessing}
                  className="flex items-center gap-2 px-8 py-3 rounded-xl font-semibold bg-gradient-to-r from-primary to-secondary text-card hover:shadow-lg hover:shadow-primary/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all cursor-pointer"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Analyzing Sonar Imagery...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Run AI Debris Detection
                    </>
                  )}
                </button>
              </div>

              {isProcessing && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-slate-400">
                    <span>Processing image...</span>
                    <span className="text-cyan-300 font-space-mono">
                      {Math.round(processingProgress)}%
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-border/50 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary to-secondary transition-all"
                      style={{ width: `${processingProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </HolographicCard>
        </TabsContent>

        <TabsContent value="video" className="mt-6 space-y-6">
          <HolographicCard>
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-bold text-cyan-300 font-orbitron mb-2">
                  Video Detection
                </h3>
                <p className="text-sm text-slate-400">
                  Process underwater videos for frame-by-frame threat analysis
                </p>
              </div>

              <div
                className="border-2 border-dashed border-primary/30 rounded-xl p-8 text-center hover:border-primary/50 transition-colors cursor-pointer"
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="video/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
                <Video className="w-12 h-12 text-cyan-300 mx-auto mb-4" />
                <p className="text-foreground mb-2 font-semibold">
                  Click to upload or drag and drop
                </p>
                <p className="text-sm text-slate-400">
                  Supports MP4, AVI, MOV, MKV formats
                </p>
                {selectedFile && (
                  <div className="mt-4 p-3 rounded-lg bg-primary/10 border border-primary/30">
                    <p className="text-sm text-foreground">
                      Selected: {selectedFile.name}
                    </p>
                    <p className="text-xs text-slate-400">
                      {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                )}
              </div>

              <div className="flex justify-center">
                <div className="grid grid-cols-2 gap-4 w-full max-w-md mb-6">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-space-mono text-cyan-400 uppercase tracking-widest block">Threat Latitude</label>
                    <input 
                      type="number" 
                      step="any"
                      placeholder="e.g. 15.3520"
                      value={latitude}
                      onChange={(e) => setLatitude(e.target.value)}
                      className="w-full bg-slate-900 border border-cyan-500/30 rounded-lg px-3 py-2 text-cyan-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400 font-space-mono text-sm"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-space-mono text-cyan-400 uppercase tracking-widest block">Threat Longitude</label>
                    <input 
                      type="number" 
                      step="any"
                      placeholder="e.g. 73.6240"
                      value={longitude}
                      onChange={(e) => setLongitude(e.target.value)}
                      className="w-full bg-slate-900 border border-cyan-500/30 rounded-lg px-3 py-2 text-cyan-100 placeholder:text-slate-600 focus:outline-none focus:border-cyan-400 font-space-mono text-sm"
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-center">
                <button
                  onClick={processVideo}
                  disabled={!selectedFile || isProcessing || !latitude || !longitude}
                  className="flex items-center gap-2 px-8 py-3 rounded-xl font-semibold bg-gradient-to-r from-primary to-secondary text-card hover:shadow-lg hover:shadow-primary/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {isProcessing ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Detect in Video
                    </>
                  )}
                </button>
              </div>

              {isProcessing && (
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-slate-400">
                    <span>Processing video frames...</span>
                    <span className="text-cyan-300 font-space-mono">
                      {Math.round(processingProgress)}%
                    </span>
                  </div>
                  <div className="w-full h-2 rounded-full bg-border/50 overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-primary to-secondary transition-all"
                      style={{ width: `${processingProgress}%` }}
                    />
                  </div>
                </div>
              )}
            </div>
          </HolographicCard>
        </TabsContent>
      </Tabs>

      {/* Real-time Map Overlay */}
      {results.length > 0 && (
        <HolographicCard>
          <div className="space-y-4">
            <div className="flex items-center justify-between border-b border-cyan-500/20 pb-3">
              <div>
                <h2 className="text-xl font-bold text-cyan-300 font-orbitron flex items-center gap-2">
                  <Map className="w-5 h-5 text-cyan-400" />
                  Real-Time GIS Sonar Map Overlay
                </h2>
                <p className="text-xs text-slate-400 font-space-mono mt-1">
                  Automated acoustic geotagging • Real-time anomaly positions with slant-to-ground range correction
                </p>
              </div>
              <span className="text-xs font-space-mono text-emerald-400 px-3 py-1 rounded bg-emerald-500/10 border border-emerald-500/30 font-bold">
                {results[0]?.detections?.length || 0} Targets Plotted
              </span>
            </div>

            <div className="h-[420px] w-full rounded-xl overflow-hidden">
              <AdvancedLeafletMap
                detections={results[0]?.detections || []}
                surveyId={results[0]?.surveyId}
                className="w-full h-full"
              />
            </div>
          </div>
        </HolographicCard>
      )}

      {/* Live feed */}
      <HolographicCard>
        <div className="space-y-4">
          <h3 className="text-lg font-bold text-cyan-300 font-orbitron">
            Real-Time Activity Feed
          </h3>
          <RealTimeFeed />
        </div>
      </HolographicCard>
    </div>
  );
}
