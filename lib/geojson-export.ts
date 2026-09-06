/**
 * Varuna - GeoJSON FeatureCollection Export Service
 * Problem Statement: SIH26057 (Ministry of Earth Sciences)
 * 
 * Generates RFC 7946 compliant GeoJSON objects from sonar detections
 * for seamless integration into QGIS, ArcGIS, and hydrographic GIS software.
 */

export interface GeoJsonDetectionInput {
  id: string;
  latitude: number;
  longitude: number;
  depthMeters?: number | null;
  predictedClass: string;
  confidenceScore: number;
  confidenceTier: 'High' | 'Medium' | 'Low';
  estimatedSizeM?: string;
  shadowDetected: boolean;
  timestamp: string;
  surveyId: string;
}

export interface GeoJsonFeature {
  type: 'Feature';
  geometry: {
    type: 'Point';
    coordinates: [number, number, number?]; // [longitude, latitude, elevation/depth]
  };
  properties: {
    detectionId: string;
    surveyId: string;
    category: string;
    confidenceScore: number;
    confidenceTier: string;
    estimatedSize: string;
    shadowVerified: boolean;
    depthMeters: number | null;
    timestamp: string;
    agency: string;
    platform: string;
  };
}

export interface GeoJsonFeatureCollection {
  type: 'FeatureCollection';
  name: string;
  crs: {
    type: 'name';
    properties: {
      name: 'urn:ogc:def:crs:OGC:1.3:CRS84';
    };
  };
  features: GeoJsonFeature[];
}

/**
 * Converts an array of sonar debris detections into an OGC GeoJSON FeatureCollection.
 */
export function generateGeoJsonFeatureCollection(
  detections: GeoJsonDetectionInput[],
  surveyTitle: string = 'Varuna SSS Survey'
): GeoJsonFeatureCollection {
  const features: GeoJsonFeature[] = detections.map((det) => ({
    type: 'Feature',
    geometry: {
      type: 'Point',
      coordinates: det.depthMeters != null 
        ? [det.longitude, det.latitude, -Math.abs(det.depthMeters)] 
        : [det.longitude, det.latitude],
    },
    properties: {
      detectionId: det.id,
      surveyId: det.surveyId,
      category: det.predictedClass,
      confidenceScore: det.confidenceScore,
      confidenceTier: det.confidenceTier,
      estimatedSize: det.estimatedSizeM || 'N/A',
      shadowVerified: det.shadowDetected,
      depthMeters: det.depthMeters ?? null,
      timestamp: det.timestamp,
      agency: 'Ministry of Earth Sciences (MoES)',
      platform: 'Varuna Deep-Ocean Sonar System',
    },
  }));

  return {
    type: 'FeatureCollection',
    name: surveyTitle,
    crs: {
      type: 'name',
      properties: {
        name: 'urn:ogc:def:crs:OGC:1.3:CRS84',
      },
    },
    features,
  };
}
