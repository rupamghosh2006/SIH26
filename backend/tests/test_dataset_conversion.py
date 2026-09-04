"""
Unit tests for AI4Shipwrecks, NOMBO/MILCO, and Mixed Dataset Conversion.
"""

import os
import shutil
import tempfile
import numpy as np
import cv2
import pytest
from ai_pipeline.datasets.convert_to_yolo import (
    extract_bboxes_from_mask,
    convert_all_datasets_to_yolo,
    UNIFIED_CLASSES,
    CLASS_TO_IDX
)


def test_extract_bboxes_from_binary_mask():
    """
    Test connected component bounding box extraction on a 400x400 binary mask.
    """
    mask = np.zeros((400, 400), dtype=np.uint8)
    # Draw two distinct wreck components
    cv2.rectangle(mask, (50, 60), (120, 100), 255, -1)   # Box 1: [50, 60, 70, 40]
    cv2.circle(mask, (300, 250), 30, 255, -1)            # Box 2: Circle radius 30 at 300, 250

    bboxes = extract_bboxes_from_mask(mask, min_area=20)
    
    assert len(bboxes) == 2, f"Expected 2 bounding boxes, got {len(bboxes)}"
    for cls_id, xc, yc, bw, bh in bboxes:
        assert cls_id == 0, f"AI4Shipwrecks class must be 0 (shipwreck), got {cls_id}"
        assert 0.0 < xc < 1.0
        assert 0.0 < yc < 1.0
        assert 0.0 < bw < 1.0
        assert 0.0 < bh < 1.0


def test_convert_all_datasets_real_only_val_split():
    """
    Test unified dataset conversion and verify that when val_mode='real_only',
    the validation set contains ONLY real images (prefixed with 'real_').
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        stats = convert_all_datasets_to_yolo(
            output_dir=temp_dir,
            include_synthetic=True,
            num_synthetic=20,
            val_ratio=0.25,
            val_mode="real_only"
        )

        assert os.path.exists(os.path.join(temp_dir, "data.yaml"))
        assert os.path.exists(os.path.join(temp_dir, "classes.yaml"))

        val_images = os.listdir(os.path.join(temp_dir, "images", "val"))
        assert len(val_images) > 0

        # Verify all validation images are from real sources
        for v_img in val_images:
            assert v_img.startswith("real_"), f"Validation image {v_img} is not from a real dataset in real_only mode"

        # Verify class counts exist
        assert stats["total_train_images"] > 0
        assert stats["total_val_images"] > 0
        assert len(UNIFIED_CLASSES) == 4
