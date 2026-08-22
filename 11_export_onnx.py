#!/usr/bin/env python3
"""
11_export_onnx.py — Export Trained PyTorch Vision Models to ONNX for Web Browser Inference

Exports trained .pth checkpoints to optimized .onnx files for client-side
inference in web/app.js using onnxruntime-web.

Usage:
    python 11_export_onnx.py --dataset indie
    python 11_export_onnx.py --dataset global
"""

import argparse
import json
import os
import sys
import shutil
import torch
import torch.nn as nn
from torchvision import models
import onnx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "output", "models")
WEB_MODELS_DIR = os.path.join(BASE_DIR, "web", "models")

os.makedirs(WEB_MODELS_DIR, exist_ok=True)


def export_onnx(dataset_name: str):
    pth_path = os.path.join(MODELS_DIR, f"{dataset_name}_model.pth")
    meta_path = os.path.join(MODELS_DIR, f"{dataset_name}_classes.json")
    onnx_path = os.path.join(MODELS_DIR, f"{dataset_name}_model.onnx")
    web_onnx_path = os.path.join(WEB_MODELS_DIR, f"capsulu_{dataset_name}_model.onnx")
    web_meta_path = os.path.join(WEB_MODELS_DIR, f"capsulu_{dataset_name}_classes.json")

    if not os.path.exists(pth_path):
        print(f"❌ Model checkpoint not found: {pth_path}. Train the model first.")
        return

    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    class_names = meta["classes"]
    num_classes = len(class_names)

    print(f"\n📦 Exporting [{dataset_name.upper()}] PyTorch Model to ONNX...")
    print(f"   Classes ({num_classes}): {class_names}")

    # Build model architecture
    model = models.mobilenet_v3_small(weights=None)
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)

    # Load weights
    state_dict = torch.load(pth_path, map_location="cpu")
    model.load_state_dict(state_dict)
    model.eval()

    # Create dummy input tensor: [batch_size, channels, height, width]
    dummy_input = torch.randn(1, 3, 224, 224, requires_grad=False)

    # Export to self-contained single ONNX file
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=17,
        do_constant_folding=True,
        input_names=["input"],
        output_names=["probabilities"],
        dynamic_axes={"input": {0: "batch_size"}, "probabilities": {0: "batch_size"}},
        dynamo=False
    )

    # Verify ONNX model
    onnx_model = onnx.load(onnx_path)
    onnx.checker.check_model(onnx_model)

    file_size_mb = os.path.getsize(onnx_path) / (1024 * 1024)
    print(f"   ✅ Validated ONNX Model ({file_size_mb:.2f} MB) → {onnx_path}")

    # Copy to web/models/ for frontend browser serving
    shutil.copy2(onnx_path, web_onnx_path)
    shutil.copy2(meta_path, web_meta_path)
    print(f"   🌐 Copied to Web App Directory → {web_onnx_path}")
    print(f"   🌐 Copied Classes Meta → {web_meta_path}")

    print(f"\n🎉 Model ready for browser ONNX Web runtime!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export PyTorch Model to ONNX")
    parser.add_argument("--dataset", choices=["indie", "global"], default="indie")
    args = parser.parse_args()

    export_onnx(args.dataset)
