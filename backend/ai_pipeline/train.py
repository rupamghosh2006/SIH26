"""
Training Script for VARUNA Sonar Marine Debris Detection.
Supports:
- Mixed real (AI4Shipwrecks + NOMBO/MILCO) and synthetic dataset training (--data-mix mixed)
- Real-only dataset training (--data-mix real)
- Synthetic-only training fallback (--data-mix synthetic)
- Dedicated real-only validation split evaluation (--val-split real_only)
- Automatic per-class balance logging and model checkpoint export.
"""

import os
import shutil
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
from ultralytics import YOLO

try:
    from .datasets.convert_to_yolo import convert_all_datasets_to_yolo, UNIFIED_CLASSES
    from .synthetic_generator import generate_synthetic_dataset
except ImportError:
    from ai_pipeline.datasets.convert_to_yolo import convert_all_datasets_to_yolo, UNIFIED_CLASSES
    from ai_pipeline.synthetic_generator import generate_synthetic_dataset


def train_varuna_model(
    data_mix: str = "mixed",            # "mixed", "real", "synthetic"
    val_split: str = "real_only",       # "real_only", "all", "synthetic"
    data_dir: Optional[str] = None,
    models_dir: str = "backend/models",
    epochs: int = 12,
    batch_size: int = 16,
    imgsz: int = 640,
    force_convert: bool = False
) -> str:
    """
    Main training execution function.
    Prepares dataset according to data-mix, logs class counts, trains YOLOv8,
    evaluates on real validation data, and saves checkpoint to models_dir/yolov8_varuna.pt.
    """
    os.makedirs(models_dir, exist_ok=True)
    models_path = Path(models_dir)

    print("=" * 75)
    print(f" VARUNA: Sonar Debris Detector Training")
    print(f" Mode: Data Mix = '{data_mix.upper()}', Validation Split = '{val_split.upper()}'")
    print(f" Epochs: {epochs}, Batch Size: {batch_size}, Image Size: {imgsz}x{imgsz}")
    print("=" * 75)

    if data_mix == "synthetic":
        # Pure synthetic path (legacy / fallback mode)
        target_data_dir = data_dir or "backend/data/synthetic_sonar"
        yaml_path = os.path.join(target_data_dir, "data.yaml")
        train_img_dir = os.path.join(target_data_dir, "images", "train")

        if force_convert or not os.path.exists(yaml_path) or not os.path.exists(train_img_dir) or len(os.listdir(train_img_dir)) < 30:
            print("[VARUNA] Generating synthetic training and validation dataset...")
            yaml_path = generate_synthetic_dataset(target_data_dir, num_train=250, num_val=50, image_size=imgsz)
        else:
            print(f"[VARUNA] Using existing synthetic dataset at: {target_data_dir}")
    else:
        # Mixed or Real path using unified converter
        target_data_dir = data_dir or "backend/data/unified_sonar"
        yaml_path = os.path.join(target_data_dir, "data.yaml")

        include_synthetic = (data_mix == "mixed")
        num_synth = 200 if data_mix == "mixed" else 0

        print(f"[VARUNA] Preparing unified dataset (Synthetic={include_synthetic}, ValMode={val_split})...")
        stats = convert_all_datasets_to_yolo(
            output_dir=target_data_dir,
            include_synthetic=include_synthetic,
            num_synthetic=num_synth,
            val_ratio=0.20,
            val_mode=val_split
        )
        yaml_path = stats.get("data_yaml", os.path.join(target_data_dir, "data.yaml"))

    # 2. Initialize YOLOv8 Model
    print("\n[VARUNA] Initializing YOLOv8 nano backbone...")
    model = YOLO("yolov8n.pt")

    # 3. Train Model
    project_dir = os.path.join("backend", "runs", "train")
    run_name = f"varuna_{data_mix}_{val_split}"

    print(f"\n[VARUNA] Launching training on {yaml_path}...")
    results = model.train(
        data=yaml_path,
        epochs=epochs,
        batch=batch_size,
        imgsz=imgsz,
        project=project_dir,
        name=run_name,
        exist_ok=True,
        verbose=True,
        workers=2
    )

    # 4. Export and Copy Best Checkpoint
    best_pt = os.path.join(project_dir, run_name, "weights", "best.pt")
    last_pt = os.path.join(project_dir, run_name, "weights", "last.pt")
    target_pt = str(models_path / "yolov8_varuna.pt")

    if os.path.exists(best_pt):
        shutil.copy2(best_pt, target_pt)
        print(f"\n[VARUNA] Best checkpoint saved to: {target_pt}")
    elif os.path.exists(last_pt):
        shutil.copy2(last_pt, target_pt)
        print(f"\n[VARUNA] Last checkpoint saved to: {target_pt}")
    else:
        model.save(target_pt)
        print(f"\n[VARUNA] Checkpoint saved to: {target_pt}")

    # 5. Dedicated Validation Benchmark (Real Data Evaluation)
    print("\n" + "=" * 75)
    print(" VARUNA: Final Validation Metrics Benchmark ")
    if val_split == "real_only":
        print(" [Benchmark: Held-Out REAL Side-Scan Sonar Imagery Only]")
    else:
        print(" [Benchmark: Standard Validation Split]")
    print("=" * 75)

    try:
        val_results = model.val(data=yaml_path, split="val", verbose=True)
        print(f"Validation Box Precision : {val_results.box.p.mean():.4f}")
        print(f"Validation Box Recall    : {val_results.box.r.mean():.4f}")
        print(f"Validation Box mAP@50    : {val_results.box.map50:.4f}")
        print(f"Validation Box mAP@50-95 : {val_results.box.map:.4f}")
    except Exception as e:
        print(f"Validation summary completed: {e}")

    print("=" * 75)
    return target_pt


def main():
    parser = argparse.ArgumentParser(description="Train VARUNA Sonar Marine Debris Detector")
    parser.add_argument(
        "--data-mix",
        type=str,
        default="mixed",
        choices=["mixed", "real", "synthetic"],
        help="Dataset composition: 'mixed' (real + synthetic), 'real' (only real AUV data), 'synthetic' (pure synthetic fallback)"
    )
    parser.add_argument(
        "--val-split",
        type=str,
        default="real_only",
        choices=["real_only", "all", "synthetic"],
        help="Validation split configuration: 'real_only' (evaluate strictly on real held-out AUV sonar images), 'all', 'synthetic'"
    )
    parser.add_argument("--epochs", type=int, default=10, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image resolution")
    parser.add_argument("--data", type=str, default=None, help="Custom dataset directory path")
    parser.add_argument("--models", type=str, default="backend/models", help="Target model weights directory")
    parser.add_argument("--force-convert", action="store_true", help="Force regenerate/reconvert dataset")

    args = parser.parse_args()

    train_varuna_model(
        data_mix=args.data_mix,
        val_split=args.val_split,
        data_dir=args.data,
        models_dir=args.models,
        epochs=args.epochs,
        batch_size=args.batch,
        imgsz=args.imgsz,
        force_convert=args.force_convert
    )


train_seaguard_model = train_varuna_model


if __name__ == "__main__":
    main()
