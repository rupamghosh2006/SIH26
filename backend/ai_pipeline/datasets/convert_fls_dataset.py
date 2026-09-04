"""
Forward-Looking Sonar (FLS) Marine Debris Dataset Converter to YOLOv8 format.
Parses Watertank acoustic sonar images and Pascal VOC XML annotations,
normalizes coordinates, splits into train/val subsets, and generates data.yaml.
"""

import os
import shutil
import glob
import random
import yaml
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import cv2

# Marine Debris Taxonomy for FLS
FLS_CLASSES = [
    "tire",                   # 0
    "bottle_or_container",    # 1 (Bottle, Drink-carton, Shampoo-bottle, Standing-bottle)
    "can",                    # 2
    "chain_or_debris",        # 3
    "propeller",              # 4
    "valve",                  # 5
    "hook",                   # 6
    "wall_boundary"           # 7
]

CLASS_TO_IDX = {name: i for i, name in enumerate(FLS_CLASSES)}

RAW_CLASS_MAPPING = {
    "tire": "tire",
    "bottle": "bottle_or_container",
    "drink-carton": "bottle_or_container",
    "shampoo-bottle": "bottle_or_container",
    "standing-bottle": "bottle_or_container",
    "can": "can",
    "chain": "chain_or_debris",
    "propeller": "propeller",
    "valve": "valve",
    "hook": "hook",
    "wall": "wall_boundary"
}


def parse_voc_xml(xml_file: str, img_w: int, img_h: int) -> List[Tuple[int, float, float, float, float]]:
    """
    Parses XML annotation file with (x, y, w, h) bounding boxes
    and returns list of (class_idx, xc, yc, bw, bh) in normalized YOLO format.
    """
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    # Read size from XML if provided
    size_w = root.find("size/width")
    size_h = root.find("size/height")
    w_dim = int(size_w.text) if size_w is not None and int(size_w.text) > 0 else img_w
    h_dim = int(size_h.text) if size_h is not None and int(size_h.text) > 0 else img_h

    yolo_boxes = []
    for obj in root.findall("object"):
        raw_name = obj.find("name").text.strip().lower()
        if raw_name not in RAW_CLASS_MAPPING:
            continue
        
        target_name = RAW_CLASS_MAPPING[raw_name]
        class_idx = CLASS_TO_IDX[target_name]

        bbox = obj.find("bndbox")
        x_elem = bbox.find("x")
        y_elem = bbox.find("y")
        w_elem = bbox.find("w")
        h_elem = bbox.find("h")

        if x_elem is None or y_elem is None or w_elem is None or h_elem is None:
            # Check if standard xmin, ymin, xmax, ymax
            xmin = float(bbox.find("xmin").text)
            ymin = float(bbox.find("ymin").text)
            xmax = float(bbox.find("xmax").text)
            ymax = float(bbox.find("ymax").text)
            x, y = xmin, ymin
            w, h = xmax - xmin, ymax - ymin
        else:
            x = float(x_elem.text)
            y = float(y_elem.text)
            w = float(w_elem.text)
            h = float(h_elem.text)

        if w <= 0 or h <= 0:
            continue

        # Convert to normalized center coords
        norm_xc = (x + w / 2.0) / float(w_dim)
        norm_yc = (y + h / 2.0) / float(h_dim)
        norm_w = w / float(w_dim)
        norm_h = h / float(h_dim)

        # Clamp within [0, 1]
        norm_xc = max(0.001, min(0.999, norm_xc))
        norm_yc = max(0.001, min(0.999, norm_yc))
        norm_w = max(0.001, min(0.999, norm_w))
        norm_h = max(0.001, min(0.999, norm_h))

        yolo_boxes.append((class_idx, norm_xc, norm_yc, norm_w, norm_h))

    return yolo_boxes


