"""
CLI Tool to generate synthetic side-scan sonar dataset in YOLOv8 format.
Usage:
    python -m ai_pipeline.generate_synthetic_dataset --output backend/data/synthetic_sonar --train 400 --val 80
"""

import argparse
import os
import sys
try:
    from .synthetic_generator import generate_synthetic_dataset
except ImportError:
    from ai_pipeline.synthetic_generator import generate_synthetic_dataset


def main():
    parser = argparse.ArgumentParser(description="Generate Synthetic Sonar Debris Dataset for YOLOv8")
    parser.add_argument("--output", type=str, default="backend/data/synthetic_sonar", help="Output dataset directory")
    parser.add_argument("--train", type=int, default=300, help="Number of training images to generate")
    parser.add_argument("--val", type=int, default=60, help="Number of validation images to generate")
    parser.add_argument("--size", type=int, default=640, help="Image width and height in pixels")
    
    args = parser.parse_args()
    
    print(f"==================================================")
    print(f" VARUNA: Generating Synthetic Sonar Dataset ")
    print(f" Target Directory: {args.output}")
    print(f" Train Images: {args.train}, Val Images: {args.val}, Size: {args.size}x{args.size}")
    print(f"==================================================")
    
    yaml_path = generate_synthetic_dataset(
        output_dir=args.output,
        num_train=args.train,
        num_val=args.val,
        image_size=args.size
    )
    print(f"Dataset generation complete! YOLO config saved at: {yaml_path}")


if __name__ == "__main__":
    main()
