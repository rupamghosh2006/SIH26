# VARUNA AI — Model Benchmarks, Datasets & AI Specifications

> **Single Source of Truth** for all artificial intelligence benchmarks, neural network metrics, dataset splits, and validation results across the VARUNA AI platform.

---

## 1. Overview of Neural Architectures

| Model Architecture | Task Scope | Checkpoint Path | Status | Input Sensor Format |
| :--- | :--- | :--- | :---: | :--- |
| **YOLOv8 Nano (Fine-Tuned)** | Multi-Class Hazard Object Detection | [`backend/models/yolov8_varuna_active.pt`](../backend/models/yolov8_varuna_active.pt) | **Production Active** | Dual-Channel Side-Scan Sonar (SSS) |
| **PyTorch U-Net** | Ghost Net (ALDFG) Semantic Contour Segmentation | [`backend/models/unet_ghostnet.pt`](../backend/models/unet_ghostnet.pt) | **Production Active** | Tiled Sonar Crops (640×640) |
| **Haralick GLCM + 2D FFT** | Seabed Facies & Geological Clutter Rejection | Pure Algorithmic (`backend/ai_pipeline/seabed_classifier.py`) | **Production Active** | Bounding Box Local Region |
| **YOLOv8 Nano (FLS)** | 8-Class Marine Debris Detection | [`backend/models/yolov8_varuna.pt`](../backend/models/yolov8_varuna.pt) / `best.pt` | **Legacy / Alternate (Non-Production)** | Forward-Looking Sonar (FLS) |

---

## 2. Active Production Model: YOLOv8 SSS Debris & Hazard Detector

### A. Model Overview
The active production detector ([`backend/models/yolov8_varuna_active.pt`](../backend/models/yolov8_varuna_active.pt)) is an anchor-free convolutional network fine-tuned specifically for automated Side-Scan Sonar (SSS) acoustic waterfall imagery. It detects 4 primary debris and navigation hazard classes:
1. `shipwreck`
2. `pipe_or_cylinder`
3. `net_or_entangled_debris`
4. `unknown_anomaly`

### B. Dataset Composition & Split Integrity
- **Unified Dataset Location:** [`backend/data/unified_sonar/`](../backend/data/unified_sonar/)
- **Split Breakdown:** 297 training images, 74 validation images (371 total captures).
- **Split Leakage:** **0.0% overlap** (strictly held-out validation set with zero train/validation identity leakage).
- **Data Provenance:**
  - *Real Hydrographic Acoustic Sonar:* `shipwreck` instances are sourced from real subsea AUV survey captures (**AI4Shipwrecks**). `pipe_or_cylinder` and `unknown_anomaly` instances are sourced from real seabed sonar survey logs (**NOMBO/MILCO**).
  - *Procedural Physics Synthetic Sonar:* Due to the near-total absence of open-source real acoustic SSS records of derelict ghost nets, all 275 instances of `net_or_entangled_debris` are trained and validated using physics-modeled synthetic sonar waterfalls generated with Rayleigh-distributed acoustic backscatter, specular reflection geometry, and nadir-aligned cast shadows.
- **Live Demo Benchmark Images:** [`public/sample-sonar/`](../public/sample-sonar/) contains 7 curated benchmark captures (`ghost_net_sample_sss_01/02`, `shipwreck_sample_sss_01/02`, `pipe_cylinder_sample_sss_01/02`, and `multi_debris_field_sample_01`) held out with **zero hash overlap** against training and validation splits.

### C. Verified Validation Benchmark Metrics (Clean Split — Zero Leakage)

| Overall Metric | Validation Score | Evaluation Condition |
| :--- | :---: | :--- |
| **mAP@50** | **95.90%** | Standard IoU threshold 0.50 on held-out clean validation split |
| **mAP@50-95** | **85.20%** | Comprehensive multi-IoU localization threshold ($[0.50 : 0.95]$) |
| **Box Precision (P)** | **86.70%** | Low false-alarm rate across complex seabed backgrounds |
| **Box Recall (R)** | **91.81%** | Target capture rate across 219 validation ground-truth instances |

### D. Per-Class Detection Performance & Data Provenance Breakdown

| Class Category | Precision (P) | Recall (R) | mAP@50 | mAP@50-95 | Ground-Truth Validation Data Source |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`shipwreck`** | 80.6% | 83.8% | **88.5%** | **76.7%** | **Real** (AI4Shipwrecks held-out acoustic AUV sonar) |
| **`pipe_or_cylinder`** | 100.0% | 84.9% | **98.0%** | **91.4%** | **Real** (NOMBO/MILCO held-out acoustic sonar) |
| **`net_or_entangled_debris`** | 85.4% | 98.5% | **97.6%** | **86.5%** | **100% Synthetic** (Rayleigh physics acoustic waterfalls) |
| **`unknown_anomaly`** | 80.9% | 100.0% | **99.5%** | **86.3%** | **Real** (NOMBO seabed clutter acoustic captures) |

---

## 3. Legacy / Alternate Model: FLS Marine Debris Detector (Not in Production)

