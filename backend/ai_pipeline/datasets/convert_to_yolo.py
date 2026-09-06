"""
Unified Dataset Normalization and YOLO Converter for VARUNA AI.
Merges and converts three sonar imagery sources:
1. AI4Shipwrecks (Binary segmentation masks -> Connected component bounding boxes -> Class 0: shipwreck)
2. NOMBO/MILCO (Mine/Object detection annotations -> Class 1: pipe_or_cylinder, Class 3: unknown_anomaly)
3. Synthetic SSS Generator (Ghost nets, pipes, shipwrecks -> Classes 0, 1, 2)

Generates unified YOLO format dataset with classes.yaml and data.yaml.
"""

import os
import shutil
import glob
import random
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import cv2

from .download_ai4shipwrecks import download_ai4shipwrecks
from .download_nombo_milco import download_nombo_milco
from ..synthetic_generator import SyntheticSonarGenerator

# Unified Class Taxonomy
UNIFIED_CLASSES = [
    "shipwreck",                 # 0
    "pipe_or_cylinder",          # 1
    "net_or_entangled_debris",   # 2
    "unknown_anomaly"            # 3
]

CLASS_TO_IDX = {c: i for i, c in enumerate(UNIFIED_CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(UNIFIED_CLASSES)}


def extract_bboxes_from_mask(mask: np.ndarray, min_area: int = 25) -> List[Tuple[int, float, float, float, float]]:
    """
    Extracts tightest enclosing YOLO bounding boxes from a binary segmentation mask
    using connected components analysis.
    Returns: List of (class_idx=0, x_center, y_center, width, height) in normalized coordinates.
    """
    h, w = mask.shape[:2]
    if len(mask.shape) == 3:
        mask_gray = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    else:
        mask_gray = mask

    # Threshold to ensure binary
    _, binary = cv2.threshold(mask_gray, 10, 255, cv2.THRESH_BINARY)
    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)

    bboxes = []
    for i in range(1, num_labels):  # Skip background (0)
        area = stats[i, cv2.CC_STAT_AREA]
        if area < min_area:
            continue

        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        bw = stats[i, cv2.CC_STAT_WIDTH]
        bh = stats[i, cv2.CC_STAT_HEIGHT]

        # Add slight padding for enclosing acoustic shadow
        pad_x = max(2, int(bw * 0.1))
        pad_y = max(2, int(bh * 0.1))

        bx1 = max(0, x - pad_x)
        by1 = max(0, y - pad_y)
        bx2 = min(w, x + bw + pad_x)
        by2 = min(h, y + bh + pad_y)

        norm_w = (bx2 - bx1) / float(w)
        norm_h = (by2 - by1) / float(h)
        norm_xc = (bx1 + bx2) / (2.0 * w)
        norm_yc = (by1 + by2) / (2.0 * h)

        bboxes.append((0, norm_xc, norm_yc, norm_w, norm_h))

    return bboxes


