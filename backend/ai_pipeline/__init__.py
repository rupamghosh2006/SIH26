"""
SeaGuard AI - AI & CV Pipeline for Side-Scan Sonar Marine Debris Detection.
"""

from .synthetic_generator import SyntheticSonarGenerator, CLASSES, CLASS_TO_IDX, IDX_TO_CLASS
from .preprocessing import preprocess_sonar_image, create_image_tiles, reconstruct_from_tiles
from .detection import SonarDetector
from .confidence_filter import evaluate_detection_confidence, ConfidenceResult
from .geotagging import SonarGeotagger, NavigationPing
from .reporting import build_detection_report

__all__ = [
    "SyntheticSonarGenerator",
    "CLASSES",
    "CLASS_TO_IDX",
    "IDX_TO_CLASS",
    "preprocess_sonar_image",
    "create_image_tiles",
    "reconstruct_from_tiles",
    "SonarDetector",
    "evaluate_detection_confidence",
    "ConfidenceResult",
    "SonarGeotagger",
    "NavigationPing",
    "build_detection_report",
]
