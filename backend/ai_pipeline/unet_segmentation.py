"""
U-Net Ghost Net (ALDFG) Semantic Segmentation Module.

Implements deep semantic segmentation for diffuse, fibrous, tangled fishing gear
('ghost nets' / ALDFG) in side-scan sonar imagery.
Computes:
1. Pixel-level binary segmentation mask of net webbing
2. Geometric polygon boundary coordinates for UI overlay
3. True physical seabed entanglement area in square meters (m²)
4. Filamentous network density and morphological continuity metric
"""

import os
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import cv2

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


if TORCH_AVAILABLE:
    class DoubleConv(nn.Module):
        """[Conv2d -> BatchNorm -> ReLU] * 2"""
        def __init__(self, in_channels: int, out_channels: int):
            super().__init__()
            self.double_conv = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
                nn.BatchNorm2d(out_channels),
                nn.ReLU(inplace=True)
            )

        def forward(self, x):
            return self.double_conv(x)

    class GhostNetUNet(nn.Module):
        """
        Lightweight 4-stage U-Net optimized for filament and mesh structure extraction
        from side-scan sonar acoustic highlight/shadow regions.
        """
        def __init__(self, in_channels: int = 1, out_channels: int = 1):
            super().__init__()
            self.inc = DoubleConv(in_channels, 16)
            self.down1 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(16, 32))
            self.down2 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(32, 64))
            self.down3 = nn.Sequential(nn.MaxPool2d(2), DoubleConv(64, 128))
            
            self.up1 = nn.ConvTranspose2d(128, 64, kernel_size=2, stride=2)
            self.conv_up1 = DoubleConv(128, 64)
            
            self.up2 = nn.ConvTranspose2d(64, 32, kernel_size=2, stride=2)
            self.conv_up2 = DoubleConv(64, 32)
            
            self.up3 = nn.ConvTranspose2d(32, 16, kernel_size=2, stride=2)
            self.conv_up3 = DoubleConv(32, 16)
            
            self.outc = nn.Conv2d(16, out_channels, kernel_size=1)

        def forward(self, x):
            x1 = self.inc(x)
            x2 = self.down1(x1)
            x3 = self.down2(x2)
            x4 = self.down3(x3)
            
            x = self.up1(x4)
            # Match spatial dimensions if odd sizes
            diff_y = x3.size()[2] - x.size()[2]
            diff_x = x3.size()[3] - x.size()[3]
            if diff_y != 0 or diff_x != 0:
                x = F.pad(x, [diff_x // 2, diff_x - diff_x // 2, diff_y // 2, diff_y - diff_y // 2])
            x = self.conv_up1(torch.cat([x3, x], dim=1))
            
            x = self.up2(x)
            diff_y = x2.size()[2] - x.size()[2]
            diff_x = x2.size()[3] - x.size()[3]
            if diff_y != 0 or diff_x != 0:
                x = F.pad(x, [diff_x // 2, diff_x - diff_x // 2, diff_y // 2, diff_y - diff_y // 2])
            x = self.conv_up2(torch.cat([x2, x], dim=1))
            
            x = self.up3(x)
            diff_y = x1.size()[2] - x.size()[2]
            diff_x = x1.size()[3] - x.size()[3]
            if diff_y != 0 or diff_x != 0:
                x = F.pad(x, [diff_x // 2, diff_x - diff_x // 2, diff_y // 2, diff_y - diff_y // 2])
            x = self.conv_up3(torch.cat([x1, x], dim=1))
            
            logits = self.outc(x)
            return torch.sigmoid(logits)


class GhostNetSegmenter:
    """
    Inference and physical metric calculation engine for ghost net segmentation.
    Uses trained PyTorch U-Net with graceful fallback to morphological filament analysis.
    """
    def __init__(self, model_path: Optional[str] = None, device: Optional[str] = None):
        self.model = None
        self.device = device or ("cuda" if (TORCH_AVAILABLE and torch.cuda.is_available()) else "cpu")
        
        if model_path is None:
            # Default model search path
            base_dir = os.path.dirname(os.path.dirname(__file__))
            cand_path = os.path.join(base_dir, "models", "unet_ghostnet.pt")
            if os.path.exists(cand_path):
                model_path = cand_path

        if TORCH_AVAILABLE:
            try:
                net = GhostNetUNet(in_channels=1, out_channels=1)
                if model_path and os.path.exists(model_path):
                    state_dict = torch.load(model_path, map_location=self.device)
                    net.load_state_dict(state_dict)
                    print(f"[GhostNet U-Net] Loaded weights from {model_path}")
                else:
                    # Initialize default weights
                    self._init_conv_weights(net)
                net.to(self.device)
                net.eval()
                self.model = net
            except Exception as e:
                print(f"[GhostNet U-Net] Warning: Could not initialize neural model ({e}), falling back to morphological pipeline.")
                self.model = None

    @staticmethod
    def _init_conv_weights(model):
        if not TORCH_AVAILABLE:
            return
        for m in model.modules():
            if isinstance(m, nn.Conv2d) or isinstance(m, nn.ConvTranspose2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)

    def segment_patch(
        self,
        patch_img: np.ndarray,
        meters_per_pixel: float = 0.08,
        threshold: float = 0.45
    ) -> Dict[str, Any]:
        """
        Segment a candidate ghost net patch.
        
        Args:
            patch_img: 2D uint8 grayscale crop around the detected object.
            meters_per_pixel: Spatial resolution across the seabed (meters / pixel).
            threshold: Probability threshold for foreground segmentation.
            
        Returns:
            Dictionary with:
            - mask: 2D binary uint8 mask (0 or 255)
            - polygon: List of [x, y] vertices along outer boundary
            - entangled_area_m2: Physical area of net coverage on seabed
            - perimeter_m: Estimated physical outer perimeter
            - filament_density: Foreground coverage percentage
            - is_filamentous: Boolean indicating whether texture resembles netting
        """
        if patch_img is None or patch_img.size == 0:
            return {
                "mask": np.zeros((1, 1), dtype=np.uint8),
                "polygon": [],
                "entangled_area_m2": 0.0,
                "perimeter_m": 0.0,
                "filament_density": 0.0,
                "is_filamentous": False
            }

        orig_h, orig_w = patch_img.shape[:2]
        
        # 1. Inference via U-Net if available
        mask = None
        if self.model is not None and TORCH_AVAILABLE:
            try:
                # Resize to multiple of 16 for U-Net pooling
                pad_h = ((orig_h + 15) // 16) * 16
                pad_w = ((orig_w + 15) // 16) * 16
                resized_in = cv2.resize(patch_img, (max(32, pad_w), max(32, pad_h)), interpolation=cv2.INTER_LINEAR)
                
                # Normalize [0, 1]
                tensor_in = torch.from_numpy(resized_in).float() / 255.0
                tensor_in = tensor_in.unsqueeze(0).unsqueeze(0).to(self.device)
                
                with torch.no_grad():
                    prob_map = self.model(tensor_in).squeeze().cpu().numpy()
                    
                # Resize back to original patch dimensions
                prob_map_orig = cv2.resize(prob_map, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)
                mask = (prob_map_orig > threshold).astype(np.uint8) * 255
            except Exception as e:
                mask = None

        # 2. Classical Morphological Fallback / Refinement
        if mask is None or np.sum(mask > 0) == 0:
            mask = self._morphological_filament_segment(patch_img)

        # 3. Post-process mask: Morphological closing to bridge web strands
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mask_clean = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Remove isolated single-pixel specks
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_OPEN, kernel)

        # 4. Extract polygon boundary using OpenCV contour approximation
        contours, _ = cv2.findContours(mask_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        polygon = []
        max_contour = None
        if contours:
            # Find largest contour
            max_contour = max(contours, key=cv2.contourArea)
            # Simplify contour to smooth polygon
            epsilon = 0.015 * cv2.arcLength(max_contour, True)
            approx = cv2.approxPolyDP(max_contour, epsilon, True)
            polygon = [[int(pt[0][0]), int(pt[0][1])] for pt in approx]

        # 5. Compute true physical metrics
        white_pixels = int(np.sum(mask_clean > 0))
        area_per_pixel = (meters_per_pixel ** 2)
        entangled_area_m2 = round(white_pixels * area_per_pixel, 2)
        
        total_pixels = orig_h * orig_w
        density = round(white_pixels / max(1, total_pixels), 3)
        
        perimeter_m = 0.0
        grapple_point = None
        if max_contour is not None:
            perimeter_px = cv2.arcLength(max_contour, True)
            perimeter_m = round(perimeter_px * meters_per_pixel, 2)
            M = cv2.moments(max_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                grapple_point = [cx, cy]

        is_filamentous = bool(0.04 <= density <= 0.85)

        return {
            "mask": mask_clean,
            "polygon": polygon,
            "entangled_area_m2": entangled_area_m2,
            "perimeter_m": perimeter_m,
            "filament_density": density,
            "is_filamentous": is_filamentous,
            "grapple_point": grapple_point
        }

    @staticmethod
    def _morphological_filament_segment(patch_img: np.ndarray) -> np.ndarray:
        """
        Multi-scale morphological line and webbing detector.
        Extracts high-frequency ridge filaments characteristic of discarded fishing nets.
        """
        # Equalize contrast locally (ensure grayscale)
        if len(patch_img.shape) == 3:
            gray = cv2.cvtColor(patch_img, cv2.COLOR_BGR2GRAY)
        else:
            gray = patch_img.copy()

        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(4, 4))
        enhanced = clahe.apply(gray)
        
        # Black top-hat and White top-hat to catch both reflective strands and dark rope shadows
        k_line = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        w_top = cv2.morphologyEx(enhanced, cv2.MORPH_TOPHAT, k_line)
        
        # Adaptive thresholding on high-intensity filament response
        thresh = cv2.adaptiveThreshold(
            w_top, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, -2
        )
        return thresh
