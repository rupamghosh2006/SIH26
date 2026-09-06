"""
Training / Weight Generation Script for Ghost Net (ALDFG) U-Net Segmentation.
Generates synthetic sonar patches with realistic fibrous net patterns,
tangled meshes, acoustic shadows, and background seafloor reverberation,
then trains and exports the PyTorch U-Net model weights to backend/models/unet_ghostnet.pt.
"""

import os
import random
import numpy as np
import cv2

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

if TORCH_AVAILABLE:
    try:
        from .unet_segmentation import GhostNetUNet
    except ImportError:
        from ai_pipeline.unet_segmentation import GhostNetUNet


class SyntheticGhostNetDataset:
    """Generates synthetic sonar patches with realistic net filaments and ground truth masks."""
    def __init__(self, num_samples: int = 120, patch_size: int = 128):
        self.num_samples = num_samples
        self.patch_size = patch_size

    def __len__(self):
        return self.num_samples

    def __getitem__(self, idx):
        size = self.patch_size
        img = np.random.normal(70, 18, (size, size)).astype(np.float32)
        mask = np.zeros((size, size), dtype=np.float32)

        # Draw seafloor speckle noise
        speckle = np.random.exponential(scale=12.0, size=(size, size)).astype(np.float32)
        img = np.clip(img + speckle, 0, 255)

        # 80% of samples contain ghost net filaments
        has_net = (idx % 5 != 0)
        if has_net:
            num_strands = random.randint(6, 18)
            cx, cy = random.randint(30, size - 30), random.randint(30, size - 30)
            
            for _ in range(num_strands):
                # Random curve / spline through net cluster
                pts = []
                num_pts = random.randint(3, 5)
                for _ in range(num_pts):
                    px = int(np.clip(cx + np.random.normal(0, 18), 5, size - 5))
                    py = int(np.clip(cy + np.random.normal(0, 18), 5, size - 5))
                    pts.append([px, py])
                pts = np.array(pts, dtype=np.int32)

                # Draw strand on mask and image
                thickness = random.choice([1, 2])
                cv2.polylines(mask, [pts], False, 1.0, thickness)
                
                # Highlight reflection
                cv2.polylines(img, [pts], False, float(random.randint(210, 255)), thickness)
                
                # Associated acoustic shadow behind highlight
                shadow_offset = random.randint(2, 6)
                shadow_pts = pts + np.array([shadow_offset, 0])
                cv2.polylines(img, [shadow_pts], False, float(random.randint(10, 35)), thickness)

        # Convert to PyTorch tensors [1, H, W]
        img_tensor = torch.from_numpy(img / 255.0).unsqueeze(0).float()
        mask_tensor = torch.from_numpy(mask).unsqueeze(0).float()
        return img_tensor, mask_tensor


def train_and_save_model(output_path: str, epochs: int = 5):
    if not TORCH_AVAILABLE:
        print("[Train GhostNet] PyTorch is not available. Skipping model training.")
        return False

    print(f"[Train GhostNet] Starting synthetic U-Net training ({epochs} epochs)...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    model = GhostNetUNet(in_channels=1, out_channels=1).to(device)
    optimizer = optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
    criterion = nn.BCELoss()

    dataset = SyntheticGhostNetDataset(num_samples=80, patch_size=128)
    loader = DataLoader(dataset, batch_size=8, shuffle=True)

    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        for images, masks in loader:
            images = images.to(device)
            masks = masks.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, masks)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
        
        print(f"  Epoch {epoch+1}/{epochs} - Loss: {epoch_loss/len(loader):.4f}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    torch.save(model.state_dict(), output_path)
    print(f"[Train GhostNet] Successfully saved trained U-Net weights to {output_path}")
    return True


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_file = os.path.join(base_dir, "models", "unet_ghostnet.pt")
    train_and_save_model(out_file)
