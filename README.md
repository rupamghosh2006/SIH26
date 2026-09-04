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

## 3. Institutional Attribution and Development Team

- **Institution:** Netaji Subhash Engineering College (NSEC), Kolkata, West Bengal, India
- **Address:** Techno City, Garia, Kolkata, West Bengal 700152, India
- **Lead Developers:**
  - **Rupam Ghosh** ([@rupamghosh2006](https://github.com/rupamghosh2006)) | Email: [rupamgh32@gmail.com](mailto:rupamgh32@gmail.com)
  - **[BDutta18](https://github.com/BDutta18)** | Email: [workwithbd18@gmail.com](mailto:workwithbd18@gmail.com) | Phone: `+91 8967722448`
- **Target Agency:** Ministry of Earth Sciences (MoES), Government of India
- **Problem Statement ID:** SIH26057

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

| Class ID | Category Name | Acoustic Characteristics | Ecological Risk Level |
| :---: | :--- | :--- | :---: |
| `0` | **Ghost Net (ALDFG)** | High acoustic backscatter with entangled, diffuse cast shadows | Critical Risk |
| `1` | **Fishing Gear and Lines** | Linear cordage, longlines, buoy ropes, anchor cables | High Risk |
| `2` | **Rubber Tires** | Circular specular highlight with central void acoustic shadow | Medium Risk |
| `3` | **Containers and Drums** | Rectangular hard edges with elongated geometric cast shadows | Critical Risk |
| `4` | **Metal Debris** | Strong specular reflectance with sharp acoustic blockage | High Risk |
| `5` | **Shipwreck Fragments** | Multi-structural acoustic scatter and extensive shadow fields | Moderate Risk |
| `6` | **Rock Clusters** | Natural geological formations (Shadow-filtered to suppress false triggers) | Non-Hazardous |
| `7` | **Unknown Anomalies** | Unidentified acoustic targets flagged for human operator review | Review Required |

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

## 7. Technology Stack

- **Frontend Application:** Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS (Sonar Dark Theme), Lucide Icons, Leaflet GIS, Recharts.
- **Backend API & Microservices:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy ORM, SQLite / PostgreSQL, Pydantic v2.
- **AI and Computer Vision:** Ultralytics YOLOv8, PyTorch, Torchvision, ONNX Runtime, OpenCV, SciPy, NumPy, scikit-image.
- **Hardware Integration Support:** NVIDIA Jetson Orin / Nano edge deployment modules, ESP32-CAM telemetry stream emulation.
- **Packaging & Deployment:** Docker, Docker Compose, Gunicorn, Uvicorn.

---

## 8. Installation and Execution Guide

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

## 9. Platform Core Modules

1. **Acoustic Sonar Enhancement Lab (`/cnn`)**: Interactive acoustic enhancement utilizing bilateral filtering, CLAHE, and real-time contrast metrics.
2. **Debris Detection Center (`/detection`)**: Multi-scale YOLOv8 object detection with bounding boxes, confidence score tiers, and shadow length telemetry.
3. **GIS Operations Command Center (`/command-center`)**: Real-time Leaflet GIS swath mapping, GPS anomaly markers, and bathymetric depth profiles.
4. **AUV Swath Mission Planner (`/mission-planner`)**: Autonomous swath survey path optimization, grid sweeps, and telemetry waypoint routing.
5. **Ecological Risk & Drift Predictor (`/threat-prediction`)**: Hydrodynamic dispersion modeling and benthic ecosystem vulnerability index calculations.
6. **Telemetry and Hydrophone Feeds (`/comm-intercept`)**: Real-time acoustic frequency spectrum and subsea telemetry logs.
7. **Audit & Report Export**: Automated structured GeoJSON, CSV, and PDF report compilation for maritime authorities.

---

## 10. Automated Verification Suite

Run the full automated test suite verifying preprocessing, physics confidence filters, coordinate splining, and REST endpoints:

```bash
python -m pytest backend/tests
```

---

## 11. Research Contact and Inquiries

For technical evaluations, collaborative research, or institutional deployments:

- **Institutional Base:** Netaji Subhash Engineering College (NSEC), Kolkata, India
- **Lead Developers:**
  - **Rupam Ghosh:** [rupamgh32@gmail.com](mailto:rupamgh32@gmail.com) | GitHub: [@rupamghosh2006](https://github.com/rupamghosh2006)
  - **BDutta18:** [workwithbd18@gmail.com](mailto:workwithbd18@gmail.com) | Phone: `+91 8967722448` | GitHub: [@BDutta18](https://github.com/BDutta18)
- **Sponsoring Agency:** Ministry of Earth Sciences (MoES), Government of India

---

<div align="center">
  <b>VARUNA AI</b> | Autonomous Sonar Marine Debris Intelligence Platform | Ministry of Earth Sciences (MoES)
</div>
