"""
Synthetic Side-Scan Sonar (SSS) Image & Label Generator.
Produces high-fidelity synthetic side-scan sonar waterfall images with realistic
speckle noise, seafloor textures (sand ripples, rock clusters, mud flats),
central nadir water column blind zone, specular acoustic reflections,
and physics-aligned acoustic cast shadows for man-made marine debris.
"""

import os
import random
import math
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import cv2

CLASSES = ["ghost_net", "pipe_cylinder", "shipwreck_fragment"]
UNIFIED_CLASSES = ["shipwreck", "pipe_or_cylinder", "net_or_entangled_debris", "unknown_anomaly"]

CLASS_TO_IDX = {
    "ghost_net": 2,
    "net_or_entangled_debris": 2,
    "pipe_cylinder": 1,
    "pipe_or_cylinder": 1,
    "shipwreck_fragment": 0,
    "shipwreck": 0,
    "unknown_anomaly": 3
}

IDX_TO_CLASS = {
    0: "shipwreck",
    1: "pipe_or_cylinder",
    2: "net_or_entangled_debris",
    3: "unknown_anomaly"
}


class SyntheticSonarGenerator:
    def __init__(self, image_width: int = 1024, image_height: int = 1024, seed: Optional[int] = None):
        self.width = image_width
        self.height = image_height
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

    def _generate_seabed_background(self) -> np.ndarray:
        """
        Generates realistic acoustic backscatter seabed background using
        Rayleigh-distributed speckle noise and procedural texture layers
        (sand ripples, mud flats, gentle slope gradients).
        """
        w, h = self.width, self.height
        
        # Base seafloor backscatter intensity (typical mid-grey ~100-130)
        base_intensity = np.random.uniform(95, 125)
        
        # 1. Multiplicative Rayleigh speckle noise
        # Rayleigh distribution parameter sigma
        sigma = np.random.uniform(22, 32)
        speckle = np.random.rayleigh(scale=sigma, size=(h, w)).astype(np.float32)
        speckle = speckle - np.mean(speckle)  # zero-center
        
        background = np.full((h, w), base_intensity, dtype=np.float32) + speckle

        # 2. Add Sand Ripples (sinusoidal wave pattern with spatial frequency modulation)
        has_ripples = random.random() < 0.75
        if has_ripples:
            ripple_angle = np.random.uniform(-0.4, 0.4)  # slight angle to trackline
            ripple_freq = np.random.uniform(0.03, 0.08)
            ripple_amp = np.random.uniform(12, 28)
            
            y_coords, x_coords = np.mgrid[0:h, 0:w]
            # Add slight non-linear distortion to ripples
            distortion = 10 * np.sin(y_coords * 0.005) + 8 * np.cos(x_coords * 0.008)
            phase = (x_coords * np.cos(ripple_angle) + y_coords * np.sin(ripple_angle) + distortion) * ripple_freq
            ripple_layer = ripple_amp * np.sin(phase)
            
            # Sand ripples also have subtle asymmetric shadows
            ripple_shadow = np.clip(ripple_layer, -ripple_amp, 0) * 0.6
            background += ripple_layer + ripple_shadow

        # 3. Add Natural Clutter / Rock Patches (non-debris natural seabed anomalies)
        num_rock_clusters = random.randint(3, 8)
        for _ in range(num_rock_clusters):
            cx = random.randint(int(w * 0.1), int(w * 0.9))
            cy = random.randint(int(h * 0.1), int(h * 0.9))
            # Rock clusters have small chaotic bright spots without systematic unilateral long shadow
            num_rocks = random.randint(4, 12)
            cluster_radius = random.randint(15, 45)
            for _ in range(num_rocks):
                rx = int(np.clip(cx + np.random.normal(0, cluster_radius * 0.4), 0, w - 1))
                ry = int(np.clip(cy + np.random.normal(0, cluster_radius * 0.4), 0, h - 1))
                r_size = random.randint(2, 6)
                cv2.circle(background, (rx, ry), r_size, float(np.random.uniform(180, 230)), -1)

        # 4. Slant-range gain curve (time-varied gain: signal slightly decays with range from nadir)
        nadir_x = w // 2
        dist_from_nadir = np.abs(np.arange(w) - nadir_x) / (w / 2.0)
        gain_falloff = 1.0 - 0.15 * (dist_from_nadir ** 1.5)
        background = background * gain_falloff[np.newaxis, :]

        return background

    def _apply_nadir_gap(self, image: np.ndarray) -> Tuple[np.ndarray, int, int]:
        """
        Creates the central nadir water-column blind zone where no seafloor echo
        returns before first bottom arrival, bounded by high-intensity first bottom return lines.
        """
        w, h = self.width, self.height
        nadir_center = w // 2
        nadir_width = random.randint(int(w * 0.06), int(w * 0.12))
        
        nadir_left = max(0, nadir_center - nadir_width // 2)
        nadir_right = min(w, nadir_center + nadir_width // 2)
        
        # Water column echo is very low intensity (~5-20) with low noise
        water_noise = np.random.normal(12, 4, (h, nadir_right - nadir_left))
        image[:, nadir_left:nadir_right] = np.clip(water_noise, 2, 30)

        # First bottom arrival boundary: intense acoustic specular reflection
        boundary_w = random.randint(2, 4)
        left_bound = max(0, nadir_left - boundary_w)
        right_bound = min(w, nadir_right + boundary_w)
        
        image[:, left_bound:nadir_left] = np.random.uniform(210, 255, (h, nadir_left - left_bound))
        image[:, nadir_right:right_bound] = np.random.uniform(210, 255, (h, right_bound - nadir_right))
        
        return image, nadir_left, nadir_right

    def _render_debris_object(
        self,
        image: np.ndarray,
        cls_name: str,
        nadir_x: int,
        target_side: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Renders a physics-accurate debris object with specular acoustic highlight
        and matching acoustic shadow facing AWAY from nadir track.
        """
        w, h = self.width, self.height
        
        # Choose port or starboard placement (avoiding nadir gap)
        if target_side is None:
            side = random.choice(["port", "starboard"])
        else:
            side = target_side
            
        if side == "port":
            # Left side of image. Sound travels right-to-left.
            # Highlight is on right side of object, shadow extends LEFT towards x=0.
            cx = random.randint(int(w * 0.08), int(nadir_x - w * 0.08))
            shadow_dir = -1  # leftwards
        else:
            # Right side of image. Sound travels left-to-right.
            # Highlight is on left side of object, shadow extends RIGHT towards x=w.
            cx = random.randint(int(nadir_x + w * 0.08), int(w * 0.92))
            shadow_dir = 1  # rightwards

        cy = random.randint(int(h * 0.08), int(h * 0.92))
        dist_from_nadir = abs(cx - nadir_x)
        # Grazing angle effect: further from nadir = longer acoustic shadow
        shadow_length_factor = 1.0 + (dist_from_nadir / (w * 0.5)) * 1.4

        pts_highlight = []
        pts_shadow = []
        
        if cls_name == "pipe_cylinder":
            # Linear / cylindrical structure
            # Typically oriented at some angle, high specular line + parallel shadow strip
            obj_len = random.randint(35, 90)
            obj_thickness = random.randint(4, 9)
            angle = np.random.uniform(-0.8, 0.8)  # tilt angle in radians
            
            # Center coordinates
            dx = (obj_len / 2) * np.sin(angle)
            dy = (obj_len / 2) * np.cos(angle)
            
            p1 = (int(cx - dx), int(cy - dy))
            p2 = (int(cx + dx), int(cy + dy))
            
            # Acoustic shadow distance
            shadow_len = int(random.randint(25, 60) * shadow_length_factor)
            
            # Draw shadow first (dark area on background)
            # Shadow polygon: projected from pipe away from nadir
            s_p1 = (p1[0] + shadow_dir * shadow_len, p1[1])
            s_p2 = (p2[0] + shadow_dir * shadow_len, p2[1])
            shadow_poly = np.array([p1, p2, s_p2, s_p1], dtype=np.int32)
            cv2.fillPoly(image, [shadow_poly], float(random.randint(5, 25)))
            pts_shadow.extend([p1, p2, s_p2, s_p1])

            # Draw highlight (bright specular reflection)
            highlight_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.line(highlight_mask, p1, p2, 255, thickness=obj_thickness)
            # Add highlight intensity
            image[highlight_mask > 0] = np.random.uniform(220, 255, np.sum(highlight_mask > 0))
            pts_highlight.extend([p1, p2])

        elif cls_name == "ghost_net":
            # Tangled / mesh / filamentous blob
            blob_w = random.randint(28, 70)
            blob_h = random.randint(28, 70)
            shadow_len = int(random.randint(25, 55) * shadow_length_factor)
            
            # Create irregular mesh contours
            num_nodes = random.randint(6, 12)
            angles = np.linspace(0, 2 * np.pi, num_nodes, endpoint=False)
            radii = np.random.uniform(0.6, 1.3, num_nodes) * (blob_w / 2.0)
            nodes = []
            for a, r in zip(angles, radii):
                nx = int(cx + r * np.cos(a))
                ny = int(cy + r * np.sin(a) * (blob_h / blob_w))
                nodes.append((nx, ny))
            nodes = np.array(nodes, dtype=np.int32)

            # Irregular shadow polygon
            shadow_nodes = []
            for nx, ny in nodes:
                shadow_nodes.append((nx + shadow_dir * shadow_len + random.randint(-5, 5), ny))
            combined_shadow_poly = np.concatenate([nodes, shadow_nodes[::-1]])
            cv2.fillPoly(image, [combined_shadow_poly], float(random.randint(8, 30)))
            pts_shadow.extend(combined_shadow_poly.tolist())

            # Fibrous bright highlights inside net boundary
            net_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.fillPoly(net_mask, [nodes], 255)
            # Multi-strand texture
            for _ in range(random.randint(8, 18)):
                p_a = (cx + random.randint(-blob_w//2, blob_w//2), cy + random.randint(-blob_h//2, blob_h//2))
                p_b = (cx + random.randint(-blob_w//2, blob_w//2), cy + random.randint(-blob_h//2, blob_h//2))
                cv2.line(net_mask, p_a, p_b, 255, thickness=random.randint(1, 3))
            
            image[net_mask > 0] = np.clip(
                image[net_mask > 0] * 0.4 + np.random.uniform(190, 255, np.sum(net_mask > 0)), 0, 255
            )
            pts_highlight.extend(nodes.tolist())

        elif cls_name == "shipwreck_fragment":
            # Angular / structural plate or rib fragment
            frag_w = random.randint(35, 85)
            frag_h = random.randint(30, 80)
            shadow_len = int(random.randint(35, 80) * shadow_length_factor)

            # Convex / angular polygon
            num_vertices = random.randint(4, 7)
            angles = np.sort(np.random.uniform(0, 2 * np.pi, num_vertices))
            poly_pts = []
            for a in angles:
                px = int(cx + (frag_w / 2) * np.cos(a) * np.random.uniform(0.7, 1.2))
                py = int(cy + (frag_h / 2) * np.sin(a) * np.random.uniform(0.7, 1.2))
                poly_pts.append((px, py))
            poly_pts = np.array(poly_pts, dtype=np.int32)

            # Structural shadow cast
            shadow_pts = []
            for px, py in poly_pts:
                shadow_pts.append((px + shadow_dir * shadow_len, py))
            combined_shadow = np.concatenate([poly_pts, shadow_pts[::-1]])
            cv2.fillPoly(image, [combined_shadow], float(random.randint(4, 20)))
            pts_shadow.extend(combined_shadow.tolist())

            # High-reflectance structural surface
            struct_mask = np.zeros((h, w), dtype=np.uint8)
            cv2.fillPoly(struct_mask, [poly_pts], 255)
            image[struct_mask > 0] = np.random.uniform(215, 255, np.sum(struct_mask > 0))
            
            # Add structural internal ribs / edges
            for i in range(len(poly_pts)):
                p1 = tuple(poly_pts[i])
                p2 = tuple(poly_pts[(i + 2) % len(poly_pts)])
                cv2.line(image, p1, p2, float(random.randint(240, 255)), thickness=2)
            pts_highlight.extend(poly_pts.tolist())

        # Compute bounding box encompassing highlight and shadow
        all_pts = pts_highlight + pts_shadow
        if not all_pts:
            return None
            
        xs = [p[0] for p in all_pts]
        ys = [p[1] for p in all_pts]
        
        min_x = max(0, min(xs) - 4)
        max_x = min(w - 1, max(xs) + 4)
        min_y = max(0, min(ys) - 4)
        max_y = min(h - 1, max(ys) + 4)
        
        bbox_w = max_x - min_x
        bbox_h = max_y - min_y
        
        if bbox_w < 10 or bbox_h < 10:
            return None

        # Normalized coordinates for YOLO (x_center, y_center, width, height)
        x_center = (min_x + max_x) / (2.0 * w)
        y_center = (min_y + max_y) / (2.0 * h)
        norm_w = bbox_w / float(w)
        norm_h = bbox_h / float(h)
        
        return {
            "class_name": cls_name,
            "class_idx": CLASS_TO_IDX[cls_name],
            "bbox_pixels": [int(min_x), int(min_y), int(bbox_w), int(bbox_h)],
            "yolo_bbox": [float(x_center), float(y_center), float(norm_w), float(norm_h)],
            "side": side,
            "highlight_center": (cx, cy)
        }

    def generate_image_with_debris(
        self,
        num_objects: Optional[int] = None,
        force_classes: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Generates a complete synthetic side-scan sonar image with background,
        nadir gap, and randomly placed debris targets.
        """
        # 1. Base seabed texture
        img = self._generate_seabed_background()
        
        # 2. Nadir water column gap
        img, nadir_left, nadir_right = self._apply_nadir_gap(img)
        nadir_x = self.width // 2
        
        # 3. Add debris objects
        if num_objects is None:
            num_objects = random.randint(1, 5)
            
        detections = []
        classes_to_use = force_classes if force_classes else [random.choice(CLASSES) for _ in range(num_objects)]
        
        for cls_name in classes_to_use:
            det = self._render_debris_object(img, cls_name, nadir_x)
            if det:
                detections.append(det)

        # 4. Final post-processing (clip & 8-bit conversion)
        img_uint8 = np.clip(img, 0, 255).astype(np.uint8)
        
        # Add subtle acoustic high-frequency blur to simulate transducer impulse response
        img_uint8 = cv2.GaussianBlur(img_uint8, (3, 3), 0.5)

        return img_uint8, detections


def generate_synthetic_dataset(
    output_dir: str,
    num_train: int = 400,
    num_val: int = 80,
    image_size: int = 640
):
    """
    Generates a full YOLO-format synthetic dataset on disk with images and .txt label files.
    """
    os.makedirs(os.path.join(output_dir, "images", "train"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "images", "val"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "labels", "train"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "labels", "val"), exist_ok=True)

    generator = SyntheticSonarGenerator(image_width=image_size, image_height=image_size)

    splits = [("train", num_train), ("val", num_val)]
    
    for split_name, count in splits:
        print(f"Generating {count} synthetic sonar images for '{split_name}' split...")
        for idx in range(count):
            img, annotations = generator.generate_image_with_debris()
            
            img_filename = f"sonar_synth_{split_name}_{idx:05d}.jpg"
            lbl_filename = f"sonar_synth_{split_name}_{idx:05d}.txt"
            
            img_path = os.path.join(output_dir, "images", split_name, img_filename)
            lbl_path = os.path.join(output_dir, "labels", split_name, lbl_filename)
            
            # Save image
            cv2.imwrite(img_path, img)
            
            # Save YOLO annotations: class_idx x_center y_center width height
            with open(lbl_path, "w") as f:
                for ann in annotations:
                    c = ann["class_idx"]
                    xc, yc, w, h = ann["yolo_bbox"]
                    f.write(f"{c} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")

    # Generate data.yaml for YOLOv8 training
    yaml_path = os.path.join(output_dir, "data.yaml")
    with open(yaml_path, "w") as f:
        f.write(f"path: {os.path.abspath(output_dir)}\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        f.write(f"nc: {len(CLASSES)}\n")
        f.write(f"names: {CLASSES}\n")

    print(f"Dataset generated successfully at: {output_dir}")
    return yaml_path


if __name__ == "__main__":
    generate_synthetic_dataset("backend/data/synthetic_sonar", num_train=300, num_val=60)
