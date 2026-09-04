# SeaGuard AI — Sonar Marine Debris Intelligence System

**SeaGuard AI** is a production-grade full-stack artificial intelligence web application designed for detecting, classifying, and geotagging man-made marine debris (**ghost nets, industrial pipes, cylinders, and shipwreck structural fragments**) in dual-channel side-scan sonar (SSS) waterfall imagery.

![SeaGuard AI Architecture](https://img.shields.io/badge/Architecture-YOLOv8%20%2B%20Physics%20Filter%20%2B%20FastAPI%20%2B%20React%2018-00F0FF?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-00FF9D?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11%2B-38BDF8?style=for-the-badge)
![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3B82F6?style=for-the-badge)

---

## 🌊 System Architecture Overview

```
                          [ Side-Scan Sonar Waterfall Survey ]
                                           │
                                           ▼
                    ┌─────────────────────────────────────────────┐
                    │       AI & CV Preprocessing Engine          │
                    │  • CLAHE Slant-Range Gain Normalization     │
                    │  • Bilateral Adaptive Speckle Filter        │
                    │  • Automated Nadir Blind-Zone Detection     │
                    │  • Overlapping 640x640 Image Tiling         │
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
                    ┌─────────────────────────────────────────────┐
                    │       Deep Neural Detection (YOLOv8)        │
                    │  • Trained on Real + Synthetic Mixed Sonar  │
                    │  • Tiled Inference & Box Coordinate Reproj  │
                    │  • Cross-Tile Non-Maximum Suppression (NMS) │
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
                    ┌─────────────────────────────────────────────┐
                    │   Physics-Based Acoustic Confidence Filter  │
                    │  • Port/Starboard Acoustic Beam Direction   │
                    │  • Highlight-to-Shadow Contrast Ratio       │
                    │  • Morphological Solidity & Hu Descriptors  │
                    │  • Suppresses No-Shadow Rock Clutter        │
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
                    ┌─────────────────────────────────────────────┐
                    │     Geospatial Interpolation Engine         │
                    │  • Navigation Ping Lat/Lon Linear Spline    │
                    │  • Across-Track Slant-Range Projection      │
                    │  • Physical Dimensions (Meters) Estimation  │
                    └──────────────────────┬──────────────────────┘
                                           │
                        ┌──────────────────┴──────────────────┐
                        ▼                                     ▼
             [ FastAPI Backend API ]               [ React 18 Web Console ]
           • SQLite Persistence via ORM          • Interactive Sonar Canvas
           • JSON / CSV Structured Reports       • Leaflet Geospatial Radar Map
           • Thumbnail Crop Service              • Synchronized Telemetry Panel
```

---

## 🛠️ Tech Stack

- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS (Dark Ocean Theme), Lucide Icons, Leaflet (Dark CartoDB tiles & clustering), Recharts (Telemetry visual analytics).
- **Backend:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy ORM, SQLite database, Pydantic v2 schemas, Aiofiles async I/O.
- **AI / CV Pipeline:** Ultralytics YOLOv8 nano detector, OpenCV, NumPy, SciPy, scikit-image, Pandas, PyTorch.
- **Packaging:** Docker, Docker Compose, Pytest test suite.

---

## 🚀 Quickstart Guide

### Option 1: Running with Docker Compose (Recommended)

Run both the frontend and backend services in isolated containers with a single command:

```bash
docker-compose up --build
```

- **Web Frontend:** Open [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation & Swagger:** Open [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Option 2: Running Locally without Docker

#### 1. Backend Setup

```bash
# In project root
python -m pip install -r backend/requirements.txt

# Start the FastAPI backend
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```

The backend will start at `http://127.0.0.1:8000`.

#### 2. Frontend Setup

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend development server will launch at `http://localhost:5173`.

---

## 🎯 Exploring the Application (1-Click Demo)

SeaGuard AI includes a built-in instant demonstration generator:

1. Open the web interface at `http://localhost:5173` (or `http://localhost:3000`).
2. Click **"Instant Demo Survey"** or click **"Upload Survey" → "Monterey Canyon Survey"**.
3. The system generates realistic synthetic side-scan sonar waterfall imagery with physics-aligned acoustic cast shadows, runs the full AI detection pipeline, interpolates GPS coordinates, and opens the interactive review screen!
4. You can also upload your own images from `backend/sample_data/`:
   - Sonar Image: `backend/sample_data/sample_coastal_survey.jpg`
   - Navigation Track: `backend/sample_data/sample_coastal_nav.csv`

---

## 🌊 Real-World Public Sonar Datasets Integration

SeaGuard AI natively integrates two prominent real-world side-scan sonar datasets alongside its physics-based synthetic generator:

### 1. AI4Shipwrecks Dataset
- **Description:** 286 real high-resolution side-scan sonar images with pixel-wise shipwreck segmentation masks collected by AUV in Thunder Bay National Marine Sanctuary.
- **Target Folder:** `backend/data/real/ai4shipwrecks/`
  - `images/`: `.png` / `.jpg` waterfall imagery
  - `labels/`: `.png` binary segmentation masks (0 = background, 1/255 = shipwreck)
- **Conversion:** Bounding boxes are derived from connected component analysis of the binary masks.
- **Downloader:** `python -m ai_pipeline.datasets.download_ai4shipwrecks`

### 2. NOMBO/MILCO Sonar Dataset
- **Description:** 1,170 real AUV side-scan sonar images distinguishing Mine-Like Objects (MILCO) from Non-Mine Bottom Objects (NOMBO).
- **Target Folder:** `backend/data/real/nombo_milco/`
  - `images/`: `.jpg` sonar images
  - `labels/`: `.txt` annotation files
- **Mapping:** MILCO is mapped to `pipe_or_cylinder` (class 1) and NOMBO to `unknown_anomaly` (class 3).
- **Downloader:** `python -m ai_pipeline.datasets.download_nombo_milco`

### 3. Unified Class Taxonomy

| Class ID | Class Name | Sources |
| :---: | :--- | :--- |
| `0` | `shipwreck` | AI4Shipwrecks (masks) + Synthetic Wrecks |
| `1` | `pipe_or_cylinder` | NOMBO/MILCO (MILCO) + Synthetic Pipes |
| `2` | `net_or_entangled_debris` | Synthetic Ghost Nets |
| `3` | `unknown_anomaly` | NOMBO/MILCO (NOMBO Seabed Clutter) |

---

## 🔬 Dataset Conversion & Mixed Training

### 1. Run Unified YOLO Dataset Conversion
```bash
python -m ai_pipeline.datasets.convert_to_yolo
```
This merges real and synthetic datasets into `backend/data/unified_sonar/`, generating `data.yaml` and `classes.yaml`.

### 2. Run Mixed Real + Synthetic Training with Real-Only Validation
```bash
python -m ai_pipeline.train --data-mix mixed --val-split real_only --epochs 12 --batch 16
```
- **`--data-mix mixed`**: Combines real AUV sonar imagery with synthetic data, balanced per class so synthetic imagery does not overwhelm the real acoustic signal.
- **`--val-split real_only`**: Strictly reserves held-out **real** sonar images for validation, ensuring that precision, recall, and mAP@50 metrics measure real-world performance.
- **`--data-mix synthetic`**: Fallback mode for pure synthetic training when real data is not present.

The trained checkpoint is saved directly to `backend/models/yolov8_seaguard.pt`.

---

## 📜 Dataset Licenses & Academic Citations

If using SeaGuard AI in academic publications, research, or public demonstrations, please cite the following original datasets:

1. **AI4Shipwrecks:**
   ```bibtex
   @dataset{ai4shipwrecks,
     author = {University of Michigan Field Robotics Group},
     title = {AI4Shipwrecks: High-Resolution Side-Scan Sonar Dataset for Shipwreck Segmentation},
     publisher = {Deep Blue Data, University of Michigan},
     doi = {10.7302/8623-hz41},
     url = {https://deepblue.lib.umich.edu/data/concern/data_sets/8623hz41x}
   }
   ```

2. **NOMBO/MILCO Sonar Dataset:**
   ```bibtex
   @article{nombo_milco_2024,
     title = {Mine-Like and Non-Mine Bottom Object Detection in Side-Scan Sonar Imagery},
     journal = {Sensors / PMC},
     year = {2024},
     pmid = {PMC10879765},
     url = {https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10879765/}
   }
   ```

---

## 🔬 Classical Physics-Based Acoustic Confidence Filter

In side-scan sonar, brightness alone does not guarantee a valid 3D structure on the seafloor — flat rock clutter and high backscatter gravel patches often produce false positive neural network triggers.

SeaGuard AI implements a classical **physics-based acoustic filter** (`backend/ai_pipeline/confidence_filter.py`) that executes before finalizing detection confidence:

$$\text{Final Score} = 0.50 \cdot \text{YOLO Score} + 0.35 \cdot \text{Shadow Consistency} + 0.15 \cdot \text{Morphological Shape}$$

- **Shadow Consistency:** Checks if the expected acoustic shadow zone behind the highlight (oriented away from nadir) exhibits a significant drop in backscatter relative to local ambient background.
- **Directional Verification:** Verifies that the acoustic shadow is positioned along the correct radial vector away from the nadir line.
- **Heavy Suppression:** If an object lacks an acoustic cast shadow (e.g., flat rock cluster or noise anomaly), the confidence score is **heavily suppressed ($\times 0.48$)**, demoting it to the **Low Tier ($<45\%$)**.
- **Tier Classification:**
  - 🟢 **High Tier:** Score $\ge 75\%$ (Strong neural confidence + verified acoustic shadow).
  - 🟡 **Medium Tier:** $45\% \le \text{Score} < 75\%$.
  - 🔴 **Low Tier:** Score $< 45\%$ (Suppressed clutter or low detector confidence).

---

## 📡 REST API Reference

### Survey Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/surveys/upload` | Uploads sonar image (`image_file`) and optional navigation GPS CSV/JSON (`metadata_file`). |
| `POST` | `/api/surveys/{id}/process` | Runs async preprocessing, tiled YOLO detection, physics filtering, and geotagging. |
| `GET` | `/api/surveys` | Lists all surveys with status (`uploaded`, `processing`, `done`, `failed`) and tier counts. |
| `GET` | `/api/surveys/{id}` | Detailed survey record with resolution, nadir position, and detection array. |
| `GET` | `/api/surveys/{id}/detections` | Query detections with filters (`min_confidence`, `tier`, `predicted_class`). |
| `GET` | `/api/surveys/{id}/report?format=json\|csv` | Downloads structured survey report. |
| `DELETE` | `/api/surveys/{id}` | Removes survey, detections, and associated thumbnail artifacts from disk. |
| `POST` | `/api/surveys/demo/create` | 1-click synthetic demo mission generator. |
| `GET` | `/api/health` | Diagnostics and model checkpoint verification. |

### Downloadable Report Schema (CSV & JSON)

```csv
detection_id,survey_id,ping_index,latitude,longitude,depth_m,bbox_x,bbox_y,bbox_width,bbox_height,estimated_size_m,predicted_class,confidence_score,confidence_tier,timestamp,source_file
```

---

## 🧪 Running the Pytest Test Suite

Execute the complete 16-test suite verifying preprocessing, physics confidence filters, rock cluster suppression, dataset conversion, geotagging, and FastAPI endpoints:

```bash
python -m pytest backend/tests
```

```
============================== 16 passed in 10.45s ==============================
```
