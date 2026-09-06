"use client";

import { useState, useEffect } from "react";
import { Activity, TrendingUp, AlertCircle, Radio } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { loadDetections } from "@/lib/detection-storage";

interface RealTimeFeedProps {
  isLoading?: boolean;
}

interface FeedItem {
  id: string | number;
  timestamp: Date;
  type: "detection" | "alert" | "info";
  message: string;
  confidence: number;
}

export default function RealTimeFeed({ isLoading = false }: RealTimeFeedProps) {
  const [feedItems, setFeedItems] = useState<FeedItem[]>([
    {
      id: 1,
      timestamp: new Date(),
      type: "detection",
      message: "ALDFG Ghost Net cluster identified at 16.35°N, 84.52°E",
      confidence: 98,
    },
    {
      id: 2,
      timestamp: new Date(Date.now() - 120000),
      type: "alert",
      message: "Proximity warning: Hydrographic debris near navigational fairway",
      confidence: 87,
    },
    {
      id: 3,
      timestamp: new Date(Date.now() - 300000),
      type: "detection",
      message: "Submerged metal hull section categorized with acoustic shadow",
      confidence: 91,
    },
    {
      id: 4,
      timestamp: new Date(Date.now() - 600000),
      type: "info",
      message: "System status: Dual-frequency SSS sonar telemetry synchronized",
      confidence: 100,
    },
  ]);

  // Sync recent detection events if available
  useEffect(() => {
    if (typeof window === "undefined") return;

    const refreshFeed = () => {
      try {
        const stored = loadDetections();
        if (stored && stored.length > 0) {
          const newItems: FeedItem[] = [];
          stored.slice(0, 5).forEach((survey, surveyIdx) => {
            survey.detections?.slice(0, 2).forEach((det, detIdx) => {
              const anyDet = det as any;
              const conf = Math.round(
                anyDet.confidence_score || (det.confidence <= 1 ? det.confidence * 100 : det.confidence)
              );
              newItems.push({
                id: `stored_${survey.id || surveyIdx}_${detIdx}`,
                timestamp: new Date(survey.timestamp),
                type: det.threat_level === "CRITICAL" || det.threat_level === "HIGH" ? "alert" : "detection",
                message: `${det.class.replace(/_/g, " ")} detected at ${
                  survey.lat ? `${survey.lat.toFixed(3)}°N, ${survey.lng?.toFixed(3)}°E` : "survey coordinate grid"
                }`,
                confidence: conf || 92,
              });
            });
          });

          if (newItems.length > 0) {
            setFeedItems((prev) => {
              const ids = new Set(newItems.map((i) => i.id));
              const filteredOld = prev.filter((i) => !ids.has(i.id));
              return [...newItems, ...filteredOld].slice(0, 8);
            });
          }
        }
      } catch (err) {
        console.error("Failed to sync detections to activity feed:", err);
      }
    };

    refreshFeed();

    const handleNewThreat = () => refreshFeed();
    const handleSurveyLoaded = () => refreshFeed();

    window.addEventListener("threatDetected", handleNewThreat);
    window.addEventListener("varunaSurveyLoaded", handleSurveyLoaded);
    window.addEventListener("detectionAdded", handleNewThreat);

    return () => {
      window.removeEventListener("threatDetected", handleNewThreat);
      window.removeEventListener("varunaSurveyLoaded", handleSurveyLoaded);
      window.removeEventListener("detectionAdded", handleNewThreat);
    };
  }, []);

  const getTypeColor = (type: string) => {
    switch (type) {
      case "detection":
        return "text-cyan-300";
      case "alert":
        return "text-yellow-400";
      case "info":
        return "text-secondary";
      default:
        return "text-slate-400";
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "detection":
        return <Activity className="w-4 h-4" />;
      case "alert":
        return <AlertCircle className="w-4 h-4" />;
      case "info":
        return <TrendingUp className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);

    if (seconds < 60) return "just now";
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  // Tactical Skeleton Loader when processing
  if (isLoading) {
    return (
      <div className="space-y-3 font-space-mono">
        {/* Telemetry Ingestion Status Bar */}
        <div className="p-2.5 rounded-lg bg-cyan-950/40 border border-cyan-500/30 flex items-center justify-between text-xs text-cyan-300">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-400" />
            </span>
            <span className="font-semibold uppercase tracking-wider text-[11px]">
              Telemetry Stream Active
            </span>
          </div>
          <span className="text-[10px] text-cyan-400/70 animate-pulse flex items-center gap-1.5">
            <Radio className="w-3 h-3 animate-pulse" />
            Ingesting Acoustic Waterfall Frames...
          </span>
        </div>

        {/* Skeleton Feed Rows */}
        <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
          {[
            { width: "w-3/4", subWidth: "w-24", badge: "w-10" },
            { width: "w-5/6", subWidth: "w-20", badge: "w-12" },
            { width: "w-2/3", subWidth: "w-28", badge: "w-10" },
            { width: "w-4/5", subWidth: "w-16", badge: "w-11" },
          ].map((item, idx) => (
            <div
              key={idx}
              className="p-3 rounded-lg border border-cyan-500/20 bg-slate-800/30 flex items-center gap-3 animate-pulse"
            >
              {/* Icon Skeleton */}
              <div className="w-8 h-8 rounded-lg bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center shrink-0">
                <Skeleton className="w-4 h-4 rounded bg-cyan-500/25" />
              </div>

              {/* Message & Timestamp Skeleton */}
              <div className="flex-1 min-w-0 space-y-2">
                <Skeleton className={`h-3.5 ${item.width} bg-cyan-500/20 rounded`} />
                <Skeleton className={`h-2.5 ${item.subWidth} bg-slate-700/60 rounded`} />
              </div>

              {/* Confidence Badge Skeleton */}
              <div className="shrink-0">
                <Skeleton className={`h-4 ${item.badge} bg-cyan-500/20 rounded`} />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3 max-h-96 overflow-y-auto">
      {feedItems.map((item) => (
        <div
          key={item.id}
          className="p-3 rounded-lg border border-cyan-500/20 bg-slate-800/30 flex gap-3 hover:bg-slate-800/50 transition-colors"
        >
          <div className={`flex-shrink-0 ${getTypeColor(item.type)}`}>
            {getTypeIcon(item.type)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-foreground">{item.message}</p>
            <p className="text-xs text-slate-400 mt-1">
              {formatTime(item.timestamp)}
            </p>
          </div>
          <div className="flex-shrink-0 text-right">
            <p className="text-xs font-space-mono text-cyan-300">
              {item.confidence}%
            </p>
          </div>
        </div>
      ))}
    </div>
  );
}
