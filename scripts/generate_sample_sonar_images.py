import os
import shutil
import numpy as np
import cv2

def create_realistic_sonar_waterfall(
    filename: str,
    target_type: str = "ghost_net",
    width: int = 800,
    height: int = 800
):
    """
    Synthesizes a high-fidelity Side-Scan Sonar (SSS) waterfall image
    with Rayleigh speckle noise, slant-range attenuation, central nadir gap,
    and distinct acoustic specular highlight + cast acoustic shadow features.
    """
    # 1. Base Seabed Texture (Sandy ripples with acoustic backscatter)
    np.random.seed(42 if target_type == "ghost_net" else 101)
    
    # Low frequency seabed variation
    x = np.linspace(0, 10, width)
    y = np.linspace(0, 10, height)
    xx, yy = np.meshgrid(x, y)
    
    # Acoustic ripple pattern
    ripples = np.sin(xx * 3.0 + yy * 0.5) * 15 + np.cos(yy * 2.0) * 10
    
    # Rayleigh / speckle noise
    speckle = np.random.rayleigh(scale=28, size=(height, width))
    base = np.clip(95 + ripples + speckle, 20, 230).astype(np.uint8)
    
    # 2. Slant-Range Transmission Loss (Darker at far swath edges)
    distance_from_center = np.abs(np.linspace(-1, 1, width))
    attenuation = 1.0 - (0.35 * (distance_from_center ** 1.8))
    attenuation = np.tile(attenuation, (height, 1))
    base = np.clip(base * attenuation, 10, 255).astype(np.uint8)
    
    # 3. Central Nadir Blind Zone (Dark vertical stripe representing water column)
    nadir_width = int(width * 0.08)
    nadir_center = width // 2
    nadir_start = nadir_center - nadir_width // 2
    nadir_end = nadir_center + nadir_width // 2
    
    nadir_mask = np.random.normal(15, 4, (height, nadir_width)).clip(5, 30).astype(np.uint8)
    base[:, nadir_start:nadir_end] = nadir_mask
    
    # 4. Synthesize Acoustic Targets (Highlight + Cast Acoustic Shadow)
    # Target is placed in Starboard Swath (right side of nadir)
    tx, ty = int(width * 0.70), int(height * 0.45)
    
    if target_type == "ghost_net":
        # Entangled diffuse high-reflectance net filaments + irregular shadow
        for i in range(12):
            offset_x = int(np.random.normal(0, 22))
            offset_y = int(np.random.normal(0, 35))
            pt1 = (tx + offset_x - 30, ty + offset_y - 15)
            pt2 = (tx + offset_x + 35, ty + offset_y + 20)
            cv2.line(base, pt1, pt2, int(np.random.randint(220, 255)), thickness=np.random.randint(2, 4))
        
        # Cast Acoustic Shadow (Radially away from nadir, towards right)
        shadow_poly = np.array([
            [tx + 40, ty - 40],
            [tx + 180, ty - 50],
            [tx + 195, ty + 65],
            [tx + 45, ty + 50]
        ], np.int32)
        cv2.fillPoly(base, [shadow_poly], color=int(np.random.randint(8, 20)))
        
    elif target_type == "crab_pot":
        # Derelict Crab Pot (Wire mesh frame specular highlight + sharp rectangular shadow)
        cv2.rectangle(base, (tx - 25, ty - 25), (tx + 25, ty + 25), color=245, thickness=4)
        cv2.line(base, (tx - 25, ty - 25), (tx + 25, ty + 25), color=230, thickness=2)
        cv2.line(base, (tx - 25, ty + 25), (tx + 25, ty - 25), color=230, thickness=2)
        
        # Crisp cast acoustic shadow
        shadow_pts = np.array([
            [tx + 28, ty - 26],
            [tx + 140, ty - 32],
            [tx + 140, ty + 32],
            [tx + 28, ty + 26]
        ], np.int32)
        cv2.fillPoly(base, [shadow_pts], color=12)
        
    elif target_type == "tire":
        # Toroidal specular arc + inner/outer void shadow
        cv2.ellipse(base, (tx, ty), (28, 28), 0, 0, 360, color=240, thickness=5)
        # Cast shadow
        shadow_pts = np.array([
            [tx + 30, ty - 25],
            [tx + 120, ty - 30],
            [tx + 120, ty + 30],
            [tx + 30, ty + 25]
        ], np.int32)
        cv2.fillPoly(base, [shadow_pts], color=10)
        
    elif target_type == "shipwreck":
        # Large fragmented hull with multi-structural acoustic scatter
        hull_pts = np.array([
            [tx - 60, ty - 70],
            [tx + 10, ty - 90],
            [tx + 40, ty + 80],
            [tx - 30, ty + 100]
        ], np.int32)
        cv2.fillPoly(base, [hull_pts], color=235)
        
        # Deep extensive shadow field
        shadow_pts = np.array([
            [tx + 42, ty - 90],
            [tx + 240, ty - 110],
            [tx + 260, ty + 95],
            [tx + 42, ty + 80]
        ], np.int32)
        cv2.fillPoly(base, [shadow_pts], color=8)
        
    elif target_type == "metal_container":
        # Cargo shipping container (Hard rectilinear specular edge + elongated shadow)
        cv2.rectangle(base, (tx - 20, ty - 50), (tx + 20, ty + 50), color=250, thickness=-1)
        shadow_pts = np.array([
            [tx + 22, ty - 50],
            [tx + 160, ty - 60],
            [tx + 160, ty + 60],
            [tx + 22, ty + 50]
        ], np.int32)
        cv2.fillPoly(base, [shadow_pts], color=10)

    # Convert to standard 3-channel BGR for maximum viewer compatibility
    color_sonar = cv2.cvtColor(base, cv2.COLOR_GRAY2BGR)
    cv2.imwrite(filename, color_sonar)
    print(f"Generated sample sonar image: {filename}")


def main():
    target_dir = os.path.join("public", "sample-sonar")
    os.makedirs(target_dir, exist_ok=True)
    
    samples = [
        ("sss_ghost_net_sample.jpg", "ghost_net"),
        ("sss_crab_pot_sample.jpg", "crab_pot"),
        ("sss_rubber_tire_sample.jpg", "tire"),
        ("sss_shipwreck_sample.jpg", "shipwreck"),
        ("sss_metal_container_sample.jpg", "metal_container"),
    ]
    
    for fname, stype in samples:
        filepath = os.path.join(target_dir, fname)
        create_realistic_sonar_waterfall(filepath, target_type=stype)
        
    # Copy to frontend directory as well
    fe_target_dir = os.path.join("frontend", "public", "sample-sonar")
    os.makedirs(fe_target_dir, exist_ok=True)
    for fname, _ in samples:
        src = os.path.join(target_dir, fname)
        dst = os.path.join(fe_target_dir, fname)
        shutil.copy(src, dst)
        
    print(f"All sample sonar images generated and copied to {fe_target_dir}")

if __name__ == "__main__":
    main()