def convert_all_datasets_to_yolo(
    output_dir: str = "backend/data/unified_sonar",
    ai4shipwrecks_dir: Optional[str] = None,
    nombo_milco_dir: Optional[str] = None,
    include_synthetic: bool = True,
    num_synthetic: int = 300,
    val_ratio: float = 0.20,
    val_mode: str = "real_only",  # 'real_only', 'all', 'synthetic'
    seed: int = 42
) -> Dict[str, Any]:
    """
    Main normalization routine. Ingests AI4Shipwrecks, NOMBO/MILCO, and Synthetic
    imagery, generates YOLO bounding boxes, and writes unified train/val sets.
    """
    random.seed(seed)
    np.random.seed(seed)

    out_path = Path(output_dir)
    train_img_dir = out_path / "images" / "train"
    val_img_dir = out_path / "images" / "val"
    train_lbl_dir = out_path / "labels" / "train"
    val_lbl_dir = out_path / "labels" / "val"

    # Reset/prepare directories
    for d in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
        os.makedirs(d, exist_ok=True)

    records: List[Dict[str, Any]] = []

    # 1. Ingest AI4Shipwrecks
    ai4_path = Path(ai4shipwrecks_dir) if ai4shipwrecks_dir else download_ai4shipwrecks()
    ai4_imgs = sorted(list((ai4_path / "images").glob("*.png")) + list((ai4_path / "images").glob("*.jpg")))
    print(f"[Converter] Processing {len(ai4_imgs)} AI4Shipwrecks images...")

    for img_p in ai4_imgs:
        mask_p = ai4_path / "labels" / img_p.name
        if not mask_p.exists():
            # Try with .png extension
            mask_p = ai4_path / "labels" / f"{img_p.stem}.png"

        if mask_p.exists():
            mask = cv2.imread(str(mask_p), cv2.IMREAD_GRAYSCALE)
            if mask is not None:
                boxes = extract_bboxes_from_mask(mask)
                if boxes:
                    records.append({
                        "source": "real_ai4shipwrecks",
                        "is_real": True,
                        "image_path": str(img_p),
                        "boxes": boxes,
                        "primary_class": "shipwreck"
                    })

    # 2. Ingest NOMBO/MILCO
    nombo_path = Path(nombo_milco_dir) if nombo_milco_dir else download_nombo_milco()
    nombo_imgs = sorted(list((nombo_path / "images").glob("*.jpg")) + list((nombo_path / "images").glob("*.png")))
    print(f"[Converter] Processing {len(nombo_imgs)} NOMBO/MILCO images...")

    for img_p in nombo_imgs:
        lbl_p = nombo_path / "labels" / f"{img_p.stem}.txt"
        if lbl_p.exists():
            boxes = []
            with open(lbl_p, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        tag = parts[0].upper()
                        try:
                            xc, yc, bw, bh = map(float, parts[1:5])
                            # Mapping: MILCO -> 1 (pipe_or_cylinder), NOMBO -> 3 (unknown_anomaly)
                            if tag in ["MILCO", "MINE", "0"]:
                                cls_id = 1
                            elif tag in ["NOMBO", "CLUTTER", "1", "3"]:
                                cls_id = 3
                            else:
                                cls_id = 1
                            boxes.append((cls_id, xc, yc, bw, bh))
                        except ValueError:
                            continue
            if boxes:
                records.append({
                    "source": "real_nombo_milco",
                    "is_real": True,
                    "image_path": str(img_p),
                    "boxes": boxes,
                    "primary_class": "pipe_or_cylinder"
                })

    # 3. Generate / Ingest Synthetic Data
    if include_synthetic and num_synthetic > 0:
        print(f"[Converter] Generating {num_synthetic} synthetic sonar images for balanced coverage...")
        synth_gen = SyntheticSonarGenerator(image_width=640, image_height=640)
        synth_temp_dir = out_path / "temp_synthetic"
        os.makedirs(synth_temp_dir, exist_ok=True)

        for s_idx in range(num_synthetic):
            img_syn, anns = synth_gen.generate_image_with_debris()
            s_img_name = f"synth_sonar_{s_idx:05d}.jpg"
            s_img_path = synth_temp_dir / s_img_name
            cv2.imwrite(str(s_img_path), img_syn)

            synth_boxes = []
            for a in anns:
                orig_cls = a["class_name"]
                # Remap synthetic class names:
                # ghost_net -> 2: net_or_entangled_debris
                # pipe_cylinder -> 1: pipe_or_cylinder
                # shipwreck_fragment -> 0: shipwreck
                if orig_cls == "ghost_net":
                    c_id = 2
                elif orig_cls == "pipe_cylinder":
                    c_id = 1
                else:
                    c_id = 0

                xc, yc, bw, bh = a["yolo_bbox"]
                synth_boxes.append((c_id, xc, yc, bw, bh))

            if synth_boxes:
                records.append({
                    "source": "synthetic",
                    "is_real": False,
                    "image_path": str(s_img_path),
                    "boxes": synth_boxes,
                    "primary_class": "net_or_entangled_debris"
                })

    # Partition into Train and Validation
    real_records = [r for r in records if r["is_real"]]
    synth_records = [r for r in records if not r["is_real"]]

    random.shuffle(real_records)
    random.shuffle(synth_records)

    train_set: List[Dict[str, Any]] = []
    val_set: List[Dict[str, Any]] = []

    if val_mode == "real_only":
        # Keep a dedicated fraction of real images ONLY for validation
        n_real_val = max(1, int(len(real_records) * val_ratio))
        val_set.extend(real_records[:n_real_val])
        train_set.extend(real_records[n_real_val:])
        # All synthetic images go into train
        train_set.extend(synth_records)
    elif val_mode == "synthetic":
        n_synth_val = max(1, int(len(synth_records) * val_ratio))
        val_set.extend(synth_records[:n_synth_val])
        train_set.extend(synth_records[n_synth_val:])
        train_set.extend(real_records)
    else:  # 'all' mixed validation
        n_real_val = max(1, int(len(real_records) * val_ratio))
        n_synth_val = max(1, int(len(synth_records) * val_ratio))
        val_set.extend(real_records[:n_real_val])
        val_set.extend(synth_records[:n_synth_val])
        train_set.extend(real_records[n_real_val:])
        train_set.extend(synth_records[n_synth_val:])

    # Write files to disk
    counts = {c: {"train": 0, "val": 0} for c in UNIFIED_CLASSES}
    source_counts = {"real": {"train": 0, "val": 0}, "synthetic": {"train": 0, "val": 0}}

    for split_name, dataset in [("train", train_set), ("val", val_set)]:
        img_dest_dir = train_img_dir if split_name == "train" else val_img_dir
        lbl_dest_dir = train_lbl_dir if split_name == "train" else val_lbl_dir

        for idx, item in enumerate(dataset):
            prefix = "real_" if item["is_real"] else "synth_"
            src_type = "real" if item["is_real"] else "synthetic"
            source_counts[src_type][split_name] += 1

            orig_ext = os.path.splitext(item["image_path"])[1]
            out_filename = f"{prefix}{item['source']}_{idx:05d}{orig_ext}"
            out_lblname = f"{prefix}{item['source']}_{idx:05d}.txt"

            shutil.copy2(item["image_path"], str(img_dest_dir / out_filename))

            with open(lbl_dest_dir / out_lblname, "w") as f:
                for cls_id, xc, yc, bw, bh in item["boxes"]:
                    cls_name = IDX_TO_CLASS.get(cls_id, "unknown_anomaly")
                    counts[cls_name][split_name] += 1
                    f.write(f"{cls_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")

    # Clean temporary synthetic directory
    synth_temp = out_path / "temp_synthetic"
    if synth_temp.exists():
        shutil.rmtree(synth_temp, ignore_errors=True)

    # Generate data.yaml and classes.yaml
    classes_yaml = out_path / "classes.yaml"
    with open(classes_yaml, "w") as f:
        f.write("# Unified VARUNA AI Class Taxonomy\n")
        for i, c in enumerate(UNIFIED_CLASSES):
            f.write(f"{i}: {c}\n")

    data_yaml = out_path / "data.yaml"
    with open(data_yaml, "w") as f:
        f.write(f"path: {os.path.abspath(output_dir)}\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        f.write(f"nc: {len(UNIFIED_CLASSES)}\n")
        f.write(f"names: {UNIFIED_CLASSES}\n")

    stats = {
        "output_dir": str(out_path.resolve()),
        "data_yaml": str(data_yaml.resolve()),
        "total_train_images": len(train_set),
        "total_val_images": len(val_set),
        "source_breakdown": source_counts,
        "class_instance_counts": counts,
        "val_mode": val_mode
    }

    print("=" * 70)
    print(" VARUNA AI: Unified YOLO Dataset Generated ")
    print(f" Output: {out_path.resolve()}")
    print(f" Train Images: {len(train_set)} (Real: {source_counts['real']['train']}, Synth: {source_counts['synthetic']['train']})")
    print(f" Val Images: {len(val_set)} (Real: {source_counts['real']['val']}, Synth: {source_counts['synthetic']['val']})")
    print(" Per-Class Instance Distribution:")
    for c, cnt in counts.items():
        print(f"   • {c:25s}: Train={cnt['train']}, Val={cnt['val']}")
    print("=" * 70)

    return stats


if __name__ == "__main__":
    convert_all_datasets_to_yolo()
