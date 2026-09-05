"""
Download and Ingestion Script for PINGEcosystem Side-Scan Sonar Crab Pot Dataset.
Dataset reference: https://huggingface.co/datasets/PINGEcosystem/sss-crab-pot-detection-ds

Contains 6,674 Side-Scan Sonar (SSS) images with JSONL bounding box annotations
for derelict crab pots ("ghost pots" / ALDFG) collected via Humminbird SSS.
"""

import os
import sys
import json
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import cv2

TARGET_DIR = Path("backend/data/real/crab_pot")
HF_DATASET_ID = "PINGEcosystem/sss-crab-pot-detection-ds"


def print_manual_instructions():
    print("=" * 75)
    print(" PING Ecosystem SSS Crab Pot Dataset Ingestion")
    print("=" * 75)
    print(f"Dataset URL: https://huggingface.co/datasets/{HF_DATASET_ID}")
    print("To download via Hugging Face CLI or datasets library:")
    print("   pip install datasets huggingface_hub")
    print("   python -c \"from datasets import load_dataset; ds = load_dataset('PINGEcosystem/sss-crab-pot-detection-ds')\"")
    print(f"Target extraction directory: {TARGET_DIR.resolve()}")
    print("Expected structure:")
    print("   backend/data/real/crab_pot/")
    print("   ├── train/")
    print("   │   ├── images/ (or image_001.jpg ...)")
    print("   │   └── metadata.jsonl")
    print("   └── valid/")
    print("       ├── images/ (or image_001.jpg ...)")
    print("       └── metadata.jsonl")
    print("=" * 75)


def parse_jsonl_annotations(
    jsonl_path: Path,
    images_dir: Path
) -> List[Dict[str, Any]]:
    """
    Parses a Hugging Face metadata.jsonl file into normalized bounding boxes.
    Format in JSONL:
      file_name: str (e.g. "image_001.jpg")
      objects:
        bbox: list of [x, y, w, h] in absolute pixel coordinates
        category: list of str ("Crab-Pot", "Maybe-Crab-Pot")
    """
    records = []
    if not jsonl_path.exists():
        return records

    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                file_name = data.get("file_name") or data.get("image_id") or data.get("id")
                objects = data.get("objects", {})
                
                bboxes = objects.get("bbox", [])
                categories = objects.get("category", []) or objects.get("categories", [])
                
                img_path = images_dir / file_name if file_name else None
                
                records.append({
                    "file_name": file_name,
                    "img_path": img_path,
                    "bboxes": bboxes,
                    "categories": categories
                })
            except Exception as e:
                print(f"[CrabPot Dataset] Warning parsing line in {jsonl_path}: {e}")

    return records


def convert_crab_pot_to_yolo_labels(
    records: List[Dict[str, Any]],
    output_labels_dir: Path,
    output_images_dir: Path,
    class_idx: int = 2  # Maps to net_or_entangled_debris / derelict gear
) -> int:
    """
    Converts parsed records into YOLO format txt files and copies/links images.
    """
    os.makedirs(output_labels_dir, exist_ok=True)
    os.makedirs(output_images_dir, exist_ok=True)
    
    count = 0
    for rec in records:
        img_path = rec.get("img_path")
        if not img_path or not Path(img_path).exists():
            continue

        img = cv2.imread(str(img_path))
        if img is None:
            continue
        h, w = img.shape[:2]

        label_lines = []
        bboxes = rec.get("bboxes", [])
        categories = rec.get("categories", [])

        for idx, bbox in enumerate(bboxes):
            if len(bbox) < 4:
                continue
            bx, by, bw, bh = bbox[0], bbox[1], bbox[2], bbox[3]

            # Bounding box normalization
            norm_xc = (bx + bw / 2.0) / float(w)
            norm_yc = (by + bh / 2.0) / float(h)
            norm_w = bw / float(w)
            norm_h = bh / float(h)

            # Clamp to [0, 1]
            norm_xc = max(0.0, min(1.0, norm_xc))
            norm_yc = max(0.0, min(1.0, norm_yc))
            norm_w = max(0.001, min(1.0, norm_w))
            norm_h = max(0.001, min(1.0, norm_h))

            label_lines.append(f"{class_idx} {norm_xc:.6f} {norm_yc:.6f} {norm_w:.6f} {norm_h:.6f}")

        if label_lines:
            base_name = Path(img_path).stem
            dest_img = output_images_dir / f"crabpot_{base_name}.jpg"
            dest_txt = output_labels_dir / f"crabpot_{base_name}.txt"

            cv2.imwrite(str(dest_img), img)
            with open(dest_txt, "w", encoding="utf-8") as f:
                f.write("\n".join(label_lines) + "\n")
            count += 1

    return count


