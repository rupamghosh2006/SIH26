"""
YOLOv8 Fine-Tuning Script on Forward-Looking Sonar (FLS) Marine Debris Dataset.
Trains YOLOv8 nano detector on 8 marine debris categories,
evaluates on held-out sonar validation split, and exports weights.
"""

import os
import shutil
import argparse
from pathlib import Path
from typing import Dict, Any
from ultralytics import YOLO


def train_fls_sonar_detector(
    data_yaml: str = "backend/data/fls_marine_debris_yolo/data.yaml",
    models_dir: str = "backend/models",
    epochs: int = 5,
    batch_size: int = 16,
    imgsz: int = 384,
    base_model: str = "yolov8n.pt"
) -> Dict[str, Any]:
    models_path = Path(models_dir)
    models_path.mkdir(parents=True, exist_ok=True)

    print("=" * 75)
    print(" Varuna AI: YOLOv8 Sonar Marine Debris Detector Training")
    print(f" Dataset YAML : {data_yaml}")
    print(f" Base Weights : {base_model}")
    print(f" Parameters   : Epochs={epochs}, Batch={batch_size}, ImgSize={imgsz}x{imgsz}")
    print("=" * 75)

    if not os.path.exists(data_yaml):
        raise FileNotFoundError(f"data.yaml not found at {data_yaml}")

    # Initialize model
    print(f"\n[Varuna AI] Loading base model backbone: {base_model}...")
    model = YOLO(base_model)

    project_dir = os.path.join("backend", "runs", "train")
    run_name = "varuna_fls_marine_debris"

    # Train
    print(f"\n[Varuna AI] Launching training...")
    results = model.train(
        data=data_yaml,
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

    # Export to application target locations
    target_varuna = models_path / "yolov8_varuna.pt"
    target_seaguard = models_path / "yolov8_seaguard.pt"
    target_root_best = Path("best.pt")

    if source_pt.exists():
        shutil.copy2(str(source_pt), str(target_varuna))
        shutil.copy2(str(source_pt), str(target_seaguard))
        shutil.copy2(str(source_pt), str(target_root_best))
        print(f"\n[Varuna AI] Checkpoints exported successfully:")
        print(f"  -> {target_varuna}")
        print(f"  -> {target_seaguard}")
        print(f"  -> {target_root_best}")
    else:
        model.save(str(target_varuna))
        shutil.copy2(str(target_varuna), str(target_seaguard))
        shutil.copy2(str(target_varuna), str(target_root_best))

    # Evaluate on held-out validation set
    print("\n" + "=" * 75)
    print(" Varuna AI: Validation Metrics Evaluation on Sonar Imagery")
    print("=" * 75)
    
    val_model = YOLO(str(target_varuna))
    val_results = val_model.val(data=data_yaml, split="val", imgsz=imgsz, verbose=True)

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
        "model_path": str(target_varuna),
        "precision": p,
        "recall": r,
        "map50": map50,
        "map50_95": map50_95
    }


def main():
    parser = argparse.ArgumentParser(description="Train YOLOv8 Sonar Marine Debris Detector")
    parser.add_argument("--data", type=str, default="backend/data/fls_marine_debris_yolo/data.yaml")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--imgsz", type=int, default=384)
    parser.add_argument("--base", type=str, default="yolov8n.pt")
    parser.add_argument("--models", type=str, default="backend/models")
    args = parser.parse_args()

    train_fls_sonar_detector(
        data_yaml=args.data,
        models_dir=args.models,
        epochs=args.epochs,
        batch_size=args.batch,
        imgsz=args.imgsz,
        base_model=args.base
    )


if __name__ == "__main__":
    main()