def convert_fls_dataset(
    dataset_raw_dir: str,
    output_dir: str = "backend/data/fls_marine_debris_yolo",
    val_ratio: float = 0.20,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Converts Forward-Looking Sonar Marine Debris Dataset to YOLOv8 format.
    """
    random.seed(seed)
    
    # Locate Images and BoxAnnotations
    images_dir = os.path.join(dataset_raw_dir, "marine-fls", "marine-debris-fls-datasets-master", "md_fls_dataset", "data", "watertank-segmentation", "Images")
    boxes_dir = os.path.join(dataset_raw_dir, "marine-fls", "marine-debris-fls-datasets-master", "md_fls_dataset", "data", "watertank-segmentation", "BoxAnnotations")

    if not os.path.exists(images_dir):
        # Alternative fallback search
        found_imgs = glob.glob(f"{dataset_raw_dir}/**/watertank-segmentation/Images", recursive=True)
        if found_imgs:
            images_dir = found_imgs[0]
            boxes_dir = os.path.join(os.path.dirname(images_dir), "BoxAnnotations")
        else:
            raise FileNotFoundError(f"Could not find watertank-segmentation in {dataset_raw_dir}")

    out_path = Path(output_dir)
    train_img_dir = out_path / "images" / "train"
    val_img_dir = out_path / "images" / "val"
    train_lbl_dir = out_path / "labels" / "train"
    val_lbl_dir = out_path / "labels" / "val"

    for p in [train_img_dir, val_img_dir, train_lbl_dir, val_lbl_dir]:
        p.mkdir(parents=True, exist_ok=True)

    xml_files = sorted(glob.glob(os.path.join(boxes_dir, "*.xml")))
    print(f"[FLS Converter] Found {len(xml_files)} annotation files in {boxes_dir}")

    paired_samples = []
    for xml_file in xml_files:
        stem = Path(xml_file).stem
        img_name = f"{stem}.png"
        img_file = os.path.join(images_dir, img_name)
        if os.path.exists(img_file):
            paired_samples.append((img_file, xml_file, stem))

    print(f"[FLS Converter] Total verified image-annotation pairs: {len(paired_samples)}")

    # Shuffle and split
    random.shuffle(paired_samples)
    num_val = int(len(paired_samples) * val_ratio)
    val_samples = paired_samples[:num_val]
    train_samples = paired_samples[num_val:]

    print(f"[FLS Converter] Train set: {len(train_samples)} images | Val set: {len(val_samples)} images")

    class_counts = {c: 0 for c in FLS_CLASSES}

    def process_subset(samples, img_dest, lbl_dest, is_train: bool):
        for img_path, xml_path, stem in samples:
            img = cv2.imread(img_path)
            if img is None:
                continue
            h, w = img.shape[:2]

            boxes = parse_voc_xml(xml_path, w, h)
            if not boxes:
                continue

            # Copy image
            target_img_path = img_dest / f"{stem}.png"
            if not target_img_path.exists():
                shutil.copy2(img_path, target_img_path)

            # Write label file
            target_lbl_path = lbl_dest / f"{stem}.txt"
            with open(target_lbl_path, "w") as lf:
                for cls_idx, xc, yc, bw, bh in boxes:
                    lf.write(f"{cls_idx} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
                    if is_train:
                        class_counts[FLS_CLASSES[cls_idx]] += 1

    process_subset(train_samples, train_img_dir, train_lbl_dir, is_train=True)
    process_subset(val_samples, val_img_dir, val_lbl_dir, is_train=False)

    # Generate data.yaml with absolute or relative paths
    yaml_data = {
        "path": str(out_path.resolve()).replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "names": {i: name for i, name in enumerate(FLS_CLASSES)},
        "nc": len(FLS_CLASSES)
    }

    yaml_file = out_path / "data.yaml"
    with open(yaml_file, "w") as yf:
        yaml.dump(yaml_data, yf, default_flow_style=False)

    print("\n[FLS Converter] Training Class Bounding Box Distribution:")
    for k, v in class_counts.items():
        print(f"  - {k:22s}: {v} instances")

    print(f"\n[FLS Converter] Successfully created YOLO dataset at: {out_path.resolve()}")
    print(f"  Configuration File: {yaml_file}")

    return {
        "output_dir": str(out_path),
        "data_yaml": str(yaml_file),
        "num_train": len(train_samples),
        "num_val": len(val_samples),
        "class_counts": class_counts
    }


if __name__ == "__main__":
    raw_dir = r"C:\Users\Rupam Ghosh\.cache\kagglehub\datasets\era2730\forward-looking-sonar-marine-debris-dataset\versions\2"
    convert_fls_dataset(raw_dir)
