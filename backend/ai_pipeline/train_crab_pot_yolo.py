"""
YOLOv8 Training and Fine-Tuning Script on PINGEcosystem Side-Scan Sonar (SSS) Crab Pot Dataset.
Dataset reference: https://huggingface.co/datasets/PINGEcosystem/sss-crab-pot-detection-ds

Trains YOLOv8 nano / medium detector on real Side-Scan Sonar derelict crab pot
and ghost fishing gear imagery, evaluates on held-out validation split, and exports weights.
"""

import os
import shutil
import argparse
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

import sys
from pathlib import Path

# Add backend directory to sys.path for direct CLI execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    from ai_pipeline.datasets.download_crab_pot_dataset import (
        download_or_load_crab_pot_dataset,
        parse_jsonl_annotations,
        convert_crab_pot_to_yolo_labels,
        TARGET_DIR
    )
except ImportError:
    from backend.ai_pipeline.datasets.download_crab_pot_dataset import (
        download_or_load_crab_pot_dataset,
        parse_jsonl_annotations,
        convert_crab_pot_to_yolo_labels,
        TARGET_DIR
    )


def prepare_crab_pot_yolo_dataset(
    raw_dataset_dir: Path = TARGET_DIR,
    output_yolo_dir: Path = Path("backend/data/crab_pot_yolo"),
    force_convert: bool = False
) -> Path:
    """
    Parses JSONL annotations and prepares a clean YOLO format dataset directory
    with train/val images and labels plus data.yaml.
    """
    os.makedirs(output_yolo_dir, exist_ok=True)
    data_yaml_path = output_yolo_dir / "data.yaml"

    if data_yaml_path.exists() and not force_convert:
        print(f"[CrabPot YOLO] Using existing normalized dataset at: {output_yolo_dir}")
        return data_yaml_path

    # Ensure raw dataset exists
    download_or_load_crab_pot_dataset(raw_dataset_dir)

    for split in ["train", "valid"]:
        split_src = raw_dataset_dir / split
        jsonl_path = split_src / "metadata.jsonl"
        
        # Output split folders
        split_out_name = "val" if split == "valid" else "train"
        out_images = output_yolo_dir / "images" / split_out_name
        out_labels = output_yolo_dir / "labels" / split_out_name
        
        records = parse_jsonl_annotations(jsonl_path, split_src)
        converted_count = convert_crab_pot_to_yolo_labels(records, out_labels, out_images, class_idx=0)
        print(f"[CrabPot YOLO] Converted {converted_count} images for split '{split_out_name}'.")

    # Generate data.yaml
    classes = ["crab_pot_or_derelict_gear"]
    yaml_dict = {
        "path": str(output_yolo_dir.resolve()).replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "names": {i: name for i, name in enumerate(classes)},
        "nc": len(classes)
    }

    with open(data_yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_dict, f, default_flow_style=False)

    print(f"[CrabPot YOLO] Successfully created data.yaml at {data_yaml_path}")
    return data_yaml_path


