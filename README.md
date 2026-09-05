<div align="center">

<img src="./public/logos/varuna-logo.png" alt="Varuna AI Logo" width="180" style="background-color: #ffffff; padding: 10px; border-radius: 50%; border: 3px solid #00F0FF; box-shadow: 0 0 35px rgba(0, 240, 255, 0.5); margin-bottom: 14px;" />

# VARUNA AI
### AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar Imagery
#### Smart India Hackathon (SIH 2026) | Problem Statement ID: SIH26057

[![Ministry](https://img.shields.io/badge/Ministry-Ministry%20of%20Earth%20Sciences%20(MoES)-00F0FF?style=for-the-badge&logo=shield)](https://www.moes.gov.in/)
[![SIH Problem](https://img.shields.io/badge/SIH%202026-SIH26057-00FF9D?style=for-the-badge)](https://www.sih.gov.in/)
[![Framework](https://img.shields.io/badge/Next.js-14%20App%20Router-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![Backend](https://img.shields.io/badge/FastAPI-Python%203.11%2B-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![AI Engine](https://img.shields.io/badge/YOLOv8-Computer%20Vision%20%2B%20U--Net-FF3864?style=for-the-badge&logo=pytorch)](https://ultralytics.com/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

</div>

---

## 1. Problem Statement and Background

The accumulation of anthropogenic debris across marine ecosystems represents an escalating ecological and operational hazard. Among the most damaging forms of pollution are Abandoned, Lost, or Discarded Fishing Gear (ALDFG), commonly designated as "Ghost Nets". These high-tensile synthetic nets persistently trap and destroy marine organisms through unmonitored ghost fishing, suffocate coral reef architectures, and entangle commercial vessel shafts as well as Autonomous Underwater Vehicle (AUV) thrusters.

To survey large benthic expanses, marine researchers and hydrographic survey teams rely on dual-channel Side-Scan Sonar (SSS) instruments towed behind survey vessels or mounted on autonomous subsea platforms.

### Primary Operational Constraints
1. **Inspection Bottlenecks:** Manual examination of thousands of linear kilometers of acoustic waterfall imagery is labor-intensive and operationally slow.
2. **Operator Fatigue:** Acoustic log analysis over prolonged periods in low-contrast environments increases false negative rates.
3. **Seabed Acoustic Interference:** Complex natural seabed geology (sand ripples, bedforms, and boulder clusters) generates significant acoustic backscatter that mimics artificial debris.

---

## 2. Executive Overview

**VARUNA AI** is an automated deep-ocean acoustic intelligence platform engineered for **SIH26057** under the auspices of the **Ministry of Earth Sciences (MoES), Government of India**.

The platform ingests raw dual-channel side-scan sonar waterfall logs, applies automated CLAHE gain equalization and bilateral speckle filtering, detects 8 distinct categories of underwater debris using fine-tuned **YOLOv8 and U-Net architectures**, cross-validates detections via **physics-based acoustic cast shadow verification**, and generates georeferenced audit reports with GPS coordinate projections.

---

## 3. Institutional Attribution and Project Details

| Entity / Property | Details |
| :--- | :--- |
| **Host Institution** | Netaji Subhash Engineering College (NSEC), Kolkata, West Bengal, India |
| **Campus Address** | Techno City, Garia, Kolkata, West Bengal 700152, India |
| **Sponsoring Body** | Ministry of Earth Sciences (MoES), Government of India |
| **Problem Statement** | SIH26057: AI-Powered Automated Underwater Marine Debris & Anomaly Detection |

### Development Team

| Name | Role | GitHub Profile | Email Address |
| :--- | :--- | :--- | :--- |
| **Bodhisatwa Dutta** | Lead Developer | [@BDutta18](https://github.com/BDutta18) | [workwithbd18@gmail.com](mailto:workwithbd18@gmail.com) |
| **Rupam Ghosh** | Lead Developer | [@rupamghosh2006](https://github.com/rupamghosh2006) | [rupamgh32@gmail.com](mailto:rupamgh32@gmail.com) |

---

## 4. System Architecture and Processing Pipeline

```
                             [ Raw SSS Waterfall Sonar Stream / Files ]
                                                 │
                                                 ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │          STAGE 1: Acoustic Preprocessing Lab           │
                    │  • CLAHE Slant-Range Gain and Contrast Normalization     │
                    │  • Adaptive Bilateral Speckle Noise Reduction           │
                    │  • Automatic Nadir Blind-Zone Isolation (Port/Starboard)│
                    │  • Overlapping 640x640 Sonar Waterfall Patch Tiling     │
                    └────────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │          STAGE 2: Deep Learning Neural Detector         │
                    │  • YOLOv8 Nano and Medium Sonar Inference               │
                    │  • Semantic U-Net Contour Segmentation for Ghost Nets   │
                    │  • Multi-Tile Coordinate Reprojection & Cross-Tile NMS  │
                    └────────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │     STAGE 3: Physics-Based Acoustic Shadow Validator    │
                    │  • Radial Offset Calculation along Sonar Beam Angle     │
                    │  • Highlight-to-Shadow Contrast Ratio Analysis          │
                    │  • Morphological Solidity and Hu Moments Computation    │
                    │  • 0.48x Confidence Demotion for Flat Seabed Clutter    │
                    └────────────────────────────┬────────────────────────────┘
                                                 │
                                                 ▼
                    ┌─────────────────────────────────────────────────────────┐
                    │         STAGE 4: Geospatial Splining & Telemetry        │
                    │  • Navigation Ping Lat/Lon Linear Spline Interpolation  │
                    │  • Across-Track Slant-Range Meter Projection            │
                    │  • Physical Dimensions (Length x Width) Estimation      │
                    │  • Benthic Ecosystem Risk Level Classification          │
                    └────────────────────────────┬────────────────────────────┘
                                                 │
                              ┌──────────────────┴──────────────────┐
                              ▼                                     ▼
                 [ FastAPI Python Backend ]             [ Next.js 14 App Router UI ]
               • High-Speed Async Processing           • Interactive Sonar Canvas Viewer
               • Edge ONNX and CUDA Inference          • Leaflet GIS Swath Map & Radars
               • Automated Inspection REST API         • Human-in-the-Loop Audit Center
```

---

## 5. Marine Debris Classification Taxonomy

VARUNA AI classifies acoustic echoes into 8 benthic hazard categories:

| Class ID | Category Name | Acoustic Characteristics | Ecological / Economic Risk |
| :---: | :--- | :--- | :---: |
| `0` | **Ghost Net (ALDFG)** | High acoustic backscatter with entangled, diffuse cast shadows | 🔴 Critical Risk |
| `1` | **Fishing Gear and Lines** | Linear cordage, longlines, buoy ropes, anchor cables | 🟠 High Risk |
| `2` | **Rubber Tires** | Circular specular highlight with central void acoustic shadow | 🟡 Medium Risk |
| `3` | **Containers and Drums** | Rectangular hard edges with elongated geometric cast shadows | 🔴 Critical Risk |
| `4` | **Metal Debris** | Strong specular reflectance with sharp acoustic blockage | 🟠 High Risk |
| `5` | **Shipwreck Fragments** | Multi-structural acoustic scatter and extensive shadow fields | 🟡 Moderate Risk |
| `6` | **Rock Clusters** | Natural geological formations (Shadow-filtered to suppress false triggers) | 🟢 Non-Hazardous |
| `7` | **Unknown Anomalies** | Unidentified acoustic targets flagged for human operator review | 🟡 Review Required |

---

## 6. Physics-Based Acoustic Shadow Validation

In side-scan sonar physics, physical three-dimensional structures protruding from the seafloor obstruct acoustic beam propagation, casting an acoustic shadow (zero backscatter region) directly behind the highlight relative to the transducer.

VARUNA AI implements a classical acoustic validation filter:

$$\text{Confidence Score} = 0.50 \cdot \mathcal{S}_{\text{YOLO}} + 0.35 \cdot \mathcal{S}_{\text{Shadow}} + 0.15 \cdot \mathcal{S}_{\text{Morphology}}$$

1. **Directional Vector Alignment:** Confirms that the shadow region is positioned radially away from the central nadir track line.
2. **Backscatter Intensity Differential:** Measures the contrast ratio between the highlight echo and the shadow floor relative to the local ambient seabed background.
3. **Clutter Suppression:** Highlight detections lacking an acoustic shadow (such as flat seabed mineral deposits) are penalized with a `0.48x` multiplier, safely demoting them to the Low Confidence Tier (`<45%`).
4. **Confidence Tier Categorization:**
   - **High Tier ($\ge 75\%$):** Neural detection verified by geometric acoustic shadow.
   - **Medium Tier ($45\% - 74\%$):** Potential anomaly requiring secondary swath pass or manual verification.
   - **Low Tier ($< 45\%$):** Suppressed geological clutter or low detector confidence.

---

## 7. Model Training, Datasets & Benchmarks

VARUNA AI incorporates specialized acoustic intelligence models trained and evaluated on real underwater sonar datasets:

### A. YOLOv8 Side-Scan Sonar (SSS) Crab Pot & Derelict Gear Model
Trained on the **PING Ecosystem SSS Crab Pot Dataset** ([Hugging Face: `PINGEcosystem/sss-crab-pot-detection-ds`](https://huggingface.co/datasets/PINGEcosystem/sss-crab-pot-detection-ds)) containing 6,674 Side-Scan Sonar acoustic captures with axis-aligned bounding box annotations for derelict crab pots ("ghost pots" / ALDFG):

- **Ingestion & Normalizer:** [`backend/ai_pipeline/datasets/download_crab_pot_dataset.py`](backend/ai_pipeline/datasets/download_crab_pot_dataset.py)
- **Training Script:** [`backend/ai_pipeline/train_crab_pot_yolo.py`](backend/ai_pipeline/train_crab_pot_yolo.py)
- **Primary Checkpoints:** `backend/models/yolov8_crab_pot.pt`, `backend/models/yolov8_varuna.pt`, `best.pt`

```bash
# Ingest and convert Hugging Face dataset to YOLO format
python backend/ai_pipeline/datasets/download_crab_pot_dataset.py

# Launch YOLOv8 fine-tuning on real SSS imagery
python backend/ai_pipeline/train_crab_pot_yolo.py --epochs 10 --batch 16 --imgsz 640
```

---

### B. YOLOv8 Sonar Marine Debris Detection Model
Trained on the **Forward-Looking Sonar (FLS) Marine Debris Dataset** ([Valdenegro-Toro / Kaggle](https://www.kaggle.com/datasets/era2730/forward-looking-sonar-marine-debris-dataset)) containing 1,868 acoustic sonar captures across 8 benthic debris classes:

- **Converter Pipeline:** [`backend/ai_pipeline/datasets/convert_fls_dataset.py`](backend/ai_pipeline/datasets/convert_fls_dataset.py)
- **Training Script:** [`backend/ai_pipeline/train_fls_yolo.py`](backend/ai_pipeline/train_fls_yolo.py)
- **Validation Split:** 373 held-out real acoustic sonar images (20%)

#### Validation Benchmark Metrics
| Overall Metric | Validation Score |
| :--- | :---: |
| **Box Precision (P)** | **92.12%** |
| **Box Recall (R)** | **88.35%** |
| **mAP@50** | **92.17%** |
| **mAP@50-95** | **65.91%** |

#### Per-Class Detection Performance (mAP@50)
| Class Category | Instances | mAP@50 | Ecological Priority |
| :--- | :---: | :---: | :---: |
| **`chain_or_debris`** | 65 | **99.0%** | 🔴 Critical (Entanglement / ALDFG) |
| **`hook`** | 22 | **97.5%** | 🟠 High (Longline hazard) |
| **`bottle_or_container`** | 195 | **97.1%** | 🟡 Medium (Microplastic source) |
| **`tire`** | 109 | **96.9%** | 🟡 Medium (Rubber benthic debris) |
| **`wall_boundary`** | 204 | **95.8%** | 🟢 Low (Structural seabed wall) |
| **`valve`** | 56 | **92.1%** | 🟠 High (Subsea pipeline fittings) |
| **`propeller`** | 35 | **83.1%** | 🟠 High (Lost propulsion hardware) |
| **`can`** | 58 | **75.9%** | 🟡 Medium (Metallic debris) |

- **Primary Checkpoints:** `backend/models/yolov8_varuna.pt`, `best.pt`, and `backend/models/yolov8_seaguard.pt`.

---

### C. Acoustic Signal Target Classifier (Mines vs. Rocks)
Trained on the **Sonar Mines vs. Rocks Dataset** ([Connectionist Bench / Kaggle](https://www.kaggle.com/datasets/mattcarter865/mines-vs-rocks)) consisting of 208 underwater sonar acoustic ping profiles across 60 frequency energy bands:

- **Training Script:** [`backend/ai_pipeline/train_acoustic_classifier.py`](backend/ai_pipeline/train_acoustic_classifier.py)
- **Inference Module:** [`backend/ai_pipeline/acoustic_classifier.py`](backend/ai_pipeline/acoustic_classifier.py)

#### Model Benchmark Comparison
| Architecture | Test Accuracy | F1-Score | ROC-AUC | Status |
| :--- | :---: | :---: | :---: | :---: |
| **PyTorch Deep MLP** | **85.71%** | **0.8696** | **0.9591** | 🏆 **Deployed** |
| **Logistic Regression** | **83.33%** | 0.8444 | 0.9045 | Benchmark |
| **Random Forest** | **80.95%** | 0.8261 | 0.9511 | Benchmark |

- **Deployed Checkpoints:** `backend/models/sonar_mine_rock_classifier.joblib` and `backend/models/sonar_mine_rock_mlp.pt`.

---

## 8. Technology Stack

- **Frontend Application:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS (Sonar Dark Theme), Lucide Icons, Leaflet GIS, Recharts.
- **Backend API & Microservices:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy ORM, SQLite / PostgreSQL, Pydantic v2.
- **AI and Computer Vision:** Ultralytics YOLOv8, PyTorch, Torchvision, ONNX Runtime, OpenCV, SciPy, NumPy, scikit-image.
- **Hardware Integration Support:** NVIDIA Jetson Orin / Nano edge deployment modules, ESP32-CAM telemetry stream emulation.
- **Packaging & Deployment:** Docker, Docker Compose, Gunicorn, Uvicorn.

---

## 8. Explainable Sonar Forensic Analysis

When human operators inspect underwater anomalies, understanding **WHY** a target was classified is essential. VARUNA AI features **Explainable Sonar**:

- **7-Section Forensic Breakdown:** YOLO detector confidence, physics acoustic shadow contrast, morphological shape metrics, composite math calculation, nadir acoustic propagation vector, and physical dimensions.
- **Dynamic Visual Overlay:** Direct visual demarcation of highlight reflection (cyan), expected cast shadow (orange), and nadir propagation beam on the raw sonar crop.
- **Auditable Formula:** Complete transparent display of the weighted acoustic confidence equation with individual component contributions.

---

## 9. Active Verification ("Verify Detection") & Adaptive Rescan

VARUNA AI does not blindly accept single-pass classifications when detections are uncertain. The **Active Verification** feature allows operators to request secondary acoustic evidence:

- **Uncertainty Trigger:** Automatically prompts verification on **Medium Tier ($45\% - 74\%$)** and **Low Tier ($<45\%$)** detections.
- **Adaptive Survey Geometry:** Calculates suggested cross-track CPA offset ($15\text{m} - 35\text{m}$) and orthogonal observation angle ($+45^\circ / -45^\circ$) with waypoint trajectories.
- **Tactical Rescan Swath Map:** Visualizes primary survey track vs. secondary adaptive verification swath with waypoint nodes.
- **Dual Simulation Scenarios:**
  - **Scenario A (Confirmation Pass):** Simulates orthogonal high-contrast pass confirming persistent acoustic relief $\rightarrow$ `✓ VERIFIED TARGET`.
  - **Scenario B (False Alarm Pass):** Simulates secondary pass revealing flat seabed ripple with reduced confidence $\rightarrow$ `⚠ DETECTION NOT CONFIRMED`.
- **Truth-Based Association & Evidence Comparison:** Reuses the existing detector and confidence filter without artificial confidence boosting ($\Delta \text{Conf} = \text{Secondary} - \text{Primary}$).
- **Human-in-the-Loop Actions:** Operator controls for `[ Confirm Detection ]`, `[ False Alarm ]`, and `[ Mark For ROV Review ]`.

---

## 10. Installation and Execution Guide

### Prerequisites
- Node.js 18+ (Node 20 recommended)
- Python 3.11+
- Git

### 1. Repository Setup
```bash
git clone https://github.com/rupamghosh2006/SIH26.git
cd SIH26
```

### 2. Frontend Launch
```bash
npm install
npm run dev
```
The client portal will be accessible at `http://localhost:3000`.

### 3. Backend Launch
```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 5000 --reload
```
Interactive Swagger documentation is available at `http://localhost:5000/docs`.

### 4. Containerized Execution via Docker Compose
```bash
docker-compose up --build
```

---

## 11. Platform Core Modules

1. **Acoustic Sonar Enhancement Lab (`/cnn`)**: Interactive acoustic enhancement utilizing bilateral speckle filtering, CLAHE gain equalization, and real-time contrast metrics.
2. **Debris Detection Center (`/detection`)**: Multi-scale YOLOv8 object detection with bounding boxes, confidence score tiers, Explainable Sonar, and Active Verification.
3. **GIS Operations Command Center (`/command-center`)**: Real-time Leaflet GIS swath mapping, GPS anomaly markers, and bathymetric depth profiles.
4. **Debris Registry & Watchlist (`/watchlist`)**: Catalog of detected marine anomalies, geolocation tracking, and ecological risk logs.
5. **Analytics Dashboard (`/analytics`)**: Statistical breakdown of debris distributions, benthic classification metrics, and survey audit summaries.
6. **Audit & Report Export**: Automated structured GeoJSON, CSV, and PDF report compilation for maritime authorities.

---

## 11. Automated Verification Suite

Run the full automated test suite verifying preprocessing, physics confidence filters, coordinate splining, and REST endpoints:

```bash
python -m pytest backend/tests
```

---

## 12. Research Contact and Inquiries

For technical evaluations, collaborative research, or institutional deployments:

| Developer / Entity | Role / Affiliation | GitHub Profile | Official Email |
| :--- | :--- | :--- | :--- |
| **Bodhisatwa Dutta** | Lead Developer | [@BDutta18](https://github.com/BDutta18) | [workwithbd18@gmail.com](mailto:workwithbd18@gmail.com) |
| **Rupam Ghosh** | Lead Developer | [@rupamghosh2006](https://github.com/rupamghosh2006) | [rupamgh32@gmail.com](mailto:rupamgh32@gmail.com) |
| **Netaji Subhash Engineering College** | Academic Host Institution | [nsec.ac.in](https://nsec.ac.in/) | Techno City, Garia, Kolkata, West Bengal 700152 |
| **Ministry of Earth Sciences (MoES)** | Sponsoring Authority | [moes.gov.in](https://www.moes.gov.in/) | New Delhi, India |

---

<div align="center">
  <b>VARUNA AI</b> | Autonomous Sonar Marine Debris Intelligence Platform | Ministry of Earth Sciences (MoES)
</div>
