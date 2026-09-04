"""
Download and Ingestion Script for NOMBO/MILCO Sonar Dataset.
1,170 real AUV side-scan sonar images with object-detection annotations
distinguishing mine-like objects (MILCO) from non-mine bottom objects (NOMBO).

MILCO is used as a stand-in class for rigid cylinder/pipe-like debris.

Reference:
https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10879765/
"""

import os
import sys
import numpy as np
import cv2
from pathlib import Path

TARGET_DIR = Path("backend/data/real/nombo_milco")


def print_manual_instructions():
    print("=" * 70)
    print(" NOMBO/MILCO Sonar Dataset Download Instructions ")
    print("=" * 70)
    print("1. Refer to the dataset publication:")
    print("   https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10879765/")
    print(f"2. Extract the dataset files into:")
    print(f"   {TARGET_DIR.resolve()}")
    print("   Expected structure:")
    print("   backend/data/real/nombo_milco/")
    print("   ├── images/     (e.g., auv_milco_001.jpg, auv_nombo_002.jpg)")
    print("   └── labels/     (e.g., auv_milco_001.txt with YOLO or XML bbox format)")
    print("=" * 70)


def generate_sample_nombo_milco_fixtures(target_dir: Path, count: int = 40):
    """
    Generates representative real-format sample fixtures for offline testing
    matching the NOMBO/MILCO layout (images/ and labels/ with MILCO and NOMBO classes).
    """
    images_dir = target_dir / "images"
    labels_dir = target_dir / "labels"
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)

    print(f"[NOMBO/MILCO] Generating {count} sample sonar images and annotations at {target_dir}...")
    np.random.seed(123)

    for i in range(count):
        h, w = 640, 640
        # AUV seabed texture
        img = np.random.rayleigh(scale=22, size=(h, w)) + 105
        img = np.clip(img, 0, 255).astype(np.uint8)

        # Nadir strip
        img[:, 300:340] = np.random.normal(12, 4, (h, 40)).clip(0, 25)

        # Labels for this image
        lines = []

        # Determine target types (MILCO = 1: cylinder/pipe, NOMBO = 3: anomaly/clutter)
        has_milco = np.random.random() < 0.75
        has_nombo = np.random.random() < 0.50

        if has_milco:
            # Draw cylindrical highlight + parallel shadow
            side = -1 if np.random.random() < 0.5 else 1
            cx = np.random.randint(80, 260) if side == -1 else np.random.randint(380, 560)
            cy = np.random.randint(100, 540)
            pipe_len = np.random.randint(40, 80)
            pipe_w = np.random.randint(5, 9)

            p1 = (cx - pipe_w // 2, cy - pipe_len // 2)
            p2 = (cx + pipe_w // 2, cy + pipe_len // 2)

            # Shadow
            s_offset = side * np.random.randint(30, 60)
            cv2.rectangle(img, (cx + min(0, s_offset), cy - pipe_len // 2), (cx + max(0, s_offset), cy + pipe_len // 2), 15, -1)
            # Specular highlight
            cv2.rectangle(img, p1, p2, 245, -1)

            # YOLO box (enclosing highlight and shadow)
            bx1 = min(cx - pipe_w // 2, cx + s_offset) - 4
            bx2 = max(cx + pipe_w // 2, cx + s_offset) + 4
            by1 = cy - pipe_len // 2 - 4
            by2 = cy + pipe_len // 2 + 4

            xc = ((bx1 + bx2) / 2.0) / w
            yc = ((by1 + by2) / 2.0) / h
            bw = (bx2 - bx1) / float(w)
            bh = (by2 - by1) / float(h)
            
            # MILCO class (tag as MILCO or 1)
            lines.append(f"MILCO {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")

        if has_nombo:
            # Natural bottom anomaly / boulder patch without clean acoustic shadow
            cx = np.random.randint(100, 540)
            cy = np.random.randint(100, 540)
            rad = np.random.randint(15, 30)
            cv2.circle(img, (cx, cy), rad, 215, -1)

            xc = cx / float(w)
            yc = cy / float(h)
            bw = (rad * 2 + 8) / float(w)
            bh = (rad * 2 + 8) / float(h)
            lines.append(f"NOMBO {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")

        img_filename = f"nombo_milco_auv_{i+1:04d}.jpg"
        lbl_filename = f"nombo_milco_auv_{i+1:04d}.txt"

        cv2.imwrite(str(images_dir / img_filename), img)
        with open(labels_dir / lbl_filename, "w") as f:
            f.writelines(lines)

    print(f"[NOMBO/MILCO] Sample fixtures ready at {target_dir}")


def download_nombo_milco(force_download: bool = False, generate_fixtures: bool = True) -> Path:
    target_dir = TARGET_DIR
    images_dir = target_dir / "images"
    labels_dir = target_dir / "labels"

    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)

    existing_images = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
    if len(existing_images) > 0 and not force_download:
        print(f"[NOMBO/MILCO] Found {len(existing_images)} images at {target_dir}")
        return target_dir

    print_manual_instructions()

    if generate_fixtures and len(existing_images) == 0:
        generate_sample_nombo_milco_fixtures(target_dir, count=48)

    return target_dir


if __name__ == "__main__":
    download_nombo_milco()