def train_crab_pot_sonar_detector(
    raw_data_dir: str = "backend/data/real/crab_pot",
    yolo_data_dir: str = "backend/data/crab_pot_yolo",
    models_dir: str = "backend/models",
    project_dir: Optional[str] = None,
    epochs: int = 5,
    batch_size: int = 16,
    imgsz: int = 640,
    base_model: str = "yolov8n.pt",
    export_to_production: bool = False
) -> Dict[str, Any]:
    """
    Main training execution function on PINGEcosystem Crab Pot SSS data.
    Separates test/CI execution (which writes to a temporary directory only)
    from explicit manual production training runs.
    """
    models_path = Path(models_dir)
    models_path.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print(" Varuna AI: YOLOv8 SSS Crab Pot Detector Training")
    print(f" Source Data         : {raw_data_dir}")
    print(f" Normalized          : {yolo_data_dir}")
    print(f" Base Weights        : {base_model}")
    print(f" Export Production   : {export_to_production}")
    print(f" Parameters          : Epochs={epochs}, Batch={batch_size}, ImgSize={imgsz}x{imgsz}")
    print("=" * 75)

    data_yaml_path = prepare_crab_pot_yolo_dataset(Path(raw_data_dir), Path(yolo_data_dir))

    if YOLO is None:
        print("[Varuna AI] Ultralytics YOLO not installed in current environment. Returning dataset configuration.")
        return {
            "status": "dataset_prepared",
            "data_yaml": str(data_yaml_path),
            "epochs": epochs
        }

    # Initialize model
    print(f"\n[Varuna AI] Loading base model backbone: {base_model}...")
    model = YOLO(base_model)

    if project_dir is None:
        if export_to_production:
            project_dir = os.path.join("backend", "runs", "train")
        else:
            project_dir = str(models_path / "runs")
    run_name = "varuna_sss_crab_pot"

    # Train
    print(f"\n[Varuna AI] Launching training on {data_yaml_path}...")
    results = model.train(
        data=str(data_yaml_path),
        epochs=epochs,
        batch=batch_size,
        imgsz=imgsz,
        project=project_dir,
        name=run_name,
        exist_ok=True,
        verbose=True,
        workers=2,
        save=True,
        plots=True
    )

    # Locate generated best.pt
    run_weights_dir = Path(project_dir) / run_name / "weights"
    best_pt = run_weights_dir / "best.pt"
    last_pt = run_weights_dir / "last.pt"
    source_pt = best_pt if best_pt.exists() else last_pt

    # Export checkpoint to target models_path
    target_crab_pot = models_path / "yolov8_crab_pot.pt"

    if source_pt.exists():
        shutil.copy2(str(source_pt), str(target_crab_pot))
        print(f"\n[Varuna AI] Checkpoint saved: {target_crab_pot}")
    else:
        model.save(str(target_crab_pot))
        print(f"\n[Varuna AI] Model saved: {target_crab_pot}")

    # Production export only when explicitly requested (NEVER during tests or CI)
    if export_to_production:
        prod_models = Path("backend/models")
        prod_models.mkdir(parents=True, exist_ok=True)
        target_varuna = prod_models / "yolov8_varuna.pt"
        target_prod_crab = prod_models / "yolov8_crab_pot.pt"
        target_root_best = Path("best.pt")

        shutil.copy2(str(target_crab_pot), str(target_varuna))
        shutil.copy2(str(target_crab_pot), str(target_prod_crab))
        shutil.copy2(str(target_crab_pot), str(target_root_best))
        print(f"\n[Varuna AI] Production checkpoints updated successfully:")
        print(f"  -> {target_prod_crab}")
        print(f"  -> {target_varuna}")
        print(f"  -> {target_root_best}")
    else:
        print(f"\n[Varuna AI] Non-production run: production model weights untouched.")

    # Evaluate on held-out validation set
    print("\n" + "=" * 75)
    print(" Varuna AI: Validation Metrics on SSS Crab Pot Sonar Data")
    print("=" * 75)
    
    val_model = YOLO(str(target_crab_pot))
    val_results = val_model.val(data=str(data_yaml_path), split="val", imgsz=imgsz, verbose=True)

    p = float(val_results.box.p.mean()) if hasattr(val_results.box, "p") and val_results.box.p is not None else 0.0
    r = float(val_results.box.r.mean()) if hasattr(val_results.box, "r") and val_results.box.r is not None else 0.0
    map50 = float(val_results.box.map50)
    map50_95 = float(val_results.box.map)

    print(f"\nValidation Box Precision : {p:.4f}")
    print(f"Validation Box Recall    : {r:.4f}")
    print(f"Validation Box mAP@50    : {map50:.4f}")
    print(f"Validation Box mAP@50-95 : {map50_95:.4f}")
    print("=" * 75)

    return {
        "status": "success",
        "precision": p,
        "recall": r,
        "map50": map50,
        "map50_95": map50_95,
        "model_path": str(target_crab_pot)
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train YOLOv8 on PINGEcosystem Crab Pot SSS Dataset")
    parser.add_argument("--epochs", type=int, default=5, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image resolution")
    parser.add_argument("--export-production", action="store_true", help="Explicitly export trained weights to production locations")
    args = parser.parse_args()

    train_crab_pot_sonar_detector(
        epochs=args.epochs,
        batch_size=args.batch,
        imgsz=args.imgsz,
        export_to_production=args.export_production
    )
