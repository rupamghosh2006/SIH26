"""
Acoustic Ping Frequency Classifier Training (Mines vs. Rocks).
Trains and benchmarks Machine Learning (Random Forest, Logistic Regression)
and Deep Learning (PyTorch MLP) models on 60-band sonar backscatter attributes.
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset


class SonarAcousticMLP(nn.Module):
    """Deep Neural Network for 60-band acoustic frequency spectrum classification."""
    def __init__(self, input_dim: int = 60, hidden_dim: int = 64, dropout_rate: float = 0.3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.BatchNorm1d(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_dim, 32),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def load_sonar_dataset(csv_path: str) -> Tuple[np.ndarray, np.ndarray]:
    """Loads sonar dataset, parses 60 frequency attributes and maps targets: R -> 0 (Rock), M -> 1 (Mine)."""
    df = pd.read_csv(csv_path, header=None)
    X = df.iloc[:, :60].values.astype(np.float32)
    y_raw = df.iloc[:, 60].values
    # M = 1 (Mine / Cylindrical Metal), R = 0 (Rock / Natural Benthic)
    y = np.array([1 if val == 'M' else 0 for val in y_raw], dtype=np.int64)
    return X, y


def train_and_evaluate(
    csv_path: str,
    output_dir: str = "backend/models",
    random_seed: int = 42
) -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    out_path = Path(output_dir)

    print("=" * 70)
    print(" Varuna AI: Acoustic Signal Classifier (Mines vs. Rocks)")
    print(f" Dataset source: {csv_path}")
    print("=" * 70)

    X, y = load_sonar_dataset(csv_path)
    print(f"Total Sonar Pings: {len(y)} (Mines: {np.sum(y == 1)}, Rocks: {np.sum(y == 0)})")
    print(f"Feature Vector Dimensions: {X.shape[1]} acoustic frequency energy bands")

    # Stratified Train/Test Split (80% train, 20% test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, stratify=y, random_state=random_seed
    )

    # Feature Normalization
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 1. Random Forest Classifier
    rf_model = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=random_seed)
    rf_model.fit(X_train_scaled, y_train)
    rf_preds = rf_model.predict(X_test_scaled)
    rf_probs = rf_model.predict_proba(X_test_scaled)[:, 1]

    rf_acc = accuracy_score(y_test, rf_preds)
    rf_f1 = f1_score(y_test, rf_preds)
    rf_auc = roc_auc_score(y_test, rf_probs)
    print(f"\n[Random Forest] Test Accuracy: {rf_acc:.4f} | F1: {rf_f1:.4f} | ROC-AUC: {rf_auc:.4f}")

    # 2. Logistic Regression Classifier
    lr_model = LogisticRegression(max_iter=1000, random_state=random_seed)
    lr_model.fit(X_train_scaled, y_train)
    lr_preds = lr_model.predict(X_test_scaled)
    lr_probs = lr_model.predict_proba(X_test_scaled)[:, 1]

    lr_acc = accuracy_score(y_test, lr_preds)
    lr_f1 = f1_score(y_test, lr_preds)
    lr_auc = roc_auc_score(y_test, lr_probs)
    print(f"[Logistic Reg ] Test Accuracy: {lr_acc:.4f} | F1: {lr_f1:.4f} | ROC-AUC: {lr_auc:.4f}")

    # 3. PyTorch Deep Neural Network (MLP)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    mlp_model = SonarAcousticMLP(input_dim=60).to(device)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(mlp_model.parameters(), lr=0.003, weight_decay=1e-4)

    train_tensor_x = torch.tensor(X_train_scaled, dtype=torch.float32)
    train_tensor_y = torch.tensor(y_train, dtype=torch.float32).unsqueeze(1)
    train_loader = DataLoader(TensorDataset(train_tensor_x, train_tensor_y), batch_size=16, shuffle=True)

    mlp_model.train()
    for epoch in range(60):
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            optimizer.zero_grad()
            outputs = mlp_model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

    mlp_model.eval()
    with torch.no_grad():
        test_tensor_x = torch.tensor(X_test_scaled, dtype=torch.float32).to(device)
        mlp_probs = mlp_model(test_tensor_x).cpu().numpy().flatten()
        mlp_preds = (mlp_probs >= 0.5).astype(int)

    mlp_acc = accuracy_score(y_test, mlp_preds)
    mlp_f1 = f1_score(y_test, mlp_preds)
    mlp_auc = roc_auc_score(y_test, mlp_probs)
    print(f"[PyTorch MLP  ] Test Accuracy: {mlp_acc:.4f} | F1: {mlp_f1:.4f} | ROC-AUC: {mlp_auc:.4f}")

    # Determine best model for deployment
    models_dict = {
        "RandomForest": (rf_model, rf_acc, rf_f1, rf_auc, rf_preds),
        "PyTorchMLP": (mlp_model, mlp_acc, mlp_f1, mlp_auc, mlp_preds),
        "LogisticRegression": (lr_model, lr_acc, lr_f1, lr_auc, lr_preds)
    }
    best_name = max(models_dict.keys(), key=lambda k: models_dict[k][1])
    best_model, best_acc, best_f1, best_auc, best_preds = models_dict[best_name]

    print(f"\n>> Selected Best Model: {best_name} (Accuracy: {best_acc * 100:.2f}%)")
    print(f"\nClassification Report ({best_name}):")
    print(classification_report(y_test, best_preds, target_names=["Rock (Natural)", "Mine (Threat)"]))

    # Save artifacts
    joblib_path = str(out_path / "sonar_mine_rock_classifier.joblib")
    scaler_path = str(out_path / "sonar_scaler.joblib")
    pytorch_path = str(out_path / "sonar_mine_rock_mlp.pt")
    metrics_path = str(out_path / "sonar_classifier_metrics.json")

    joblib.dump(rf_model, joblib_path)
    joblib.dump(scaler, scaler_path)
    torch.save(mlp_model.state_dict(), pytorch_path)

    metrics = {
        "selected_model": best_name,
        "test_accuracy": float(best_acc),
        "test_f1": float(best_f1),
        "test_roc_auc": float(best_auc),
        "random_forest": {"accuracy": float(rf_acc), "f1": float(rf_f1), "roc_auc": float(rf_auc)},
        "pytorch_mlp": {"accuracy": float(mlp_acc), "f1": float(mlp_f1), "roc_auc": float(mlp_auc)},
        "logistic_regression": {"accuracy": float(lr_acc), "f1": float(lr_f1), "roc_auc": float(lr_auc)},
        "classes": {0: "Rock", 1: "Mine"},
        "confusion_matrix": confusion_matrix(y_test, best_preds).tolist()
    }
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"[Varuna AI] Classifier bundle saved to:")
    print(f"  - Scikit-Learn Pipeline: {joblib_path}")
    print(f"  - Normalization Scaler: {scaler_path}")
    print(f"  - PyTorch Weights:      {pytorch_path}")
    print(f"  - Metrics Summary:      {metrics_path}")
    print("=" * 70)

    return metrics


if __name__ == "__main__":
    default_csv = r"C:\Users\Rupam Ghosh\.cache\kagglehub\datasets\mattcarter865\mines-vs-rocks\versions\1\sonar.all-data.csv"
    train_and_evaluate(default_csv)
