"""
Preprocessing Module for Side-Scan Sonar Imagery.
Handles contrast normalization (CLAHE), adaptive speckle noise reduction,
automated nadir blind-zone detection, and image tiling for large waterfall strips.
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import cv2


def apply_clahe_contrast_enhancement(
    image: np.ndarray,
    clip_limit: float = 2.5,
    tile_grid_size: Tuple[int, int] = (8, 8)
) -> np.ndarray:
    """
    Applies Contrast Limited Adaptive Histogram Equalization (CLAHE)
    to balance acoustic backscatter across slant-range distances.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()
        
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    enhanced = clahe.apply(gray)
    return enhanced


def apply_adaptive_speckle_filter(
    image: np.ndarray,
    d: int = 7,
    sigma_color: float = 40.0,
    sigma_space: float = 40.0
) -> np.ndarray:
    """
    Applies edge-preserving bilateral filtering to suppress Rayleigh speckle noise
    while preserving high-contrast acoustic specular edges and shadow boundaries.
    """
    filtered = cv2.bilateralFilter(image, d=d, sigmaColor=sigma_color, sigmaSpace=sigma_space)
    return filtered


def detect_nadir_gap(image: np.ndarray) -> Dict[str, Any]:
    """
    Detects the dark central nadir water-column blind zone in a waterfall image
    by analyzing vertical column average backscatter profile.
    """
    h, w = image.shape[:2]
    # Compute column-wise mean intensity
    col_means = np.mean(image, axis=0)
    
    # Search around central 40% of image width
    center_start = int(w * 0.3)
    center_end = int(w * 0.7)
    central_profile = col_means[center_start:center_end]
    
    # Lowest intensity column in central region
    min_idx_relative = np.argmin(central_profile)
    center_x = center_start + min_idx_relative
    
    # Find nadir boundaries where intensity rises above threshold
    min_val = col_means[center_x]
    bg_val = np.percentile(col_means, 75)
    threshold = min_val + 0.45 * (bg_val - min_val)
    
    left_x = center_x
    while left_x > 0 and col_means[left_x] < threshold:
        left_x -= 1
        
    right_x = center_x
    while right_x < w - 1 and col_means[right_x] < threshold:
        right_x += 1
        
    nadir_width = max(right_x - left_x, int(w * 0.05))
    
    return {
        "nadir_center": int(center_x),
        "nadir_left": int(left_x),
        "nadir_right": int(right_x),
        "nadir_width": int(nadir_width)
    }


