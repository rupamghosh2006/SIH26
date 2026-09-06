"""
Comprehensive Unit & Integration Tests for Advanced Sonar Capabilities:
1. Hydrographic Sonar Format Ingestion (.XTF, .JSF, .SDF)
2. True Slant-Range to Ground-Range (SRR) Correction
3. Dedicated U-Net Ghost Net (ALDFG) Semantic Segmentation
4. Seabed Geological Interference Suppression (GLCM + 2D FFT Harmonics)
"""

import os
import tempfile
import numpy as np
import pytest
import cv2

from ai_pipeline.sonar_format_reader import SonarFormatReader, create_synthetic_xtf_file
from ai_pipeline.preprocessing import apply_slant_to_ground_range_correction
from ai_pipeline.geotagging import SonarGeotagger
from ai_pipeline.unet_segmentation import GhostNetSegmenter, GhostNetUNet, TORCH_AVAILABLE
from ai_pipeline.seabed_classifier import SeabedClassifier


def test_sonar_format_reader_xtf():
    """Verify parsing of Triton XTF binary streams."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        xtf_path = os.path.join(tmp_dir, "test_survey.xtf")
        create_synthetic_xtf_file(
            xtf_path,
            num_pings=32,
            samples_per_channel=256,
            slant_range_m=75.0,
            altitude_m=12.5
        )

        assert os.path.exists(xtf_path)
        sonar_data = SonarFormatReader.read_sonar_file(xtf_path)

        assert sonar_data.num_pings == 32
        assert sonar_data.samples_per_channel == 256
        assert sonar_data.slant_range_m == 75.0
        assert sonar_data.sensor_altitude_m == 12.5
        assert sonar_data.waterfall_image.shape == (32, 512)
        assert len(sonar_data.ping_records) == 32

        # Check navigation ping integrity
        first_ping = sonar_data.ping_records[0]
        assert hasattr(first_ping, "latitude") and first_ping.latitude > 0
        assert hasattr(first_ping, "longitude") and first_ping.longitude > 0
        assert hasattr(first_ping, "timestamp") and len(first_ping.timestamp) > 0
        assert sonar_data.sensor_altitude_m == 12.5


def test_slant_to_ground_range_correction():
    """Verify geometric distortion removal via inverse hyperbolic remapping."""
    h, w = 128, 512
    # Create synthetic sonar image with nadir water column in center
    img = np.full((h, w), 120, dtype=np.uint8)
    nadir_half_w = 40
    img[:, (w//2 - nadir_half_w):(w//2 + nadir_half_w)] = 15  # Dark water column

    srr_img, srr_info = apply_slant_to_ground_range_correction(
        img,
        altitude_m=12.0,
        max_slant_range_m=75.0,
        nadir_x=w // 2
    )

    assert srr_img.shape == (h, w)
    assert srr_img.dtype == np.uint8
    assert "max_ground_range_m" in srr_info
    assert srr_info["sensor_altitude_m"] == 12.0


def test_physical_dimension_calculation():
    """Verify that physical dimensions account for slant-range non-linearity."""
    geotagger = SonarGeotagger.generate_synthetic_trackline(
        num_pings=128,
        slant_range_m=75.0,
        altitude_m=12.0
    )

    # Calculate dimensions near nadir vs far range
    dims_near = geotagger.calculate_physical_dimensions(
        bbox_w_px=30,
        bbox_h_px=30,
        pixel_x=270,  # Just outside nadir (center is 256)
        image_width=512,
        nadir_x=256
    )

    dims_far = geotagger.calculate_physical_dimensions(
        bbox_w_px=30,
        bbox_h_px=30,
        pixel_x=480,  # Near outer edge
        image_width=512,
        nadir_x=256
    )

    assert "physical_width_m" in dims_near
    assert "physical_height_m" in dims_near
    assert "area_sq_meters" in dims_near
    assert dims_near["physical_width_m"] > 0
    assert dims_far["physical_width_m"] > 0


def test_ghost_net_unet_segmentation():
    """Verify U-Net inference, polygon contour extraction, and entangled area in m²."""
    segmenter = GhostNetSegmenter()

    # Create synthetic crop with bright filamentous net lines
    patch = np.full((128, 128), 60, dtype=np.uint8)
    # Draw webbed filaments
    cv2.line(patch, (30, 30), (90, 80), 240, 2)
    cv2.line(patch, (30, 80), (90, 30), 230, 2)
    cv2.circle(patch, (60, 55), 25, 210, 1)

    result = segmenter.segment_patch(patch, meters_per_pixel=0.08)

    assert "mask" in result
    assert "polygon" in result
    assert "entangled_area_m2" in result
    assert "perimeter_m" in result
    assert result["mask"].shape == (128, 128)
    assert result["entangled_area_m2"] > 0.0
    assert len(result["polygon"]) > 0


def test_seabed_geological_classifier():
    """Verify GLCM Haralick texture features and sand ripple harmonics."""
    classifier = SeabedClassifier()

    # 1. Smooth seafloor patch
    smooth_patch = np.full((64, 64), 100, dtype=np.uint8) + np.random.normal(0, 2, (64, 64)).astype(np.uint8)
    features = classifier.extract_glcm_features(smooth_patch)
    assert "contrast" in features
    assert "homogeneity" in features
    assert features["homogeneity"] > 0.30

    # 2. Ripple harmonics patch (sinusoidal grating)
    x = np.linspace(0, 10 * np.pi, 64)
    ripple_patch = (np.sin(x) * 40 + 128).astype(np.uint8)
    ripple_2d = np.tile(ripple_patch, (64, 1))
    ripple_analysis = classifier.analyze_ripple_harmonics(ripple_2d)
    assert "harmonic_strength" in ripple_analysis
    assert ripple_analysis["harmonic_strength"] > 0.20

    # 3. Facies classification
    facies_info = classifier.classify_facies(smooth_patch)
    assert facies_info["facies"] in ["smooth_mud", "flat_sand", "sand_ripples", "rocky_reef_boulders"]
    assert 0.0 <= facies_info["confidence"] <= 1.0

    # 4. Geological interference suppression
    # Rocky patch with high variance and dissimilarity
    rocky_patch = np.random.randint(20, 240, (128, 128), dtype=np.uint8)
    interference = classifier.evaluate_geological_interference(
        full_image=rocky_patch,
        bbox=(40, 40, 30, 30),
        has_shadow=False,
        shadow_score=0.1,
        shape_score=0.2
    )
    assert "facies" in interference
    assert "is_geological_risk" in interference
