// Database schema definitions for Varuna - Side-Scan Sonar Marine Debris Detection

export interface SonarSurvey {
  _id?: string
  surveyId: string
  title: string
  vesselName: string
  sensorModel: string // e.g. "EdgeTech 4200", "Klein 3000", "AUV SSS"
  frequencyKhz: number // 100, 400, 900
  slantRangeM: number
  altitudeM?: number
  startTime: Date
  endTime?: Date
  status: "recorded" | "processing" | "analyzed"
  totalPings?: number
  totalDetections?: number
  createdAt: Date
  updatedAt: Date
}

export interface SonarDetection {
  _id?: string
  surveyId: string
  targetClass: "ghost_net" | "fishing_gear" | "cylinder_pipe" | "container_drum" | "metal_debris" | "shipwreck" | "rock_cluster" | "unknown_anomaly"
  confidence: number // 0.0 to 1.0
  threatLevel: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
  ecologicalRisk: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW"
  pingIndex: number
  location: {
    latitude: number
    longitude: number
    depthM: number
    acrossTrackDistanceM: number
    side: "port" | "starboard"
  }
  boundingBox: {
    x: number
    y: number
    width: number
    height: number
  }
  acousticShadow: {
    shadowDetected: boolean
    shadowLengthM?: number
    estimatedHeightM?: number
    contrastRatio?: number
    directionVerified: boolean
  }
  dimensions: {
    lengthM?: number
    widthM?: number
    estimatedAreaM2?: number
  }
  verificationStatus: "pending_review" | "confirmed_debris" | "natural_seabed" | "retrieved"
  createdAt: Date
  updatedAt: Date
}

export interface DebrisTarget {
  _id?: string
  targetId: string
  classification: string
  priority: "immediate_recovery" | "scheduled_cleanup" | "monitoring" | "suppressed_natural"
  location: {
    latitude: number
    longitude: number
    region: string
    waterDepthM: number
  }
  firstSighted: Date
  lastVerified: Date
  ghostFishingRisk: boolean
  entangledBiotaObserved?: boolean
  cleanupMissionId?: string
  status: "active_hazard" | "recovery_in_progress" | "cleared"
  notes?: string
}

export interface AUVSwathMission {
  _id?: string
  missionName: string
  auvPlatform: string
  plannedSwathKm2: number
  surveyPattern: "lawnmower" | "parallel_swath" | "cross_grid"
  waypointCoordinates: Array<[number, number]> // [lon, lat]
  targetAltitudeM: number
  maxOperatingDepthM: number
  status: "planned" | "executing" | "completed" | "aborted"
  detectionsCount: number
  createdAt: Date
  updatedAt: Date
}

export interface SonarAIAnalysis {
  _id?: string
  analysisType: "yolo_detection" | "acoustic_shadow_validation" | "slant_range_correction"
  inputData: {
    type: "waterfall_patch" | "raw_ping_stream" | "survey_tile"
    dataRef: string
  }
  results: {
    detections: Array<{
      class: string
      confidence: number
      shadowVerified: boolean
    }>
    processingTimeMs: number
    modelCheckpoint: string
  }
  createdAt: Date
}

