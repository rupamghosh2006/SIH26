"""
Varuna - Main FastAPI Application.
"""

import os
import sys
import time
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure backend root is on sys.path
_backend_root = str(Path(__file__).resolve().parent.parent)
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .database import engine, Base, init_db
from . import models
from .routes import surveys, health

# Create database tables and perform migrations
init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup actions
    print(r"""
 __     __ _    ____  _   _ _   _    _       _    ___ 
 \ \   / // \  |  _ \| | | | \ | |  / \     / \  |_ _|
  \ \ / // _ \ | |_) | | | |  \| | / _ \   / _ \  | | 
   \ V // ___ \|  _ <| |_| | |\  |/ ___ \ / ___ \ | | 
    \_//_/   \_\_| \_\\___/|_| \_/_/   \_/_/   \_\___|
  MoES SIH26057: Autonomous Acoustic Debris Intelligence
    """)
    print(f"[VARUNA - MoES] Starting backend service...")
    print(f"[VARUNA - MoES] Uploads directory: {settings.UPLOADS_DIR}")
    print(f"[VARUNA - MoES] Model path: {settings.MODEL_PATH} (exists={os.path.exists(settings.MODEL_PATH)})")
    yield
    # Shutdown actions
    print(f"[{settings.PROJECT_NAME}] Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Marine Debris Detection System for Side-Scan Sonar Imagery",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Directories for Images and Thumbnails
os.makedirs(settings.UPLOADS_DIR, exist_ok=True)
os.makedirs(settings.THUMBNAILS_DIR, exist_ok=True)

app.mount("/static/uploads", StaticFiles(directory=str(settings.UPLOADS_DIR)), name="uploads")
app.mount("/static/thumbnails", StaticFiles(directory=str(settings.THUMBNAILS_DIR)), name="thumbnails")

# Register Routers
app.include_router(health.router, prefix=settings.API_V1_STR)
app.include_router(surveys.router, prefix=settings.API_V1_STR)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def root():
    return {
        "service": settings.PROJECT_NAME,
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }
