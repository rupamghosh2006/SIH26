/**
 * Varuna AI - Subsea Acoustic Physics & Telemetry Engine
 * Problem Statement: SIH26057 (Ministry of Earth Sciences)
 * 
 * Provides mathematical formulas for Side-Scan Sonar (SSS) across-track 
 * slant-range correction, target height derivation from acoustic cast shadows,
 * and grazing angle calculations.
 */

export interface AcousticGeometryParams {
  altitudeMeters: number;      // AUV / Towfish altitude above seabed (H)
  slantRangeMeters: number;    // Measured acoustic slant range (Rs)
  shadowLengthMeters: number;  // Measured acoustic shadow length on image (Ls)
  soundVelocityMps?: number;   // Speed of sound in seawater (~1500 m/s default)
}

export interface AcousticTargetDimensions {
  groundRangeM: number;       // Horizontal across-track distance from nadir (Rg)
  estimatedHeightM: number;   // Physical vertical height of debris object (ht)
  grazingAngleDeg: number;    // Acoustic beam incidence angle with seafloor (theta)
  shadowValidityRatio: number;// Contrast drop confidence score (0.0 to 1.0)
}

/**
 * Calculates horizontal ground range using Pythagorean slant-range correction:
 * Rg = sqrt(Rs^2 - H^2)
 */
export function calculateGroundRange(slantRangeM: number, altitudeM: number): number {
  if (slantRangeM <= altitudeM) return 0;
  return Math.sqrt(Math.max(0, Math.pow(slantRangeM, 2) - Math.pow(altitudeM, 2)));
}

/**
 * Derives the true physical vertical height of an object from its acoustic cast shadow:
 * ht = (Ls * H) / (Rs + Ls)
 */
export function calculateObjectHeight(
  shadowLengthM: number,
  altitudeM: number,
  slantRangeM: number
): number {
  if (slantRangeM + shadowLengthM <= 0) return 0;
  const height = (shadowLengthM * altitudeM) / (slantRangeM + shadowLengthM);
  return Math.max(0, Number(height.toFixed(2)));
}

/**
 * Computes acoustic grazing angle with respect to seabed:
 * theta = arcsin(H / Rs) in degrees
 */
export function calculateGrazingAngle(altitudeM: number, slantRangeM: number): number {
  if (slantRangeM <= 0 || altitudeM <= 0) return 0;
  const ratio = Math.min(1.0, altitudeM / slantRangeM);
  const angleRad = Math.asin(ratio);
  return Number(((angleRad * 180) / Math.PI).toFixed(1));
}

/**
 * Comprehensive acoustic geometry solver for side-scan sonar detections.
 */
export function computeAcousticTargetDimensions(
  params: AcousticGeometryParams
): AcousticTargetDimensions {
  const { altitudeMeters, slantRangeMeters, shadowLengthMeters } = params;

  const groundRangeM = calculateGroundRange(slantRangeMeters, altitudeMeters);
  const estimatedHeightM = calculateObjectHeight(shadowLengthMeters, altitudeMeters, slantRangeMeters);
  const grazingAngleDeg = calculateGrazingAngle(altitudeMeters, slantRangeMeters);

  // Shadow validity ratio based on expected geometric shadow length vs altitude
  const expectedMinShadow = (estimatedHeightM * slantRangeMeters) / Math.max(0.1, altitudeMeters - estimatedHeightM);
  const shadowRatio = shadowLengthMeters > 0 
    ? Math.min(1.0, shadowLengthMeters / Math.max(0.5, expectedMinShadow))
    : 0.0;

  return {
    groundRangeM: Number(groundRangeM.toFixed(2)),
    estimatedHeightM,
    grazingAngleDeg,
    shadowValidityRatio: Number(shadowRatio.toFixed(2)),
  };
}
