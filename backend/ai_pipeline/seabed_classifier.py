"""
Seabed Geological Interference Suppression & Facies Classification Module.

Distinguishes anthropogenic marine debris from natural seafloor geology using:
1. Haralick GLCM (Grey-Level Co-occurrence Matrix) statistical texture features:
   - Contrast, Dissimilarity, Homogeneity, Energy/ASM, Correlation
2. 2D FFT Harmonic Analysis for periodic sand ripples / megaripples
3. Seafloor Facies Classification:
   - smooth_mud, flat_sand, sand_ripples, rocky_reef_boulders
4. Natural Rock False-Positive Suppression Filter:
   - Detects natural boulder fields and rocky reefs that generate false positive
     acoustic highlights, penalizing confidence unless an anthropogenic acoustic shadow
     and geometric profile are proven.
"""

import math
from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import cv2

try:
    from skimage.feature import graycomatrix, graycoprops
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False


FACIES_CLASSES = [
    "smooth_mud",
    "flat_sand",
    "sand_ripples",
    "rocky_reef_boulders"
]


class SeabedClassifier:
    """
    Analyzes seafloor acoustic texture and suppresses geological false positives.
    """
    def __init__(self):
        pass

    def extract_glcm_features(self, patch: np.ndarray) -> Dict[str, float]:
        """
        Extracts Haralick GLCM texture features from a grayscale seabed patch.
        Uses 4 directions [0, 45, 90, 135 deg] and multi-distance co-occurrence.
        """
        if patch is None or patch.size == 0:
            return {
                "contrast": 0.0,
                "dissimilarity": 0.0,
                "homogeneity": 1.0,
                "energy": 0.0,
                "correlation": 0.0,
                "variance": 0.0
            }

        # Quantize to 16 gray levels for fast and robust GLCM computation
        quantized = (patch.astype(np.float32) / 16).astype(np.uint8)
        quantized = np.clip(quantized, 0, 15)

        if SKIMAGE_AVAILABLE:
            try:
                distances = [1, 3]
                angles = [0, np.pi/4, np.pi/2, 3*np.pi/4]
                glcm = graycomatrix(quantized, distances=distances, angles=angles, levels=16, symmetric=True, normed=True)
                
                contrast = float(np.mean(graycoprops(glcm, 'contrast')))
                dissimilarity = float(np.mean(graycoprops(glcm, 'dissimilarity')))
                homogeneity = float(np.mean(graycoprops(glcm, 'homogeneity')))
                energy = float(np.mean(graycoprops(glcm, 'energy')))
                correlation = float(np.mean(graycoprops(glcm, 'correlation')))
            except Exception:
                contrast, dissimilarity, homogeneity, energy, correlation = self._fallback_glcm(quantized)
        else:
            contrast, dissimilarity, homogeneity, energy, correlation = self._fallback_glcm(quantized)

        variance = float(np.var(patch))

        return {
            "contrast": round(contrast, 3),
            "dissimilarity": round(dissimilarity, 3),
            "homogeneity": round(homogeneity, 3),
            "energy": round(energy, 3),
            "correlation": round(correlation, 3),
            "variance": round(variance, 2)
        }

    @staticmethod
    def _fallback_glcm(quantized: np.ndarray) -> Tuple[float, float, float, float, float]:
        """Pure-NumPy statistical fallback for texture estimation."""
        h, w = quantized.shape[:2]
        if h < 2 or w < 2:
            return 0.0, 0.0, 1.0, 0.0, 0.0
        
        diff_h = np.abs(quantized[:, 1:] - quantized[:, :-1])
        diff_v = np.abs(quantized[1:, :] - quantized[:-1, :])
        
        contrast = float(np.mean(diff_h ** 2) + np.mean(diff_v ** 2)) / 2.0
        dissimilarity = float(np.mean(diff_h) + np.mean(diff_v)) / 2.0
        homogeneity = float(np.mean(1.0 / (1.0 + diff_h)) + np.mean(1.0 / (1.0 + diff_v))) / 2.0
        energy = float(1.0 / (1.0 + np.std(quantized)))
        correlation = 0.5
        return contrast, dissimilarity, homogeneity, energy, correlation

    def analyze_ripple_harmonics(self, patch: np.ndarray) -> Dict[str, Any]:
        """
        2D Fast Fourier Transform (FFT) analysis to detect periodic sand ripple crests.
        Computes dominant harmonic frequency peak ratio.
        """
        if patch is None or patch.shape[0] < 16 or patch.shape[1] < 16:
            return {"has_ripples": False, "harmonic_strength": 0.0, "dominant_period_px": 0.0}

        # Normalize and apply Hanning window to prevent edge ringing
        img = patch.astype(np.float32)
        img -= np.mean(img)
        win_y = np.hanning(img.shape[0])
        win_x = np.hanning(img.shape[1])
        window = np.outer(win_y, win_x)
        windowed = img * window

        # 2D FFT
        fft2 = np.fft.fft2(windowed)
        fft_shift = np.fft.fftshift(fft2)
        magnitude_spectrum = np.abs(fft_shift)

        h, w = magnitude_spectrum.shape
        cy, cx = h // 2, w // 2

        # Mask DC and low frequency center (keep mid-frequencies where ripples appear)
        y, x = np.ogrid[:h, :w]
        dist_from_center = np.sqrt((x - cx)**2 + (y - cy)**2)
        
        # Ripple frequency band: wavelengths between 6 and 40 pixels
        min_rad = min(h, w) / 40.0
        max_rad = min(h, w) / 6.0
        band_mask = (dist_from_center >= min_rad) & (dist_from_center <= max_rad)

        band_energy = magnitude_spectrum[band_mask]
        if band_energy.size == 0:
            return {"has_ripples": False, "harmonic_strength": 0.0, "dominant_period_px": 0.0}

        mean_energy = np.mean(band_energy)
        max_energy = np.max(band_energy)
        
        # Peak-to-average ratio in ripple band indicates periodic sand ripples
        harmonic_ratio = float(max_energy / (mean_energy + 1e-6))
        # Normalize harmonic strength to [0, 1]
        harmonic_strength = float(np.clip((harmonic_ratio - 2.5) / 5.0, 0.0, 1.0))
        
        # Approximate wavelength in pixels
        max_pos = np.unravel_index(np.argmax(band_energy), band_energy.shape)
        peak_dist = dist_from_center[band_mask][max_pos]
        period_px = float(min(h, w) / (peak_dist + 1e-6)) if peak_dist > 0 else 0.0

        has_ripples = bool(harmonic_strength >= 0.28)

        return {
            "has_ripples": has_ripples,
            "harmonic_strength": round(harmonic_strength, 3),
            "dominant_period_px": round(period_px, 1)
        }

    def classify_facies(self, patch: np.ndarray) -> Dict[str, Any]:
        """
        Classifies seabed facies from Haralick GLCM features and FFT ripple harmonics.
        Returns facies label, confidence score, and feature vector.
        """
        glcm = self.extract_glcm_features(patch)
        ripple = self.analyze_ripple_harmonics(patch)

        contrast = glcm["contrast"]
        homogeneity = glcm["homogeneity"]
        dissimilarity = glcm["dissimilarity"]
        variance = glcm["variance"]
        ripple_strength = ripple["harmonic_strength"]

        # Classification heuristics grounded in hydrographic sonar seabed acoustic properties
        scores = {}

        # 1. Sand Ripples: high harmonic periodicity
        scores["sand_ripples"] = float(np.clip(ripple_strength * 1.5 + (0.4 - abs(homogeneity - 0.35)), 0.0, 1.0))

        # 2. Rocky Reef / Boulders: high contrast, high dissimilarity, low homogeneity, high variance
        rock_score = (
            np.clip((contrast - 6.0) / 12.0, 0.0, 1.0) * 0.4 +
            np.clip((dissimilarity - 2.5) / 5.0, 0.0, 1.0) * 0.3 +
            np.clip((0.35 - homogeneity) / 0.3, 0.0, 1.0) * 0.3
        )
        scores["rocky_reef_boulders"] = float(np.clip(rock_score, 0.0, 1.0))

        # 3. Smooth Mud: very high homogeneity, low contrast, low variance
        mud_score = (
            np.clip((homogeneity - 0.40) / 0.4, 0.0, 1.0) * 0.5 +
            np.clip((8.0 - contrast) / 8.0, 0.0, 1.0) * 0.3 +
            np.clip((150.0 - variance) / 150.0, 0.0, 1.0) * 0.2
        )
        scores["smooth_mud"] = float(np.clip(mud_score, 0.0, 1.0))

        # 4. Flat Sand: moderate homogeneity, low-medium contrast, no strong ripple
        sand_score = (
            np.clip((0.55 - abs(homogeneity - 0.38)) / 0.4, 0.0, 1.0) * 0.5 +
            np.clip((1.0 - ripple_strength), 0.0, 1.0) * 0.3 +
            np.clip((12.0 - contrast) / 10.0, 0.0, 1.0) * 0.2
        )
        scores["flat_sand"] = float(np.clip(sand_score, 0.0, 1.0))

        # Winner take all with normalized softmax-like confidence
        best_facies = max(scores, key=scores.get)
        raw_max = scores[best_facies]
        total_s = sum(scores.values()) + 1e-6
        confidence = float(np.clip(raw_max / total_s, 0.35, 0.99))

        return {
            "facies": best_facies,
            "confidence": round(confidence, 2),
            "scores": {k: round(v, 2) for k, v in scores.items()},
            "features": {
                **glcm,
                "ripple_harmonic_strength": ripple_strength,
                "dominant_period_px": ripple["dominant_period_px"]
            }
        }

    def evaluate_geological_interference(
        self,
        full_image: np.ndarray,
        bbox: Tuple[int, int, int, int],
        has_shadow: bool,
        shadow_score: float,
        shape_score: float
    ) -> Dict[str, Any]:
        """
        Suppresses false positive detections triggered by natural geology.
        
        Args:
            full_image: Full 2D grayscale sonar image.
            bbox: [gx, gy, gw, gh] bounding box of candidate debris.
            has_shadow: Whether physical acoustic shadow was verified.
            shadow_score: Shadow verification score (0.0 to 1.0).
            shape_score: Geometric linearity / shape score (0.0 to 1.0).
            
        Returns:
            Dictionary with facies classification, interference risk, penalty factor,
            and explanation.
        """
        gx, gy, gw, gh = bbox
        img_h, img_w = full_image.shape[:2]

        # Extract surrounding seabed context patch (2x size of bounding box, excluding target center)
        pad_x = max(24, gw)
        pad_y = max(24, gh)
        x1 = max(0, gx - pad_x)
        y1 = max(0, gy - pad_y)
        x2 = min(img_w, gx + gw + pad_x)
        y2 = min(img_h, gy + gh + pad_y)

        context_crop = full_image[y1:y2, x1:x2].copy()
        
        # Mask out target center to classify background seafloor exclusively
        tgt_x1 = max(0, gx - x1)
        tgt_y1 = max(0, gy - y1)
        tgt_x2 = min(context_crop.shape[1], tgt_x1 + gw)
        tgt_y2 = min(context_crop.shape[0], tgt_y1 + gh)
        if tgt_y2 > tgt_y1 and tgt_x2 > tgt_x1:
            # Replace target with surrounding median intensity
            median_val = np.median(context_crop)
            context_crop[tgt_y1:tgt_y2, tgt_x1:tgt_x2] = median_val

        facies_info = self.classify_facies(context_crop)
        facies = facies_info["facies"]

        is_geological_risk = False
        penalty = 0.0
        suppression_reason = None

        if facies == "rocky_reef_boulders":
            # If target sits in a rocky boulder field and has no distinct acoustic shadow
            # or lacks geometric man-made regularity, it is likely a natural boulder.
            if not has_shadow or shadow_score < 0.40:
                is_geological_risk = True
                penalty = 0.30
                suppression_reason = "Target lies in rocky reef facies without distinct acoustic shadow (natural boulder false positive)."
            elif shape_score < 0.35:
                is_geological_risk = True
                penalty = 0.20
                suppression_reason = "Rocky seabed background with irregular natural geometry."

        elif facies == "sand_ripples":
            # Sand ripple crests can create rhythmic false highlight bands
            if shape_score < 0.30 and (not has_shadow or shadow_score < 0.30):
                is_geological_risk = True
                penalty = 0.25
                suppression_reason = "Harmonic sand ripple crest interference."

        return {
            "facies": facies,
            "facies_confidence": facies_info["confidence"],
            "features": facies_info["features"],
            "is_geological_risk": is_geological_risk,
            "penalty": penalty,
            "suppression_reason": suppression_reason
        }
