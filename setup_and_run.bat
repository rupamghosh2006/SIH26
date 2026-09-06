@echo off
echo ========================================================
echo       VARUNA - Full Stack Initialization
echo    Ministry of Earth Sciences (MoES) | SIH26057
echo ========================================================

echo [1/4] Installing Python Backend Dependencies...
python -m pip install -r backend/requirements.txt

echo [2/4] Running Unit and Integration Tests...
python -m pytest backend/tests

echo [3/4] Installing Frontend NPM Dependencies...
cd frontend
call npm install
cd ..

echo [4/4] Starting Full-Stack Services...
echo Backend:  http://127.0.0.1:8000 (FastAPI Swagger Docs)
echo Frontend: http://localhost:3000 (Next.js Oceanographic Portal)

start cmd /k "python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload"
start cmd /k "cd frontend && npm run dev"

echo Services launched in background terminals!
