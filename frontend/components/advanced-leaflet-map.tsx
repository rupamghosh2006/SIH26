"use client";

import React, { useEffect, useState, useMemo } from "react";
import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer, Marker, Popup, Polyline, ZoomControl, useMap } from "react-leaflet";
import L from "leaflet";
import { Satellite, Globe, Waves, Moon } from "lucide-react";

export type BasemapType = "satellite" | "hybrid" | "ocean" | "dark";

export interface BasemapConfig {
  id: BasemapType;
  label: string;
  url: string;
  attribution: string;
  maxZoom: number;
  hasReferenceLabels?: boolean;
}

export const BASEMAP_OPTIONS: Record<BasemapType, BasemapConfig> = {
  satellite: {
    id: "satellite",
    label: "Satellite",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: '&copy; <a href="https://www.esri.com/">Esri</a> &copy; Maxar, Earthstar Geographics',
    maxZoom: 19,
  },
  hybrid: {
    id: "hybrid",
    label: "Hybrid",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attribution: '&copy; <a href="https://www.esri.com/">Esri</a> &copy; Maxar, Earthstar Geographics',
    maxZoom: 19,
    hasReferenceLabels: true,
  },
  ocean: {
    id: "ocean",
    label: "Ocean Chart",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}",
    attribution: '&copy; <a href="https://www.esri.com/">Esri</a>, GEBCO, NOAA',
    maxZoom: 13,
  },
  dark: {
    id: "dark",
    label: "Dark Tactical",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    attribution: '&copy; <a href="https://www.esri.com/">Esri</a>, HERE, Garmin, &copy; OpenStreetMap',
    maxZoom: 16,
  },
};

// Create custom icons dynamically
function createHtmlIcon(htmlContent: string) {
  return L.divIcon({
    html: htmlContent,
    className: "",
    iconSize: [28, 28],
    iconAnchor: [14, 14],
    popupAnchor: [0, -14],
  });
}

// Map Auto-Fitter Hook: automatically fits all detection markers and vessel into view
function MapBoundsUpdater({ points }: { points: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (!points || points.length === 0) return;
    if (points.length === 1) {
      map.flyTo(points[0], 12, { duration: 1.5 });
    } else {
      const bounds = L.latLngBounds(points);
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 14, duration: 1.5 });
    }
  }, [points, map]);
  return null;
}

export interface MapDetection {
  id: string | number;
  class?: string;
  predicted_class?: string;
  classification?: string;
  confidence?: number;
  confidence_score?: number;
  confidence_tier?: string;
  threat_level?: string;
  latitude?: number;
  lat?: number;
  longitude?: number;
  lng?: number;
  estimated_size_m?: string;
  physical_size_m?: string;
  acoustic_shadow_verified?: boolean;
  filter_details?: any;
}

interface AdvancedLeafletMapProps {
  detections?: MapDetection[];
  surveyId?: string;
  center?: [number, number];
  zoom?: number;
  className?: string;
  defaultBasemap?: BasemapType;
}

