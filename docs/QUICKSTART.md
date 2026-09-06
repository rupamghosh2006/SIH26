# VARUNA — Quickstart & Execution Guide

> Step-by-step guide to installing, configuring, running, and testing the VARUNA platform locally or via Docker Compose.

---

## 1. Prerequisites

Ensure your host environment meets the following baseline requirements:

| Dependency | Minimum Version | Recommended | Notes |
| :--- | :--- | :--- | :--- |
| **Node.js** | Node 18.x | Node 20 LTS | Required for Next.js 14 frontend |
| **Python** | Python 3.11 | Python 3.11 or 3.12 | Required for FastAPI backend and PyTorch |
| **Git** | 2.x+ | Latest | Version control |
| **Docker** *(Optional)* | 24.0+ | Docker Desktop with Compose v2 | For containerized execution |

---

## 2. Local Setup & Launch

### Step 1: Clone the Repository
```bash
git clone https://github.com/rupamghosh2006/SIH26.git
cd SIH26
```

### Step 2: Launch the FastAPI Backend Service
In a dedicated terminal:
```bash
# 1. Install backend Python dependencies
pip install -r backend/requirements.txt

# 2. Launch FastAPI service on port 8000
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend Service:** `http://localhost:8000`
- **Interactive Swagger Documentation:** `http://localhost:8000/docs`
- **OpenAPI JSON Schema:** `http://localhost:8000/openapi.json`

### Step 3: Launch the Next.js 14 Frontend Client
In a second terminal:
```bash
# 1. Install Node.js dependencies
npm install

# 2. Start the development server
npm run dev
```
- **Web Application Portal:** `http://localhost:3000`

---

## 3. Containerized Execution via Docker Compose

To launch the complete fullstack platform in isolated containers:

```bash
# Build and run frontend and backend containers
docker-compose up --build
```

To stop the containers:
```bash
docker-compose down
```

---

## 4. Verify It's Working

### A. Health Check Endpoints
Confirm both microservices are responsive:

1. **FastAPI Backend Diagnostics:**
   ```bash
   curl http://localhost:8000/api/health
   ```
   *Expected Response:*
   ```json
   {
     "status": "healthy",
     "service": "Varuna",
     "model_loaded": true,
     "model_path": ".../backend/models/yolov8_varuna_active.pt"
   }
   ```

2. **Next.js Fullstack Health Check:**
   ```bash
   curl http://localhost:3000/api/health
   ```
   *Expected Response:*
   ```json
   {
     "status": "healthy",
     "timestamp": "..."
   }
   ```

### B. Run Your First Sonar Detection
1. Open your browser and navigate to `http://localhost:3000/detection`.
2. Locate the **Quick Sample Select** bar at the top of the interface.
3. Click any of the 7 preloaded benchmark sonar captures from [`public/sample-sonar/`](../public/sample-sonar/):
   - `ghost_net_sample_sss_01` or `ghost_net_sample_sss_02` (Ghost Net / ALDFG)
   - `shipwreck_sample_sss_01` or `shipwreck_sample_sss_02` (Shipwreck Fragment)
   - `pipe_cylinder_sample_sss_01` or `pipe_cylinder_sample_sss_02` (Pipeline / Subsea Cylinder)
   - `multi_debris_field_sample_01` (Complex multi-target field)
4. Click **Run Sonar Inspection**.
5. Observe the multi-tile YOLOv8 bounding boxes, acoustic cast shadow validation overlays, and the Explainable Sonar forensic breakdown.

---

## 5. Running the Automated Test Suite

VARUNA includes 50 automated backend unit and integration tests covering the entire acoustic pipeline:

```bash
python -m pytest backend/tests -v
```

### Verified Test Suite Breakdown (50 Tests, 100% Pass Rate)

| Test Module | Tests | Tested Subsystem |
| :--- | :---: | :--- |
| `backend/tests/test_active_verification.py` | 12 | Adaptive rescan geometry, waypoint generation, target association |
| `backend/tests/test_api.py` | 2 | FastAPI health endpoint, demo survey creation & query |
| `backend/tests/test_confidence_filter.py` | 3 | Physics shadow verification, port/starboard beam alignment |
| `backend/tests/test_crab_pot_dataset.py` | 5 | Ingestion parser, JSONL conversion, dataset preparation |
| `backend/tests/test_dataset_conversion.py` | 2 | Binary mask bbox extraction, leak-free validation split |
| `backend/tests/test_explainability.py` | 10 | 7-factor explainability score, mathematical audit, visual overlays |
| `backend/tests/test_fls_and_acoustic.py` | 2 | Seafloor facies classifier, checkpoint existence verification |
| `backend/tests/test_geotagging.py` | 3 | Ping splining, pixel-to-geographic coordinate projection |
| `backend/tests/test_new_sonar_capabilities.py` | 5 | XTF parsing, slant-range correction, physical dimension calculation, U-Net |
| `backend/tests/test_preprocessing.py` | 4 | CLAHE contrast enhancement, bilateral speckle filter, nadir gap |
| `backend/tests/test_reporting.py` | 2 | Structured GeoJSON, CSV, and hydrographic audit report exports |
| **Total Verified Test Count** | **50** | **50 passed, 0 failures across all 11 test modules** |
