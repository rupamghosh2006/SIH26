#!/bin/bash
set -e

echo "========================================================"
echo "      VARUNA - Full Stack Initialization"
echo "   Ministry of Earth Sciences (MoES) | SIH26057"
echo "========================================================"

echo "[1/4] Installing Python Backend Dependencies..."
pip install -r backend/requirements.txt

echo "[2/4] Running Unit & Integration Tests..."
python -m pytest backend/tests

echo "[3/4] Installing Frontend Dependencies..."
cd frontend
npm install
cd ..

echo "[4/4] Starting Full-Stack Services..."
echo "Backend:  http://127.0.0.1:8000 (FastAPI Swagger Docs)"
echo "Frontend: http://localhost:3000 (Next.js Oceanographic Portal)"

# Run backend and frontend concurrently
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 &
cd frontend && npm run dev &

wait