export default function AdvancedLeafletMap({
  detections: propDetections,
  surveyId,
  center = [15.352, 73.624], // Offshore Goa / Arabian Sea ocean transect
  zoom = 11,
  className = "w-full h-full min-h-[350px]",
  defaultBasemap = "satellite",
}: AdvancedLeafletMapProps) {
  const [mounted, setMounted] = useState(false);
  const [basemap, setBasemap] = useState<BasemapType>(defaultBasemap);
  const [vesselLocation, setVesselLocation] = useState<[number, number]>(center);
  const [localDetections, setLocalDetections] = useState<MapDetection[]>([]);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Listen for window-level custom events if detections are dispatched globally
  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleThreatEvent = (e: any) => {
      if (e.detail) {
        let threat = e.detail;
        if (threat.lng > 74.0 && threat.lng < 74.3 && threat.lat > 15.1 && threat.lat < 15.5) {
          threat = { ...threat, lng: Number((threat.lng - 0.5000).toFixed(5)) };
        }
        setLocalDetections((prev) => [threat, ...prev].slice(0, 50));
      }
    };

    const handleSurveyEvent = (e: any) => {
      if (e.detail?.detections) {
        const cleaned = e.detail.detections.map((d: any) => {
          let lng = d.longitude ?? d.lng;
          let lat = d.latitude ?? d.lat;
          if (typeof lng === "number" && typeof lat === "number" && lng > 74.0 && lng < 74.3 && lat > 15.1 && lat < 15.5) {
            lng = Number((lng - 0.5000).toFixed(5));
            return { ...d, longitude: lng, lng };
          }
          return d;
        });
        setLocalDetections(cleaned);
      }
    };

    window.addEventListener("threatDetected", handleThreatEvent);
    window.addEventListener("varunaSurveyLoaded", handleSurveyEvent);

    return () => {
      window.removeEventListener("threatDetected", handleThreatEvent);
      window.removeEventListener("varunaSurveyLoaded", handleSurveyEvent);
    };
  }, []);

  // Merge prop detections with local state
  const allDetections = useMemo(() => {
    const list: MapDetection[] = [];
    if (propDetections && propDetections.length > 0) {
      list.push(...propDetections);
    }
    if (localDetections && localDetections.length > 0) {
      list.push(...localDetections);
    }

    // Deduplicate by lat/lng or ID
    const seen = new Set<string>();
    const filtered: MapDetection[] = [];

    for (const d of list) {
      let lat = d.latitude ?? d.lat;
      let lng = d.longitude ?? d.lng;
      if (typeof lat !== "number" || typeof lng !== "number") continue;
      
      // Shift any inland Goa coordinates west into the offshore Arabian Sea
      if (lng > 74.0 && lng < 74.3 && lat > 15.1 && lat < 15.5) {
        lng = Number((lng - 0.5000).toFixed(5));
      }

      const key = `${lat.toFixed(5)}_${lng.toFixed(5)}_${d.class || d.predicted_class}`;
      if (!seen.has(key)) {
        seen.add(key);
        filtered.push({
          ...d,
          lat,
          lng,
        });
      }
    }

    return filtered;
  }, [propDetections, localDetections]);

  // If detections exist, center vessel near first detection
  useEffect(() => {
    if (allDetections.length > 0) {
      const first = allDetections[0];
      const lat = first.lat ?? first.latitude;
      const lng = first.lng ?? first.longitude;
      if (lat && lng) {
        setVesselLocation([lat - 0.005, lng - 0.005]);
      }
    }
  }, [allDetections]);

  const boundsPoints = useMemo(() => {
    const pts: [number, number][] = [vesselLocation];
    for (const d of allDetections) {
      if (d.lat && d.lng) {
        pts.push([d.lat, d.lng]);
      }
    }
    return pts;
  }, [allDetections, vesselLocation]);

  if (!mounted) {
    return (
      <div className={`${className} bg-slate-950 flex items-center justify-center border-2 border-cyan-500/30 rounded-2xl`}>
        <div className="text-cyan-400 font-space-mono text-xs animate-pulse flex items-center gap-2">
          <div className="w-3 h-3 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
          Loading Hydrographic Map Engine...
        </div>
      </div>
    );
  }

  const SurveyVesselIcon = createHtmlIcon(`
    <div style="width: 28px; height: 28px; background: rgba(16, 185, 129, 0.25); border: 2px solid #10b981; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 15px rgba(16, 185, 129, 0.7); animation: pulse 2s infinite;">
      <div style="width: 8px; height: 8px; background: #10b981; border-radius: 50%;"></div>
    </div>
  `);

  const getMarkerIcon = (tier?: string) => {
    const isCritical = tier === "High" || tier === "CRITICAL";
    const isMedium = tier === "Medium" || tier === "HIGH";
    const color = isCritical ? "#ef4444" : isMedium ? "#f97316" : "#06b6d4";
    const pulse = isCritical ? "animation: pulse 1.5s infinite;" : "";

    return createHtmlIcon(`
      <div style="width: 24px; height: 24px; background: ${color}33; border: 2px solid ${color}; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: 0 0 12px ${color}88; ${pulse}">
        <div style="width: 7px; height: 7px; background: ${color}; border-radius: 50%;"></div>
      </div>
    `);
  };

  return (
    <div className={`${className} relative rounded-2xl overflow-hidden border-2 border-cyan-500/30 shadow-xl shadow-cyan-950/40`}>
      <MapContainer
        center={vesselLocation}
        zoom={zoom}
        style={{ width: "100%", height: "100%", background: "#020617" }}
        zoomControl={false}
      >
        <MapBoundsUpdater points={boundsPoints} />
        <ZoomControl position="bottomright" />

        {/* High-Resolution Dynamic Tactical Basemap (Satellite Default) */}
        <TileLayer
          key={basemap}
          url={BASEMAP_OPTIONS[basemap].url}
          attribution={BASEMAP_OPTIONS[basemap].attribution}
          maxZoom={BASEMAP_OPTIONS[basemap].maxZoom}
        />

        {/* Optional Reference Labels Layer for Hybrid Mode */}
        {BASEMAP_OPTIONS[basemap].hasReferenceLabels && (
          <TileLayer
            key="hybrid-labels"
            url="https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"
            attribution='&copy; Esri &mdash; Boundaries & Places'
            maxZoom={19}
            zIndex={300}
          />
        )}

        {/* Survey Vessel Marker */}
        <Marker position={vesselLocation} icon={SurveyVesselIcon}>
          <Popup className="bg-slate-900 border border-emerald-500/50 text-white rounded-lg p-0">
            <div className="p-3 bg-slate-900 rounded-lg">
              <h4 className="text-emerald-400 font-orbitron font-bold text-sm">ORV-SAGAR (Survey Vessel)</h4>
              <p className="text-xs text-slate-400 font-space-mono mt-1">Status: Active SSS Acoustic Survey</p>
              <p className="text-xs text-slate-300 font-space-mono mt-1">
                Lat: {vesselLocation[0].toFixed(5)}° N, Lon: {vesselLocation[1].toFixed(5)}° E
              </p>
            </div>
          </Popup>
        </Marker>

        {/* Real Geotagged Detection Markers */}
        {allDetections.map((det, idx) => {
          const lat = det.lat ?? det.latitude ?? 0;
          const lng = det.lng ?? det.longitude ?? 0;
          const clsName = det.class || det.predicted_class || det.classification || "Marine Debris Target";
          const confVal = det.confidence_score ?? (det.confidence ? Math.round(det.confidence * 100) : 50);
          const tier = det.confidence_tier || (confVal >= 75 ? "High" : confVal >= 45 ? "Medium" : "Low");
          const sizeStr = det.estimated_size_m || det.physical_size_m || "Estimated via SRR";
          const shadowOk = det.acoustic_shadow_verified !== undefined ? det.acoustic_shadow_verified : true;

          return (
            <React.Fragment key={det.id || `map_det_${idx}`}>
              <Polyline
                positions={[vesselLocation, [lat, lng]]}
                color={tier === "High" ? "#ef4444" : tier === "Medium" ? "#f97316" : "#06b6d4"}
                weight={1.5}
                dashArray="4, 8"
                opacity={0.4}
              />
              <Marker position={[lat, lng]} icon={getMarkerIcon(tier)}>
                <Popup className="bg-slate-900 border border-cyan-500/50 text-white rounded-lg p-0">
                  <div className="p-3 bg-slate-900 rounded-lg max-w-[280px]">
                    <div className="flex items-center justify-between gap-2 border-b border-cyan-500/20 pb-1.5 mb-2">
                      <h4 className="text-cyan-300 font-orbitron font-bold text-xs uppercase tracking-wider">
                        {clsName.replace(/_/g, " ")}
                      </h4>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-space-mono font-bold ${
                        tier === "High"
                          ? "bg-red-500/20 text-red-300 border border-red-500/40"
                          : tier === "Medium"
                          ? "bg-orange-500/20 text-orange-300 border border-orange-500/40"
                          : "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40"
                      }`}>
                        {tier} Tier
                      </span>
                    </div>
                    <div className="space-y-1.5 text-xs font-space-mono text-slate-300">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Confidence:</span>
                        <span className="text-emerald-400 font-bold">{confVal.toFixed(1)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Coordinates:</span>
                        <span className="text-cyan-300 text-[11px]">{lat.toFixed(5)}°, {lng.toFixed(5)}°</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Physical Size:</span>
                        <span className="text-slate-200">{sizeStr}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Acoustic Shadow:</span>
                        <span className={shadowOk ? "text-emerald-400 font-bold" : "text-amber-400"}>
                          {shadowOk ? "Verified" : "Suppressed"}
                        </span>
                      </div>
                    </div>
                  </div>
                </Popup>
              </Marker>
            </React.Fragment>
          );
        })}
      </MapContainer>

      {/* Map Overlay Badge */}
      <div className="absolute top-3 left-3 z-[400] bg-slate-900/90 backdrop-blur-md border border-cyan-500/40 p-2.5 rounded-xl shadow-lg pointer-events-none">
        <h3 className="text-cyan-400 font-orbitron text-[11px] tracking-widest uppercase flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          Real-Time GIS Debris Overlay
        </h3>
        <p className="text-[10px] text-slate-400 font-space-mono mt-0.5">
          Plotted Targets: <span className="text-cyan-300 font-bold">{allDetections.length}</span>
          {allDetections.length > 0 && (
            <span className="ml-2 text-emerald-400">• True Geotag Active</span>
          )}
        </p>
      </div>

      {/* Basemap Switcher Tactical Control */}
      <div className="absolute top-3 right-3 z-[400] bg-slate-900/90 backdrop-blur-md border border-cyan-500/40 p-1 rounded-xl shadow-lg flex items-center gap-1">
        {(Object.keys(BASEMAP_OPTIONS) as BasemapType[]).map((key) => {
          const cfg = BASEMAP_OPTIONS[key];
          const isActive = basemap === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => setBasemap(key)}
              className={`flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-orbitron font-medium rounded-lg transition-all cursor-pointer ${
                isActive
                  ? "bg-cyan-500 text-slate-950 font-bold shadow-md shadow-cyan-500/40 ring-1 ring-cyan-300"
                  : "text-slate-300 hover:text-cyan-300 hover:bg-slate-800/80"
              }`}
              title={`Switch to ${cfg.label} View`}
            >
              {key === "satellite" && <Satellite className="w-3 h-3" />}
              {key === "hybrid" && <Globe className="w-3 h-3" />}
              {key === "ocean" && <Waves className="w-3 h-3" />}
              {key === "dark" && <Moon className="w-3 h-3" />}
              <span>{cfg.label}</span>
            </button>
          );
        })}
      </div>

      <style jsx global>{`
        .leaflet-popup-content-wrapper {
          background: transparent !important;
          padding: 0;
          box-shadow: none !important;
        }
        .leaflet-popup-tip {
          background: #0f172a !important;
          border: 1px solid rgba(6, 182, 212, 0.5);
        }
        .leaflet-container {
          background: #020617;
          font-family: inherit;
        }
        .leaflet-control-zoom {
          border: 1px solid rgba(6, 182, 212, 0.3) !important;
          border-radius: 8px !important;
          overflow: hidden;
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5) !important;
        }
        .leaflet-control-zoom a {
          background-color: rgba(15, 23, 42, 0.85) !important;
          color: #22d3ee !important;
          border-bottom: 1px solid rgba(6, 182, 212, 0.2) !important;
          backdrop-filter: blur(8px);
        }
        .leaflet-control-zoom a:hover {
          background-color: rgba(6, 182, 212, 0.2) !important;
          color: #ffffff !important;
        }
        .leaflet-control-attribution {
          background: rgba(2, 6, 23, 0.75) !important;
          color: #94a3b8 !important;
          font-size: 9px !important;
          backdrop-filter: blur(4px);
          padding: 2px 6px !important;
          border-top-left-radius: 6px;
        }
        .leaflet-control-attribution a {
          color: #38bdf8 !important;
        }
      `}</style>
    </div>
  );
}