> [!WARNING]
> **Non-Production Status:** This model was trained on the Forward-Looking Sonar (FLS) Marine Debris Dataset. It is retained in the repository ([`backend/models/yolov8_varuna.pt`](../backend/models/yolov8_varuna.pt) and `best.pt`) for comparative research, but is **NOT the active production model**. Forward-Looking Sonar operates with forward sector geometry rather than downward/lateral side-scan geometry, and therefore does not produce the cross-track acoustic cast shadows essential for VARUNA AI's physics verification pipeline. Its metrics must not be conflated with the active production system.

### A. Dataset & Training Configuration
- **Dataset:** Forward-Looking Sonar (FLS) Marine Debris Dataset ([Valdenegro-Toro / Kaggle](https://www.kaggle.com/datasets/era2730/forward-looking-sonar-marine-debris-dataset))
- **Total Captures:** 1,868 acoustic sonar images across 8 debris classes
- **Validation Split:** 373 held-out real acoustic sonar images (20% split)
- **Data Ingestion Script:** [`backend/ai_pipeline/datasets/convert_fls_dataset.py`](../backend/ai_pipeline/datasets/convert_fls_dataset.py)
- **Training Script:** [`backend/ai_pipeline/train_fls_yolo.py`](../backend/ai_pipeline/train_fls_yolo.py)

### B. Legacy FLS Validation Benchmark Metrics

| Overall Metric | Validation Score |
| :--- | :---: |
| **Box Precision (P)** | **92.12%** |
| **Box Recall (R)** | **88.35%** |
| **mAP@50** | **92.17%** |
| **mAP@50-95** | **65.91%** |

### C. Legacy FLS Per-Class Breakdown (mAP@50)

| Class Category | Test Instances | mAP@50 | Ecological Priority |
| :--- | :---: | :---: | :---: |
| **`chain_or_debris`** | 65 | **99.0%** | Critical (Entanglement / ALDFG) |
| **`hook`** | 22 | **97.5%** | High (Longline hazard) |
| **`bottle_or_container`** | 195 | **97.1%** | Medium (Microplastic source) |
| **`tire`** | 109 | **96.9%** | Medium (Rubber benthic debris) |
| **`wall_boundary`** | 204 | **95.8%** | Low (Structural seabed wall) |
| **`valve`** | 56 | **92.1%** | High (Subsea pipeline fittings) |
| **`propeller`** | 35 | **83.1%** | High (Lost propulsion hardware) |
| **`can`** | 58 | **75.9%** | Medium (Metallic debris) |

---

## 4. Seafloor Geological Interference Classifier (Facies & Ripple Rejection)

To avoid high false-positive rates caused by natural seabed formations, VARUNA AI incorporates a texture and spatial-frequency analyzer ([`backend/ai_pipeline/seabed_classifier.py`](../backend/ai_pipeline/seabed_classifier.py)):

### A. Algorithmic Foundation
- **Haralick GLCM (Grey-Level Co-occurrence Matrix):** Computes contrast, dissimilarity, homogeneity, energy, and correlation across four spatial angles ($0^\circ, 45^\circ, 90^\circ, 135^\circ$).
- **2D Fast Fourier Transform (FFT):** Identifies sharp periodic energy spikes characteristic of recurring sediment bedforms (sand ripples).

### B. Geological Facies Rejection Benchmarks

| Seabed Facies | Dominant Acoustic Texture Profile | False-Alarm Penalty | Rejection Action |
| :--- | :--- | :---: | :--- |
| **Sand Ripples** | Strong periodic spatial harmonic peaks in 2D FFT | **-35%** | Suppressed as periodic sediment bedform |
| **Rocky Reef / Boulders** | High backscatter contrast, zero geometric shadow regularity | **-45%** | Demoted unless 3D acoustic cast shadow verified |
| **Smooth Mud / Silt** | High homogeneity, low acoustic backscatter | **0%** | Clear acoustic background (optimal target contrast) |
| **Flat Sand** | Uniform reverberation, zero periodic peaks | **0%** | Planar seabed reference baseline |

---

## 5. Architectural Integrity Note on Purged / Historical Experiments

In accordance with rigorous scientific transparency:
- **60-Band Sonar Frequency MLP:** An early experimental classifier trained on the UCI Connectionist Bench Sonar Mines vs. Rocks dataset was evaluated in exploratory phases. Because real-world side-scan sonar waterfall data consists of 2D spatial acoustic backscatter maps rather than 60-band beamformed spectrum vectors, this standalone MLP was explicitly removed from the production pipeline in commit `480b363`.
- **Grad-CAM Heatmaps:** Feature attribution via Grad-CAM was evaluated conceptually in early project presentations, but is not implemented in the active application. In side-scan sonar hydrography, classical physics-guided acoustic ray-tracing (highlight, shadow length, and towfish altitude) provides deterministic, auditable explainability that outperforms heuristic gradient heatmaps.
- **Current Single Source of Truth:** Only the 4-class SSS YOLOv8 detector, the PyTorch U-Net segmenter, and the Haralick/FFT seabed facies analyzer represent the active, verified AI components of VARUNA AI.
