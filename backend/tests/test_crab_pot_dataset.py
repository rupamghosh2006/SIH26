"""
Unit and Integration Tests for PINGEcosystem Crab Pot SSS Dataset and YOLO Training Pipeline.
Verifies:
1. Sample fixtures generation matching PINGEcosystem structure.
2. JSONL metadata parser and bounding box normalization.
3. YOLO dataset preparation with valid data.yaml.
4. Training initialization and execution on Crab Pot Sonar data.
"""

import os
import json
import pytest
import numpy as np
from pathlib import Path

from ai_pipeline.datasets.download_crab_pot_dataset import (
    generate_sample_crab_pot_fixtures,
    parse_jsonl_annotations,
    convert_crab_pot_to_yolo_labels,
    download_or_load_crab_pot_dataset
)
from ai_pipeline.train_crab_pot_yolo import (
    prepare_crab_pot_yolo_dataset,
    train_crab_pot_sonar_detector
)


@pytest.fixture
def temp_crab_pot_dir(tmp_path):
    target = tmp_path / "crab_pot_raw"
    generate_sample_crab_pot_fixtures(target, count=10)
    return target


def test_generate_sample_crab_pot_fixtures(temp_crab_pot_dir):
    """Test that sample crab pot fixtures create train and valid splits with metadata.jsonl."""
    train_dir = temp_crab_pot_dir / "train"
    valid_dir = temp_crab_pot_dir / "valid"

    assert train_dir.exists()
    assert valid_dir.exists()
    assert (train_dir / "metadata.jsonl").exists()
    assert (valid_dir / "metadata.jsonl").exists()

    # Verify at least one image exists in train
    train_images = list(train_dir.glob("*.jpg"))
    assert len(train_images) > 0


def test_parse_jsonl_annotations(temp_crab_pot_dir):
    """Test parsing JSONL annotations into records."""
    train_dir = temp_crab_pot_dir / "train"
    jsonl_path = train_dir / "metadata.jsonl"

    records = parse_jsonl_annotations(jsonl_path, train_dir)
    assert len(records) > 0

    first_rec = records[0]
    assert "file_name" in first_rec
    assert "bboxes" in first_rec
    assert "categories" in first_rec
    assert len(first_rec["bboxes"]) > 0


def test_convert_crab_pot_to_yolo_labels(temp_crab_pot_dir, tmp_path):
    """Test converting parsed JSONL records into YOLO format annotations."""
    train_dir = temp_crab_pot_dir / "train"
    jsonl_path = train_dir / "metadata.jsonl"
    records = parse_jsonl_annotations(jsonl_path, train_dir)

    out_images = tmp_path / "yolo_test" / "images" / "train"
    out_labels = tmp_path / "yolo_test" / "labels" / "train"

    converted = convert_crab_pot_to_yolo_labels(records, out_labels, out_images, class_idx=0)
    assert converted > 0

    txt_files = list(out_labels.glob("*.txt"))
    assert len(txt_files) == converted

    # Check contents of first txt file
    with open(txt_files[0], "r") as f:
        lines = f.readlines()
        assert len(lines) > 0
        parts = lines[0].strip().split()
        assert len(parts) == 5
        cls_id = int(parts[0])
        assert cls_id == 0
        xc, yc, w, h = map(float, parts[1:])
        assert 0.0 <= xc <= 1.0
        assert 0.0 <= yc <= 1.0
        assert 0.0 <= w <= 1.0
        assert 0.0 <= h <= 1.0


def test_prepare_crab_pot_yolo_dataset(temp_crab_pot_dir, tmp_path):
    """Test preparing complete YOLO dataset with data.yaml."""
    out_yolo = tmp_path / "crab_pot_yolo_ready"
    data_yaml = prepare_crab_pot_yolo_dataset(temp_crab_pot_dir, out_yolo, force_convert=True)

    assert data_yaml.exists()
    assert (out_yolo / "images" / "train").exists()
    assert (out_yolo / "images" / "val").exists()
    assert (out_yolo / "labels" / "train").exists()
    assert (out_yolo / "labels" / "val").exists()


def test_train_crab_pot_sonar_detector_interface(temp_crab_pot_dir, tmp_path):
    """Test train_crab_pot_sonar_detector initializes and configures dataset without crashing."""
    out_yolo = tmp_path / "crab_pot_yolo_run"
    models_dir = tmp_path / "models"

    result = train_crab_pot_sonar_detector(
        raw_data_dir=str(temp_crab_pot_dir),
        yolo_data_dir=str(out_yolo),
        models_dir=str(models_dir),
        epochs=1,
        batch_size=4,
        imgsz=384
    )

    assert "status" in result
    assert result["status"] in ["success", "dataset_prepared"]
