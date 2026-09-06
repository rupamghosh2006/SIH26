"""
Utility to generate sample sonar survey images and paired navigation ping CSV files.
These can be used for demonstration, testing, or offline uploads.
"""

import os
import cv2
import pandas as pd
from datetime import datetime, timezone
import sys
from pathlib import Path

# Ensure backend in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ai_pipeline.synthetic_generator import SyntheticSonarGenerator
from ai_pipeline.geotagging import SonarGeotagger


def generate_sample_suite(output_dir: str = "backend/sample_data"):
    os.makedirs(output_dir, exist_ok=True)
    
    samples = [
        {
            "id": "sample_coastal_survey",
            "name": "sample_coastal_survey.jpg",
            "nav": "sample_coastal_nav.csv",
            "w": 1024,
            "h": 1280,
            "objects": 4,
            "start_lat": 15.8500,
            "start_lon": 83.9500,
            "heading": 60.0
        },
        {
            "id": "sample_deep_trench",
            "name": "sample_deep_trench.jpg",
            "nav": "sample_deep_trench_nav.csv",
            "w": 1024,
            "h": 1400,
            "objects": 5,
            "start_lat": 16.5000,
            "start_lon": 85.2000,
            "heading": 135.0
        }
    ]

    for s in samples:
        print(f"Generating sample: {s['id']}...")
        generator = SyntheticSonarGenerator(image_width=s["w"], image_height=s["h"])
        img, annotations = generator.generate_image_with_debris(num_objects=s["objects"])
        
        img_path = os.path.join(output_dir, s["name"])
        cv2.imwrite(img_path, img)

        # Generate paired Navigation CSV
        geotagger = SonarGeotagger.generate_synthetic_trackline(
            num_pings=s["h"],
            start_lat=s["start_lat"],
            start_lon=s["start_lon"],
            heading_deg=s["heading"],
            slant_range_m=75.0
        )

        rows = []
        for p in geotagger.pings:
            rows.append({
                "ping_index": p.ping_index,
                "latitude": p.latitude,
                "longitude": p.longitude,
                "depth_m": p.depth_m,
                "heading_deg": p.heading_deg,
                "timestamp": p.timestamp
            })
            
        df = pd.DataFrame(rows)
        csv_path = os.path.join(output_dir, s["nav"])
        df.to_csv(csv_path, index=False)
        print(f"Sample saved: {img_path} and {csv_path}")


if __name__ == "__main__":
    generate_sample_suite()