def preprocess_sonar_image(
    image: np.ndarray,
    apply_clahe: bool = True,
    apply_denoise: bool = True
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Complete preprocessing pipeline for raw sonar waterfall imagery:
    1. Grayscale conversion if required
    2. Adaptive speckle noise reduction
    3. CLAHE contrast normalization
    4. Nadir blind zone analysis
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    processed = gray
    if apply_denoise:
        processed = apply_adaptive_speckle_filter(processed)
        
    if apply_clahe:
        processed = apply_clahe_contrast_enhancement(processed)

    nadir_info = detect_nadir_gap(processed)
    
    return processed, nadir_info


def create_image_tiles(
    image: np.ndarray,
    tile_size: int = 640,
    overlap: float = 0.20
) -> List[Dict[str, Any]]:
    """
    Tiles a large sonar waterfall image into overlapping square tiles
    for YOLOv8 model inference.
    """
    h, w = image.shape[:2]
    step = int(tile_size * (1.0 - overlap))
    
    tiles = []
    
    # Ensure at least 1 tile if image is smaller than tile_size
    if h <= tile_size and w <= tile_size:
        padded = np.zeros((tile_size, tile_size), dtype=image.dtype)
        padded[:h, :w] = image
        return [{
            "tile_image": padded,
            "x_offset": 0,
            "y_offset": 0,
            "width": w,
            "height": h,
            "original_shape": (h, w)
        }]

    y_points = list(range(0, max(1, h - tile_size + 1), step))
    if not y_points or y_points[-1] + tile_size < h:
        y_points.append(max(0, h - tile_size))
        
    x_points = list(range(0, max(1, w - tile_size + 1), step))
    if not x_points or x_points[-1] + tile_size < w:
        x_points.append(max(0, w - tile_size))

    # Remove duplicates
    y_points = sorted(list(set(y_points)))
    x_points = sorted(list(set(x_points)))

    for y in y_points:
        for x in x_points:
            cur_w = min(tile_size, w - x)
            cur_h = min(tile_size, h - y)
            
            tile_crop = image[y:y + cur_h, x:x + cur_w]
            
            # If tile is smaller than tile_size, pad with zero (or edge replication)
            if cur_h < tile_size or cur_w < tile_size:
                padded = np.zeros((tile_size, tile_size), dtype=image.dtype)
                padded[:cur_h, :cur_w] = tile_crop
                tile_to_return = padded
            else:
                tile_to_return = tile_crop
                
            tiles.append({
                "tile_image": tile_to_return,
                "x_offset": x,
                "y_offset": y,
                "width": cur_w,
                "height": cur_h,
                "original_shape": (h, w)
            })

    return tiles


def reconstruct_from_tiles(
    tiles: List[Dict[str, Any]],
    original_shape: Tuple[int, int]
) -> np.ndarray:
    """
    Reconstructs the full image from tiled patches with blending in overlapping areas.
    """
    h, w = original_shape
    canvas = np.zeros((h, w), dtype=np.float32)
    weight_map = np.zeros((h, w), dtype=np.float32)
    
    for t in tiles:
        x = t["x_offset"]
        y = t["y_offset"]
        cur_w = t["width"]
        cur_h = t["height"]
        
        tile_crop = t["tile_image"][:cur_h, :cur_w].astype(np.float32)
        
        canvas[y:y + cur_h, x:x + cur_w] += tile_crop
        weight_map[y:y + cur_h, x:x + cur_w] += 1.0

    weight_map[weight_map == 0] = 1.0
    reconstructed = (canvas / weight_map).astype(np.uint8)
    return reconstructed


def apply_slant_to_ground_range_correction(
    image: np.ndarray,
    altitude_m: float,
    max_slant_range_m: float,
    nadir_x: Optional[int] = None
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    True Slant-Range to Ground-Range (SRR) Correction.
    
    Transforms the acoustic slant-range image into a true horizontal ground-range
    seafloor representation by solving:
        R_g = sqrt(max(0, R_s^2 - H^2))
    where:
        R_s is the acoustic slant range (distance along wave ray),
        H is the sensor altitude above the seafloor,
        R_g is the true horizontal distance on the seabed.

    Near the nadir (R_s < H), acoustic energy is traveling through the water column.
    Once R_s >= H, the bottom return begins. This function remaps pixels from slant range
    to a uniform, equidistant ground-range spatial grid, removing the water-column blind zone
    distortion and restoring correct physical aspect ratios (length x width) for detected debris.

    Returns:
        corrected_image: 2D np.ndarray warped to uniform ground range
        srr_info: metadata including max_ground_range_m, ground_res_m_per_pixel, nadir_offset_m
    """
    import math

    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image.copy()

    h, w = gray.shape[:2]
    if nadir_x is None:
        nadir_x = w // 2

    # If altitude is 0 or invalid, estimate altitude from nadir width
    if altitude_m <= 0.5:
        nadir_info = detect_nadir_gap(gray)
        nadir_half_px = nadir_info["nadir_width"] / 2.0
        altitude_m = max(3.0, (nadir_half_px / (w / 2.0)) * max_slant_range_m)

    # Altitude cannot exceed slant range
    altitude_m = min(altitude_m, max_slant_range_m * 0.95)

    # Maximum ground range on each side (Port and Starboard)
    max_ground_range_m = math.sqrt(max(0.0, max_slant_range_m**2 - altitude_m**2))
    
    port_w = max(1, nadir_x)
    stbd_w = max(1, w - nadir_x)
    
    # Construct remapping coordinate grid for cv2.remap
    map_x = np.zeros((h, w), dtype=np.float32)
    map_y = np.zeros((h, w), dtype=np.float32)
    
    for row in range(h):
        map_y[row, :] = row

    # Port channel: x ranges from 0 to port_w - 1
    # At x = port_w - 1 (near nadir), ground range R_g = 0 -> slant range R_s = H
    # At x = 0 (far port), ground range R_g = max_ground_range_m -> slant range R_s = max_slant_range_m
    for col in range(port_w):
        norm_gr = (port_w - 1 - col) / max(1.0, float(port_w - 1))
        rg = norm_gr * max_ground_range_m
        rs = math.sqrt(rg**2 + altitude_m**2)
        norm_sr = rs / max_slant_range_m
        src_x = port_w - 1 - (norm_sr * (port_w - 1))
        map_x[:, col] = max(0.0, min(float(w - 1), src_x))

    # Starboard channel: x ranges from nadir_x to w - 1
    # At x = nadir_x (near nadir), ground range R_g = 0 -> slant range R_s = H
    # At x = w - 1 (far starboard), ground range R_g = max_ground_range_m -> slant range R_s = max_slant_range_m
    for col in range(nadir_x, w):
        norm_gr = (col - nadir_x) / max(1.0, float(w - 1 - nadir_x))
        rg = norm_gr * max_ground_range_m
        rs = math.sqrt(rg**2 + altitude_m**2)
        norm_sr = rs / max_slant_range_m
        src_x = nadir_x + (norm_sr * (w - 1 - nadir_x))
        map_x[:, col] = max(0.0, min(float(w - 1), src_x))

    # Remap slant-range image to ground-range image using bilinear interpolation
    corrected = cv2.remap(gray, map_x, map_y, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    ground_res = max_ground_range_m / max(1.0, float(w / 2.0))

    srr_info = {
        "max_ground_range_m": round(max_ground_range_m, 2),
        "max_slant_range_m": round(max_slant_range_m, 2),
        "sensor_altitude_m": round(altitude_m, 2),
        "ground_resolution_m_per_px": round(ground_res, 4),
        "srr_corrected": True
    }

    return corrected, srr_info