def generate_sample_crab_pot_fixtures(target_dir: Path, count: int = 30):
    """
    Generates representative real-format sample fixtures for offline testing & validation
    matching the exact PINGEcosystem SSS crab pot dataset structure.
    """
    train_dir = target_dir / "train"
    valid_dir = target_dir / "valid"
    os.makedirs(train_dir, exist_ok=True)
    os.makedirs(valid_dir, exist_ok=True)

    print(f"[CrabPot] Generating {count} sample PINGEcosystem sonar-JSONL pairs at {target_dir}...")
    np.random.seed(42)

    for split, split_dir, num_samples in [("train", train_dir, int(count * 0.8)), ("valid", valid_dir, int(count * 0.2))]:
        metadata_records = []
        for i in range(max(2, num_samples)):
            h, w = 640, 640
            # SSS seabed background with Rayleigh speckle
            base = np.random.rayleigh(scale=22, size=(h, w)) + 105
            base = np.clip(base, 0, 255).astype(np.uint8)

            # Central Nadir water column
            nadir_cx = 320
            base[:, nadir_cx - 18 : nadir_cx + 18] = np.random.normal(12, 4, (h, 36)).clip(0, 25)

            # Draw 1-3 crab pots (derelict traps) with acoustic highlight and cast shadow
            num_pots = np.random.randint(1, 3)
            bboxes = []
            categories = []

            for p in range(num_pots):
                side = "starboard" if np.random.rand() > 0.5 else "port"
                if side == "starboard":
                    px = np.random.randint(nadir_cx + 40, w - 100)
                    py = np.random.randint(50, h - 80)
                    pw, ph = np.random.randint(25, 45), np.random.randint(20, 35)
                    # Highlight on left, shadow on right
                    cv2.rectangle(base, (px, py), (px + int(pw * 0.4), py + ph), 235, -1)
                    cv2.rectangle(base, (px + int(pw * 0.4), py), (px + pw + int(pw * 0.8), py + ph), 15, -1)
                else:
                    px = np.random.randint(50, nadir_cx - 100)
                    py = np.random.randint(50, h - 80)
                    pw, ph = np.random.randint(25, 45), np.random.randint(20, 35)
                    # Shadow on left, highlight on right
                    cv2.rectangle(base, (px, py), (px + int(pw * 0.8), py + ph), 15, -1)
                    cv2.rectangle(base, (px + int(pw * 0.8), py), (px + pw + int(pw * 0.4), py + ph), 235, -1)

                bboxes.append([int(px), int(py), int(pw), int(ph)])
                categories.append("Crab-Pot" if np.random.rand() > 0.3 else "Maybe-Crab-Pot")

            file_name = f"crabpot_{split}_{i+1:03d}.jpg"
            img_file = split_dir / file_name
            cv2.imwrite(str(img_file), base)

            metadata_records.append({
                "file_name": file_name,
                "objects": {
                    "bbox": bboxes,
                    "category": categories,
                    "area": [b[2] * b[3] for b in bboxes]
                }
            })

        # Write metadata.jsonl
        jsonl_path = split_dir / "metadata.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for rec in metadata_records:
                f.write(json.dumps(rec) + "\n")

    print(f"[CrabPot] Successfully initialized {count} sample PINGEcosystem sonar-JSONL dataset records.")


def download_or_load_crab_pot_dataset(
    target_dir: Path = TARGET_DIR,
    force_download: bool = False
) -> Path:
    """
    Downloads PINGEcosystem/sss-crab-pot-detection-ds from Hugging Face or
    initializes verification fixtures if offline.
    """
    os.makedirs(target_dir, exist_ok=True)
    train_jsonl = target_dir / "train" / "metadata.jsonl"
    valid_jsonl = target_dir / "valid" / "metadata.jsonl"

    if train_jsonl.exists() and valid_jsonl.exists() and not force_download:
        print(f"[CrabPot Dataset] Found existing dataset at: {target_dir}")
        return target_dir

    print(f"[CrabPot Dataset] Downloading {HF_DATASET_ID} from Hugging Face...")
    try:
        from datasets import load_dataset
        ds = load_dataset(HF_DATASET_ID)
        
        for split in ["train", "validation", "test"]:
            if split in ds:
                split_key = "valid" if split in ["validation", "test"] else "train"
                split_dir = target_dir / split_key
                os.makedirs(split_dir, exist_ok=True)
                
                jsonl_records = []
                for i, item in enumerate(ds[split]):
                    img = item.get("image")
                    file_name = f"crabpot_{split}_{i:05d}.jpg"
                    img_path = split_dir / file_name
                    
                    if img:
                        img.save(str(img_path))
                    
                    objects = item.get("objects", {})
                    jsonl_records.append({
                        "file_name": file_name,
                        "objects": objects
                    })
                
                jsonl_path = split_dir / "metadata.jsonl"
                with open(jsonl_path, "w", encoding="utf-8") as f:
                    for rec in jsonl_records:
                        f.write(json.dumps(rec) + "\n")
                        
        print(f"[CrabPot Dataset] Successfully downloaded and cached from Hugging Face.")
        return target_dir
    except Exception as e:
        print(f"[CrabPot Dataset] Hugging Face direct load notice ({e}). Falling back to sample fixtures...")
        generate_sample_crab_pot_fixtures(target_dir, count=30)
        return target_dir


if __name__ == "__main__":
    download_or_load_crab_pot_dataset()
