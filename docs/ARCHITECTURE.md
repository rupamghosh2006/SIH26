# VARUNA AI — System Architecture & Technical Specifications

> **Smart India Hackathon (SIH 2026) | Problem Statement ID: SIH26057**  
> **Sponsoring Authority:** Ministry of Earth Sciences (MoES), Government of India  
> **Host Institution:** Netaji Subhash Engineering College (NSEC), Kolkata

---

## 1. End-to-End System Processing Pipeline

VARUNA AI ingests raw dual-channel side-scan sonar (SSS) acoustic waterfall logs, applies sensor-specific acoustic normalization, executes deep-learning object detection, validates detections via physics-based acoustic shadow geometry, and projects georeferenced anomaly coordinates onto an interactive GIS swath map.

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
                    │  • YOLOv8 SSS Neural Detection (Active 4-Class Model)   │
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
                    │  • 3D Acoustic Relief Height Calculation (H = h·Ls/(Rs+Ls))
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
                • High-Speed Async Microservices        • Interactive Sonar Canvas Viewer
                • PyTorch & ONNX Pipeline Engine        • Leaflet GIS Swath Map & Radars
                • Automated Inspection REST API         • Human-in-the-Loop Audit Center
```

---

## 2. Marine Debris Classification Taxonomy

### A. Active Production Model (Side-Scan Sonar — 4 Classes)

The live production detector ([`backend/models/yolov8_varuna_active.pt`](../backend/models/yolov8_varuna_active.pt)) is specifically trained for dual-channel Side-Scan Sonar (SSS) waterfall logs across 4 verified debris and navigation hazard categories:

| Class ID | Category Name | Key Acoustic Characteristics | Ecological & Operational Risk |
| :---: | :--- | :--- | :---: |
| `0` | **`shipwreck`** | Multi-structural specular highlights with extensive acoustic cast shadows and structural relief. | High Navigational Hazard |
| `1` | **`pipe_or_cylinder`** | Elongated high-reflectance linear highlights accompanied by parallel acoustic shadows; characteristic of subsea pipelines, discarded drums, and cylindrical ordnance. | High Infrastructure Risk |
| `2` | **`net_or_entangled_debris`** | Diffuse, irregular acoustic backscatter webbing with complex non-geometric cast shadows indicative of ALDFG (ghost nets) smothering benthic topography. | Critical Ecological Hazard |
| `3` | **`unknown_anomaly`** | High-contrast acoustic anomalies that do not match canonical debris geometries, flagged for human hydrographer inspection. | Operator Review Required |

### B. Legacy / Alternate Model (Forward-Looking Sonar — 8 Classes, Not in Production)

An earlier iteration of the project evaluated an 8-class taxonomy on Forward-Looking Sonar (FLS) acoustic captures ([`backend/ai_pipeline/datasets/convert_fls_dataset.py`](../backend/ai_pipeline/datasets/convert_fls_dataset.py)):

| Class ID | Category Name | Sensor Geometry | Production Status |
| :---: | :--- | :--- | :---: |
| `0` | `tire` | Forward-Looking Sonar (FLS) | Inactive (Experimental) |
| `1` | `bottle_or_container` | Forward-Looking Sonar (FLS) | Inactive (Experimental) |
| `2` | `can` | Forward-Looking Sonar (FLS) | Inactive (Experimental) |
| `3` | `chain_or_debris` | Forward-Looking Sonar (FLS) | Inactive (Experimental) |
| `4` | `propeller` | Forward-Looking Sonar (FLS) | Inactive (Experimental) |
| `5` | `valve` | Forward-Looking Sonar (FLS) | Inactive (Experimental) |
| `6` | `hook` | Forward-Looking Sonar (FLS) | Inactive (Experimental) |
| `7` | `wall_boundary` | Forward-Looking Sonar (FLS) | Inactive (Experimental) |

> [!IMPORTANT]
> **Operational Distinction:** Forward-Looking Sonar (FLS) looks ahead horizontally across a narrow sector, whereas Side-Scan Sonar (SSS) scans downward and laterally across wide port/starboard benthic swaths. Because FLS geometry does not produce standard cross-track acoustic cast shadows or slant-range geometry, the 8-class FLS model was replaced with the 4-class SSS production checkpoint (`yolov8_varuna_active.pt`) for real survey workflows. For complete benchmark metrics on both models, see [docs/AI_BENCHMARK.md](AI_BENCHMARK.md).

---

## 3. Physics-Based Acoustic Shadow Validation

In side-scan sonar hydrography, three-dimensional solid obstacles protruding above the seafloor obstruct acoustic beam propagation, casting an acoustic shadow (zero-backscatter zone) directly behind the object relative to the sonar towfish trajectory.

VARUNA AI implements a deterministic acoustic validation filter ([`backend/ai_pipeline/confidence_filter.py`](../backend/ai_pipeline/confidence_filter.py)):

### Acoustic Confidence Composite Equation

$$\text{Confidence Score} = 0.50 \cdot \mathcal{S}_{\text{YOLO}} + 0.35 \cdot \mathcal{S}_{\text{Shadow}} + 0.15 \cdot \mathcal{S}_{\text{Morphology}}$$

Where:
- $\mathcal{S}_{\text{YOLO}} \in [0, 1]$: Raw bounding-box confidence output from the YOLOv8 neural detector.
- $\mathcal{S}_{\text{Shadow}} \in [0, 1]$: Normalized contrast ratio between the specular highlight and the acoustic cast shadow floor relative to the local background:
  $$\mathcal{S}_{\text{Shadow}} = \text{clip}\left(\frac{\mu_{\text{highlight}} - \mu_{\text{shadow}}}{\mu_{\text{background}} + \epsilon}, 0, 1\right)$$
- $\mathcal{S}_{\text{Morphology}} \in [0, 1]$: Geometric solidity and aspect ratio score derived from contour analysis.

### Protrusion Height Estimation (Acoustic Trigonometry)

For any detected target exhibiting a verified cast shadow, the target's physical vertical relief height ($H$) above the seabed is calculated from the towfish altitude ($h$), the measured acoustic shadow length ($L_s$), and the slant range to the highlight ($R_s$):

$$H = \frac{h \cdot L_s}{R_s + L_s}$$

### Clutter Suppression & Confidence Tiers

1. **Directional Vector Alignment:** Verifies that the cast shadow extends radially outward from the central nadir line along the acoustic propagation vector (starboard shadow for starboard targets; port shadow for port targets).
2. **Flat Seabed Clutter Suppression:** Highlights that lack a corresponding acoustic shadow (e.g., flat mineral deposits, sediment color variations, or seabed ripples) receive a `0.48x` penalty multiplier:
   $$\text{Confidence}_{\text{final}} = \text{Confidence}_{\text{composite}} \cdot 0.48$$
3. **Operational Confidence Tiers:**
   - **High Tier ($\ge 75\%$):** Neural detection validated by geometric cast shadow and directional alignment.
   - **Medium Tier ($45\% - 74\%$):** Candidate anomaly exhibiting weak or partial shadow; triggers the Active Verification workflow.
   - **Low Tier ($< 45\%$):** Demoted natural geological clutter or marginal detection.

---

## 4. Explainable Sonar Forensic Analysis

When hydrographers inspect underwater anomalies, understanding **WHY** an acoustic target was classified is paramount. VARUNA AI provides transparent, auditable forensic explainability ([`frontend/components/explainable-sonar-panel.tsx`](../frontend/components/explainable-sonar-panel.tsx)):

- **Multi-Factor Forensic Breakdown:** Visualizes YOLO detector confidence, physics acoustic shadow contrast, morphological shape metrics, composite math calculation, and acoustic relief height.
- **Dynamic Visual Overlays:** Visual demarcation of the specular highlight reflection (cyan), expected cast shadow region (orange), and nadir acoustic propagation beam directly on the raw sonar crop.
- **Acoustic Trigonometry Telemetry:** Displays towfish altitude, slant range, calculated acoustic shadow length, and estimated 3D object height ($H$).
- **Mathematical Formula Audit:** Full transparent display of the weighted acoustic confidence equation with individual component contributions.

---

## 5. Active Verification ("Verify Detection") & Adaptive Rescan

VARUNA AI does not rely on single-pass classifications when detections are ambiguous. The **Active Verification** engine ([`backend/ai_pipeline/active_verification.py`](../backend/ai_pipeline/active_verification.py)) enables autonomous multi-look evidence collection:

- **Uncertainty Trigger:** Automatically recommends verification for **Medium Tier ($45\% - 74\%$)** and **Low Tier ($<45\%$)** detections.
- **Adaptive Survey Geometry:** Calculates an optimal secondary survey flightpath:
  - Suggested cross-track Closest Point of Approach (CPA): $15\,\text{m} - 35\,\text{m}$ offset.
  - Orthogonal observation trajectory: $+45^\circ / -45^\circ$ heading relative to the original trackline.
- **Evidence Comparison Without Artificial Boosting:** Re-evaluates the secondary pass using the identical detector and physics confidence filter ($\Delta \text{Conf} = \text{Secondary} - \text{Primary}$), ensuring no synthetic score inflation.
- **Dual Verification Outcomes:**
  - **Confirmation Pass:** Orthogonal view confirms persistent 3D acoustic relief and cast shadow $\rightarrow$ target promoted to High Confidence.
  - **False Alarm Pass:** Secondary pass reveals flat seabed sediment with reduced shadow contrast $\rightarrow$ target demoted.
- **Human-in-the-Loop Controls:** Explicit operator actions for `Confirm Detection`, `Mark False Alarm`, and `Escalate to ROV Inspection`.

---

## 6. Technology Stack

| Layer | Component | Version / Technology | Purpose |
| :--- | :--- | :--- | :--- |
| **Frontend UI** | Next.js 14 App Router | React 18, TypeScript, Tailwind CSS | High-performance tactical dark-theme operator dashboard |
| **Mapping & GIS** | Leaflet GIS & Canvas | Leaflet.js, React-Leaflet | Real-time SSS swath coverage, trackline splining, target markers |
| **Backend API** | FastAPI | Python 3.11+, Uvicorn, Pydantic v2 | High-speed asynchronous survey ingestion and processing API |
| **Database** | SQLAlchemy ORM | SQLite (Default) / PostgreSQL ready | Relational persistence for surveys, detections, and telemetry |
| **Computer Vision** | Ultralytics YOLOv8 | PyTorch, Torchvision | Deep-learning object detection across 4 SSS hazard classes |
| **Segmentation** | Custom PyTorch U-Net | PyTorch | ALDFG (Ghost Net) semantic contour segmentation & area estimation |
| **Acoustic Physics** | OpenCV & SciPy | OpenCV 4.x, SciPy, NumPy | CLAHE gain equalization, bilateral filtering, shadow ray-tracing |
| **Geological AI** | Haralick GLCM & 2D FFT | scikit-image, NumPy | Seafloor facies analysis & periodic sand-ripple harmonic rejection |
| **Containerization** | Docker & Compose | Docker Engine 24+, Compose v2 | Multi-container deployment for frontend and backend microservices |

---

## 7. Platform Core Modules & Capabilities

1. **Acoustic Sonar Enhancement Lab (`/cnn`):** Interactive acoustic enhancement tool applying bilateral speckle filtering, CLAHE gain equalization, and side-by-side backscatter comparison.
2. **Debris Detection & Sonar Map Center (`/detection`):** Full multi-scale YOLOv8 object detection with bounding boxes, confidence tiers, Explainable Sonar forensic modals, Active Verification tools, and Leaflet GIS swath mapping.
3. **Live Benchmark Quick Select Bar (`/detection`):** Zero-configuration evaluation using 7 curated benchmark sonar waterfall captures ([`public/sample-sonar/`](../public/sample-sonar/)).
4. **Debris Registry & Watchlist (`/watchlist`):** Searchable catalog of detected marine debris targets, bathymetric depths, GPS coordinates, and ecological threat ratings.
5. **Analytics Dashboard (`/analytics`):** Real-time aggregation of survey statistics, debris class distributions, confidence tier ratios, and operational summaries.
6. **Audit & Structured Export Engine:** One-click export of survey findings into standardized GeoJSON, CSV, and formal hydrographic PDF inspection dossiers.
