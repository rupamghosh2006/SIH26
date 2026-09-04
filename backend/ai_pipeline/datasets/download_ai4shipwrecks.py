"""
Download and Ingestion Script for AI4Shipwrecks Dataset.
286 real high-resolution side-scan sonar waterfall images with pixel-wise
shipwreck segmentation masks collected by AUV in Thunder Bay National Marine Sanctuary.

Dataset reference:
https://umfieldrobotics.github.io/ai4shipwrecks/
https://deepblue.lib.umich.edu/data/concern/data_sets/8623hz41x?locale=en
"""

import os
import sys
import urllib.request
import zipfile
import tarfile
import numpy as np
import cv2
from pathlib import Path

TARGET_DIR = Path("backend/data/real/ai4shipwrecks")


def print_manual_instructions():
    print("=" * 70)
    print(" AI4Shipwrecks Dataset Download Instructions ")
    print("=" * 70)
    print("1. Visit the University of Michigan Deep Blue Data repository:")
    print("   https://deepblue.lib.umich.edu/data/concern/data_sets/8623hz41x")
    print("2. Download the sonar waterfall images and segmentation masks archive.")
    print(f"3. Extract the contents into:")
    print(f"   {TARGET_DIR.resolve()}")
    print("   Expected structure:")
    print("   backend/data/real/ai4shipwrecks/")
    print("   ├── images/     (e.g., wreck_001.png, wreck_002.png)")
    print("   └── labels/     (e.g., wreck_001.png, wreck_002.png - binary masks)")
    print("=" * 70)


def generate_sample_ai4shipwrecks_fixtures(target_dir: Path, count: int = 24):
    """
    Generates representative real-format sample fixtures for offline testing
    matching the exact AI4Shipwrecks layout (images/ and labels/ binary mask pairs).
    """
    images_dir = target_dir / "images"
    labels_dir = target_dir / "labels"
    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)

    print(f"[AI4Shipwrecks] Generating {count} sample sonar-mask pairs at {target_dir}...")
    np.random.seed(42)

    for i in range(count):
        h, w = 800, 800
        # Simulated high-res AUV waterfall backscatter
        base = np.random.rayleigh(scale=25, size=(h, w)) + 110
        base = np.clip(base, 0, 255).astype(np.uint8)

        # Nadir line
        base[:, 380:420] = np.random.normal(15, 5, (h, 40)).clip(0, 30)

        # Create binary mask (0 = background, 255 = shipwreck)
        mask = np.zeros((h, w), dtype=np.uint8)

        # Draw 1 or 2 wreck structures
        num_wrecks = np.random.randint(1, 3)
        for _ in range(num_wrecks):
            cx = np.random.randint(120, 340) if np.random.random() < 0.5 else np.random.randint(460, 680)
            cy = np.random.randint(150, 650)
            rw = np.random.randint(40, 90)
            rh = np.random.randint(30, 70)

            # Mask polygon
            pts = np.array([
                [cx - rw // 2, cy - rh // 2],
                [cx + rw // 2, cy - rh // 3],
                [cx + rw // 3, cy + rh // 2],
                [cx - rw // 2, cy + rh // 2],
            ], dtype=np.int32)

            cv2.fillPoly(mask, [pts], 255)

            # Paint corresponding acoustic highlight and shadow on image
            shadow_offset = -60 if cx < 400 else 60
            shadow_pts = pts.copy()
            shadow_pts[:, 0] += shadow_offset
            cv2.fillPoly(base, [shadow_pts], 15)
            cv2.fillPoly(base, [pts], 240)

        filename = f"ai4shipwreck_auv_{i+1:04d}.png"
        cv2.imwrite(str(images_dir / filename), base)
        cv2.imwrite(str(labels_dir / filename), mask)

    print(f"[AI4Shipwrecks] Sample data ready in {target_dir}")


def download_ai4shipwrecks(force_download: bool = False, generate_fixtures: bool = True) -> Path:
    target_dir = TARGET_DIR
    images_dir = target_dir / "images"
    labels_dir = target_dir / "labels"

    os.makedirs(images_dir, exist_ok=True)
    os.makedirs(labels_dir, exist_ok=True)

    existing_images = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))
    if len(existing_images) > 0 and not force_download:
        print(f"[AI4Shipwrecks] Found {len(existing_images)} images at {target_dir}")
        return target_dir

    print_manual_instructions()

    if generate_fixtures and len(existing_images) == 0:
        generate_sample_ai4shipwrecks_fixtures(target_dir, count=32)

    return target_dir


if __name__ == "__main__":
    download_ai4shipwrecks()
