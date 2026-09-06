"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { History, Radar, Upload } from "lucide-react";
import HolographicCard from "./holographic-card";
import DetectionResultsEnhanced from "./detection-results-enhanced";
import {
  deleteDetection,
  loadDetections,
  normalizeOverallThreatScore,
  type StoredDetection,
} from "@/lib/detection-storage";

export default function DetectionHistory() {
  const [results, setResults] = useState<StoredDetection[]>([]);
  const [hasLoaded, setHasLoaded] = useState(false);

  const refreshHistory = () => {
    setResults(loadDetections());
    setHasLoaded(true);
  };

  useEffect(() => {
    refreshHistory();
    window.addEventListener("detectionAdded", refreshHistory);
    window.addEventListener("storage", refreshHistory);
    return () => {
      window.removeEventListener("detectionAdded", refreshHistory);
      window.removeEventListener("storage", refreshHistory);
    };
  }, []);

  const downloadFile = (fileData: string, filename: string) => {
    try {
      const link = document.createElement("a");
      link.href = fileData;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error("Download failed:", error);
      alert("Download failed. Please try again.");
    }
  };

  const handleDelete = (id: string) => {
    if (!window.confirm("Are you sure you want to delete this detection result?")) {
      return;
    }
    deleteDetection(id);
    refreshHistory();
  };

  return (
    <div className="relative min-h-screen overflow-hidden bg-gradient-to-br from-slate-950 via-blue-950 to-cyan-950 pt-16">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_right,rgba(34,211,238,0.08),transparent_32%),radial-gradient(circle_at_bottom_left,rgba(14,116,144,0.14),transparent_35%)]" />

      <main className="relative mx-auto max-w-[1600px] px-4 py-7 sm:px-6 lg:px-8">
        <section className="mb-6 flex flex-col gap-5 rounded-2xl border border-cyan-300/15 bg-slate-950/55 p-5 backdrop-blur-md sm:p-6 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="mb-2 flex items-center gap-2 text-[10px] font-space-mono font-bold uppercase tracking-[0.16em] text-cyan-300/75">
              <History className="h-3.5 w-3.5" />
              Operations / Archive
            </div>
            <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
              <h1 className="font-orbitron text-2xl font-bold tracking-tight text-slate-100 sm:text-3xl">
                Detection history
              </h1>
              <span className="text-sm font-space-mono text-cyan-200">
                {results.length} {results.length === 1 ? "scan" : "scans"}
              </span>
            </div>
            <p className="mt-2 max-w-2xl text-sm text-slate-400">
              Review completed sonar scans, export reports, and manage prior detection records.
            </p>
          </div>

          <Link
            href="/detection"
            className="no-underline inline-flex items-center justify-center gap-2 self-start rounded-lg bg-cyan-300 px-4 py-2.5 text-sm font-semibold text-slate-950 transition-colors hover:bg-cyan-200 lg:self-auto"
          >
            <Upload className="h-4 w-4" />
            New detection
          </Link>
        </section>

        {hasLoaded && results.length === 0 ? (
          <HolographicCard>
            <div className="flex min-h-72 flex-col items-center justify-center px-5 py-12 text-center">
              <div className="mb-4 grid h-14 w-14 place-items-center rounded-2xl border border-cyan-300/20 bg-cyan-400/10">
                <Radar className="h-7 w-7 text-cyan-300" />
              </div>
              <h2 className="font-orbitron text-lg font-bold text-slate-100">No detections recorded yet</h2>
              <p className="mt-2 max-w-md text-sm text-slate-400">
                Run a sonar scan from the detection workspace and its results will appear here automatically.
              </p>
              <Link href="/detection" className="no-underline mt-5 text-sm font-semibold text-cyan-300 hover:text-cyan-100">
                Open detection workspace →
              </Link>
            </div>
          </HolographicCard>
        ) : (
          <div className="space-y-4">
            {results.map((result, index) => (
              <DetectionResultsEnhanced
                key={result.id}
                index={index}
                surveyId={result.surveyId}
                originalImage={result.originalImage}
                detectedImage={result.detectedImage}
                originalFileName={result.originalFileName}
                detections={result.detections}
                processingTime={result.processingTime}
                totalObjects={result.totalObjects}
                overallThreatLevel={result.overallThreatLevel}
                overallThreatScore={normalizeOverallThreatScore(result.overallThreatScore)}
                threatCount={result.threatCount}
                seafloorFacies={result.seafloorFacies}
                srrApplied={result.srrApplied}
                onDelete={() => handleDelete(result.id)}
                onDownload={downloadFile}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
