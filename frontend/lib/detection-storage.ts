"use client"

export interface StoredDetection {
  id: string
  timestamp: number
  surveyId?: string
  originalImage: string
  detectedImage: string
  originalFileName?: string
  detections: Array<{
    class: string
    confidence: number
    threat_level?: string
    bbox: [number, number, number, number]
    color: string
    verification_status?: string
    operator_notes?: string
    confidence_tier?: string
    detector_score?: number
    shadow_score?: number
    shape_score?: number
    shadow_detected?: boolean
    verification_record?: any
  }>
  processingTime: number
  totalObjects: number
  overallThreatLevel?: string
  overallThreatScore?: number
  threatCount?: number
  seafloorFacies?: string
  srrApplied?: boolean
  // Location where the detection was performed (from user profile GPS or manual input)
  lat?: number
  lng?: number
  locationName?: string
}

const STORAGE_KEY = "varuna_detections"
const MAX_STORED_DETECTIONS = 100

export function normalizeOverallThreatScore(score?: number): number | undefined {
  if (typeof score !== "number" || Number.isNaN(score)) return undefined

  const percentageScore = score <= 1 ? score * 100 : score
  const boundedScore = Math.max(0, Math.min(100, percentageScore))
  return Math.round(boundedScore * 10) / 10
}

function sanitizeToBayOfBengalSea(lat?: number, lng?: number): { lat?: number; lng?: number } {
  if (typeof lat !== "number" || typeof lng !== "number" || Number.isNaN(lat) || Number.isNaN(lng)) {
    return { lat, lng };
  }
  // If coordinates are in America (negative longitude)
  if (lng < 0) {
    const latOffset = ((Math.abs(lat) * 100) % 8) * 0.01;
    const lngOffset = ((Math.abs(lng) * 100) % 8) * 0.01;
    return {
      lat: Number((16.3300 + latOffset).toFixed(5)),
      lng: Number((84.5000 + lngOffset).toFixed(5)),
    };
  }
  // If legacy inland Goa coordinates
  if (lng > 74.0 && lng < 74.3 && lat > 15.1 && lat < 15.5) {
    return {
      lat: Number(lat.toFixed(5)),
      lng: Number((lng - 0.5000).toFixed(5)),
    };
  }
  return { lat, lng };
}

export function loadDetections(): StoredDetection[] {
  if (typeof window === "undefined") return []
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (!stored) return []

    const parsed: StoredDetection[] = JSON.parse(stored)
    if (!Array.isArray(parsed)) return []

    // Support both legacy 0-1 and current 0-100 threat-score formats,
    // and automatically migrate any American or inland coordinates into the Bay of Bengal open sea
    const normalized = parsed.map((detection) => {
      const sanitizedRoot = sanitizeToBayOfBengalSea(detection.lat, detection.lng);
      const lat = sanitizedRoot.lat;
      const lng = sanitizedRoot.lng;

      const updatedDets = (detection.detections || []).map((d: any) => {
        let dLat = d.latitude ?? d.lat;
        let dLng = d.longitude ?? d.lng ?? d.lon;
        const sanitizedDet = sanitizeToBayOfBengalSea(dLat, dLng);
        dLat = sanitizedDet.lat;
        dLng = sanitizedDet.lng;
        return { ...d, latitude: dLat, longitude: dLng, lat: dLat, lon: dLng, lng: dLng };
      });

      return {
        ...detection,
        lat,
        lng,
        detections: updatedDets,
        overallThreatScore: normalizeOverallThreatScore(detection.overallThreatScore),
      };
    });

    // Also migrate activeThreats in localStorage to Bay of Bengal ocean if needed
    try {
      const activeRaw = localStorage.getItem("activeThreats");
      if (activeRaw) {
        const threats = JSON.parse(activeRaw);
        if (Array.isArray(threats)) {
          let modified = false;
          const updatedThreats = threats.map((t: any) => {
            const sanitized = sanitizeToBayOfBengalSea(t.lat, t.lng);
            if (sanitized.lat !== t.lat || sanitized.lng !== t.lng) {
              modified = true;
              return { ...t, lat: sanitized.lat, lng: sanitized.lng };
            }
            return t;
          });
          if (modified) {
            localStorage.setItem("activeThreats", JSON.stringify(updatedThreats));
          }
        }
      }
    } catch (threatErr) {
      console.warn("Could not migrate activeThreats:", threatErr);
    }

    // Persist migrated scores and ocean coordinates once to keep subsequent reads consistent.
    if (JSON.stringify(parsed) !== JSON.stringify(normalized)) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
    }

    return normalized
  } catch (error) {
    console.error("[v0] Failed to load detections from localStorage:", error)
    return []
  }
}

export function saveDetections(detections: StoredDetection[]): void {
  if (typeof window === "undefined") return
  try {
    const limited = detections.slice(0, MAX_STORED_DETECTIONS)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(limited))
  } catch (error) {
    console.error("[v0] Failed to save detections to localStorage:", error)
  }
}

export function addDetection(detection: Omit<StoredDetection, "id" | "timestamp">): StoredDetection {
  const storedDetection: StoredDetection = {
    ...detection,
    id: `detection_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    timestamp: Date.now(),
  }

  const existing = loadDetections()
  const updated = [storedDetection, ...existing]
  saveDetections(updated)

  // Notify other components (like the Designer/Planner) that a new detection is available
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent("detectionAdded", { detail: storedDetection }))
  }

  return storedDetection
}

export function deleteDetection(id: string): void {
  const existing = loadDetections()
  const updated = existing.filter((d) => d.id !== id)
  saveDetections(updated)
}

export function clearAllDetections(): void {
  if (typeof window === "undefined") return
  try {
    localStorage.removeItem(STORAGE_KEY)
  } catch (error) {
    console.error(" Failed to clear detections from localStorage:", error)
  }
}

export function getThreatStats() {
  const detections = loadDetections()
  const totalScans = detections.length
  const totalThreats = detections.reduce((sum, d) => sum + (d.threatCount || 0), 0)

  let avgConfidence = 0
  if (detections.length > 0) {
    const allConfidences = detections.flatMap((d) => d.detections.map((det) => det.confidence))
    if (allConfidences.length > 0) {
      avgConfidence = Math.round(
        (allConfidences.reduce((sum, conf) => sum + conf, 0) / allConfidences.length) * 100,
      )
    }
  }

  const criticalThreats = detections.filter((d) => d.overallThreatLevel === "CRITICAL").length

  return { totalScans, totalThreats, avgConfidence, criticalThreats }
}

export function getAllThreatObjects() {
  const detections = loadDetections()
  return detections.flatMap((detection, scanIndex) =>
    detection.detections.map((obj, objIndex) => ({
      id: `${detection.id}_${objIndex}`,
      scanId: detection.id,
      scanIndex,
      timestamp: detection.timestamp,
      class: obj.class,
      confidence: obj.confidence,
      threat_level: obj.threat_level,
      bbox: obj.bbox,
      color: obj.color,
    })),
  )
}
