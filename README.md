<div align="center">

<img src="./public/logos/varuna-logo.png" alt="Varuna Logo" width="180" style="background-color: #ffffff; padding: 10px; border-radius: 50%; border: 3px solid #00F0FF; box-shadow: 0 0 35px rgba(0, 240, 255, 0.5); margin-bottom: 14px;" />

# VARUNA
### AI-Powered Automated Underwater Marine Debris and Anomaly Detection System using Side-Scan Sonar Imagery
#### Smart India Hackathon (SIH 2026) | Problem Statement ID: SIH26057

[![Ministry](https://img.shields.io/badge/Ministry-Ministry%20of%20Earth%20Sciences%20(MoES)-00F0FF?style=for-the-badge&logo=shield)](https://www.moes.gov.in/)
[![SIH Problem](https://img.shields.io/badge/SIH%202026-SIH26057-00FF9D?style=for-the-badge)](https://www.sih.gov.in/)
[![Pitching Report](https://img.shields.io/badge/Official%20Pitch%20Report-PDF%20Download-0284C7?style=for-the-badge&logo=adobe-acrobat-reader)](./public/docs/VARUNA_AI_Pitching_Report.pdf)
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

**VARUNA** is an automated deep-ocean acoustic intelligence platform engineered for **SIH26057** under the auspices of the **Ministry of Earth Sciences (MoES), Government of India**.

The platform ingests raw dual-channel side-scan sonar waterfall logs, applies automated CLAHE gain equalization and bilateral speckle filtering, detects 4 primary categories of underwater debris and navigation hazards (`shipwreck`, `pipe_or_cylinder`, `net_or_entangled_debris`, and `unknown_anomaly`) using fine-tuned **YOLOv8 and U-Net architectures**, cross-validates detections via **physics-based acoustic cast shadow verification**, and generates georeferenced audit reports with GPS coordinate projections.

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

## 4. Documentation Index

The complete technical documentation for VARUNA is organized in dedicated reference guides:

| Document | Primary Focus | Key Contents |
| :--- | :--- | :--- |
| [**docs/ARCHITECTURE.md**](docs/ARCHITECTURE.md) | **System Architecture & Technical Specs** | Full processing pipeline, 4-class SSS production vs. 8-class FLS taxonomy, acoustic shadow trigonometry ($H = \frac{h \cdot L_s}{R_s + L_s}$), forensic explainability, adaptive rescan, and core modules. |
| [**docs/AI_BENCHMARK.md**](docs/AI_BENCHMARK.md) | **Model Benchmarks & Datasets** | Single source of truth for all AI metrics: verified clean-split YOLOv8 SSS benchmarks (**95.90% mAP@50**, **85.20% mAP@50-95**), per-class data provenance, legacy FLS model benchmarks, and Haralick GLCM / 2D FFT facies rejection. |
| [**docs/QUICKSTART.md**](docs/QUICKSTART.md) | **Setup & Execution Guide** | Prerequisites, local frontend & backend launch commands, Docker Compose execution, service health verification, demo sample workflows, and automated test instructions. |
| [**docs/SECURITY.md**](docs/SECURITY.md) | **Security & Known Limitations** | Baseline security posture, deliberate demo authentication state, FastAPI CORS configuration, secrets management via `.gitignore`, and known roadmap limitations. |

---

## 5. System Architecture & Processing Pipeline

VARUNA processes raw side-scan sonar waterfall logs through a modular four-stage pipeline: (1) acoustic preprocessing with CLAHE gain equalization and bilateral speckle filtering; (2) tiled multi-scale YOLOv8 object detection paired with PyTorch U-Net ghost net segmentation; (3) physics-based acoustic cast shadow verification with 3D relief estimation ($H = \frac{h \cdot L_s}{R_s + L_s}$); and (4) geospatial trackline splining for GPS coordinate projection.

> *For complete pipeline diagrams, ray-tracing equations, and module breakdowns, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).*

---

## 6. Marine Debris Classification Taxonomy

The live production model operates on dual-channel Side-Scan Sonar (SSS) imagery and detects 4 primary benthic hazard categories: `shipwreck` (high navigational hazard), `pipe_or_cylinder` (subsea infrastructure risk), `net_or_entangled_debris` (critical ALDFG ghost net ecological threat), and `unknown_anomaly` (flagged for hydrographer review). An earlier 8-class taxonomy evaluated on Forward-Looking Sonar (FLS) is retained for research comparison but is not part of the active production pipeline due to sensor geometry differences.

> *For the full taxonomy table and sensor geometry distinctions, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#2-marine-debris-classification-taxonomy).*

---

## 7. Physics-Based Acoustic Shadow Validation

To suppress false alarms from natural seabed topography and planar mineral deposits, VARUNA implements a deterministic acoustic shadow validation filter:

$$\text{Confidence Score} = 0.50 \cdot \mathcal{S}_{\text{YOLO}} + 0.35 \cdot \mathcal{S}_{\text{Shadow}} + 0.15 \cdot \mathcal{S}_{\text{Morphology}}$$

Targets lacking a verifiable acoustic cast shadow receive a `0.48x` penalty multiplier, safely demoting planar geological clutter to the Low Confidence Tier ($<45\%$), while verified 3D protrusions are categorized into High ($\ge 75\%$) or Medium ($45\% - 74\%$) tiers.

> *For full acoustic ray-tracing derivations and tier rules, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#3-physics-based-acoustic-shadow-validation).*

---

## 8. AI Models, Datasets & Verified Benchmarks

All production detection metrics are evaluated on a clean, unified sonar dataset ([`backend/data/unified_sonar/`](backend/data/unified_sonar/)) with **0.0% train/validation leakage** (297 training images, 74 held-out validation images):

| Active Production Metric | Clean Split Score | Dataset Condition |
| :--- | :---: | :--- |
| **mAP@50** | **95.90%** | Held-out clean validation split (zero identity leakage) |
| **mAP@50-95** | **85.20%** | Multi-IoU localization threshold ($[0.50 : 0.95]$) |
| **Box Precision (P)** | **86.70%** | Zero false-positive clutter suppression |
| **Box Recall (R)** | **91.81%** | Target capture rate across 219 ground-truth instances |

- **Primary Production Checkpoint:** [`backend/models/yolov8_varuna_active.pt`](backend/models/yolov8_varuna_active.pt)
- **Live Demo Benchmark Images:** [`public/sample-sonar/`](public/sample-sonar/) (7 held-out zero-hash overlap captures for zero-configuration testing).

> *For per-class breakdowns, data provenance details, legacy FLS model metrics, and Haralick GLCM geological rejection benchmarks, see [docs/AI_BENCHMARK.md](docs/AI_BENCHMARK.md).*

---

## 9. Explainable Sonar & Active Verification

VARUNA provides hydrographers with transparent forensic explainability: specular highlight reflections (cyan), expected cast shadows (orange), nadir propagation vectors, and 3D protrusion height telemetry ($H$) are rendered directly on the sonar canvas. When detections fall into ambiguous tiers, the platform's **Active Verification** engine autonomously calculates secondary survey trajectories ($\pm 45^\circ$ orthogonal headings, $15-35\,\text{m}$ CPA offsets) to resolve candidate anomalies through multi-look acoustic evidence.

> *For forensic overlay specifications and adaptive rescan geometry, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#4-explainable-sonar-forensic-analysis).*

---

## 10. Technology Stack & Platform Capabilities

VARUNA is built on Next.js 14 App Router (React 18, TypeScript, Tailwind CSS, Leaflet GIS) and a high-speed asynchronous FastAPI backend (Python 3.11+, PyTorch, Ultralytics YOLOv8, OpenCV, SQLAlchemy). Core modules include the Acoustic Sonar Enhancement Lab (`/cnn`), Debris Detection & Sonar Map Center (`/detection`), Watchlist Anomaly Registry (`/watchlist`), Analytics Dashboard (`/analytics`), and automated export of GeoJSON, CSV, and hydrographic PDF inspection dossiers.

> *For complete architectural component listings, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md#6-technology-stack).*

---

## 11. Security Posture & Known Limitations

In its current demonstration and evaluation state, UI authentication has been deliberately bypassed to provide evaluators with frictionless access to hydrographic inspection tools. Network CORS allows multi-port local development, and secrets are strictly excluded from version control via `.gitignore`. A production deployment pre-condition is the reinstatement of OAuth2/JWT role-based authentication and restricted CORS policies.

> *For the complete security policy and roadmap hardening matrix, see [docs/SECURITY.md](docs/SECURITY.md).*

---

## 12. Quickstart & Installation Guide

Run VARUNA locally in minutes:

```bash
# Backend Service (Terminal 1)
pip install -r backend/requirements.txt
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend Client (Terminal 2)
npm install
npm run dev
```

Interactive Swagger API docs are accessible at `http://localhost:8000/docs`, and the operator portal is available at `http://localhost:3000`.

> *For containerized Docker Compose instructions and step-by-step verification flows, see [docs/QUICKSTART.md](docs/QUICKSTART.md).*

---

## 13. Automated Test Suite (50 Tests, 100% Pass)

The platform is backed by 50 automated backend unit and integration tests across 11 test suites verifying preprocessing, physics confidence filters, coordinate splining, explainability overlays, active verification, and reporting:

```bash
python -m pytest backend/tests -v
```

```
============================= test session starts =============================
collected 50 items

backend/tests/test_active_verification.py ............                   [ 24%]
backend/tests/test_api.py ..                                             [ 28%]
backend/tests/test_confidence_filter.py ...                              [ 34%]
backend/tests/test_crab_pot_dataset.py .....                             [ 44%]
backend/tests/test_dataset_conversion.py ..                              [ 48%]
backend/tests/test_explainability.py ..........                          [ 68%]
backend/tests/test_fls_and_acoustic.py ..                                [ 72%]
backend/tests/test_geotagging.py ...                                     [ 78%]
backend/tests/test_new_sonar_capabilities.py .....                       [ 88%]
backend/tests/test_preprocessing.py ....                                 [ 96%]
backend/tests/test_reporting.py ..                                       [100%]

======================= 50 passed in 30.30s =======================
```

> *For detailed test module descriptions, see [docs/QUICKSTART.md](docs/QUICKSTART.md#5-running-the-automated-test-suite).*

---

## 14. Official SIH 2026 Pitching Report

The complete executive presentation dossier detailing the problem scope, technical architecture, deployment feasibility, operational impact, and scientific references is available for download:

- **Official Pitch Report (PDF):** [**VARUNA_AI_Pitching_Report.pdf**](./public/docs/VARUNA_AI_Pitching_Report.pdf)

This document provides a concise 5-slide technical summary engineered for institutional evaluation by the Ministry of Earth Sciences (MoES), Government of India.

---

## 15. Research Contact and Inquiries

For technical evaluations, collaborative research, or institutional deployments:

| Developer / Entity | Role / Affiliation | GitHub Profile | Official Email |
| :--- | :--- | :--- | :--- |
| **Bodhisatwa Dutta** | Lead Developer | [@BDutta18](https://github.com/BDutta18) | [workwithbd18@gmail.com](mailto:workwithbd18@gmail.com) |
| **Rupam Ghosh** | Lead Developer | [@rupamghosh2006](https://github.com/rupamghosh2006) | [rupamgh32@gmail.com](mailto:rupamgh32@gmail.com) |
| **Netaji Subhash Engineering College** | Academic Host Institution | [nsec.ac.in](https://nsec.ac.in/) | Techno City, Garia, Kolkata, West Bengal 700152 |
| **Ministry of Earth Sciences (MoES)** | Sponsoring Authority | [moes.gov.in](https://www.moes.gov.in/) | New Delhi, India |

---

<div align="center">
  <b>VARUNA</b> | Autonomous Sonar Marine Debris Intelligence Platform | Ministry of Earth Sciences (MoES)
</div>
