"""
Unit tests for preprocessing module (CLAHE, speckle filter, nadir detection, tiling).
"""

import numpy as np
import pytest
from ai_pipeline.preprocessing import (
    apply_clahe_contrast_enhancement,
    apply_adaptive_speckle_filter,
    detect_nadir_gap,
    preprocess_sonar_image,
    create_image_tiles,
    reconstruct_from_tiles
)


def test_clahe_enhancement():
    img = np.random.randint(80, 140, (200, 200), dtype=np.uint8)
    enhanced = apply_clahe_contrast_enhancement(img)
    assert enhanced.shape == img.shape
    assert enhanced.dtype == np.uint8
    # CLAHE typically widens standard deviation
    assert np.std(enhanced) >= np.std(img) - 1.0


def test_speckle_filter():
    img = np.full((100, 100), 120, dtype=np.uint8)
    noise = np.random.normal(0, 20, (100, 100)).astype(np.int16)
    noisy_img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    filtered = apply_adaptive_speckle_filter(noisy_img)
    assert filtered.shape == noisy_img.shape
    assert np.std(filtered) < np.std(noisy_img)


def test_detect_nadir_gap():
    img = np.full((400, 600), 120, dtype=np.uint8)
    # Put dark nadir in center (col 280 to 320)
    img[:, 280:320] = 10
    
    nadir_info = detect_nadir_gap(img)
    assert "nadir_center" in nadir_info
    assert 270 <= nadir_info["nadir_center"] <= 330
    assert nadir_info["nadir_width"] > 10


def test_image_tiling_and_reconstruction():
    img = np.random.randint(50, 200, (1200, 800), dtype=np.uint8)
    tiles = create_image_tiles(img, tile_size=640, overlap=0.20)
    
    assert len(tiles) > 1
    for t in tiles:
        assert t["tile_image"].shape == (640, 640)
        assert t["width"] <= 640
        assert t["height"] <= 640
        
    reconstructed = reconstruct_from_tiles(tiles, (1200, 800))
    assert reconstructed.shape == (1200, 800)
