"""
Health Check and System Diagnostics Endpoint.
"""

import os
from fastapi import APIRouter
from ..config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    model_exists = os.path.exists(settings.MODEL_PATH)
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "model_loaded": model_exists,
        "model_path": str(settings.MODEL_PATH) if model_exists else "base/fallback"
    }
