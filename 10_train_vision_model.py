#!/usr/bin/env python3
"""
10_train_vision_model.py — Train Deep Learning Capsule Success Models

Trains a convolutional neural network (MobileNetV3 / EfficientNet) to predict:
1. 'indie'  — Indie Review Milestone Tier (0, 1-5, 6-10, 11-100, 100-500 reviews)
2. 'global' — Macro Commercial Steam Tier (Mega-Hits, Solid Indies, Moderate, etc.)

Uses Apple Silicon MPS GPU acceleration for fast training.

Usage:
    python 10_train_vision_model.py --dataset indie --epochs 10 --batch-size 32
    python 10_train_vision_model.py --dataset global --epochs 10 --batch-size 32
"""

import argparse
import json
import os
import time
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "models")

os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_device():
    """Detect fastest available acceleration hardware (MPS Apple Silicon, CUDA, or CPU)."""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    else:
        return torch.device("cpu")


def train_model(dataset_name: str, epochs: int = 10, batch_size: int = 32, lr: float = 0.001):
    device = get_device()
    print(f"\n🚀 Training Steam Capsule Vision Model [{dataset_name.upper()}] on device: {device}")

    data_dir = os.path.join(DATA_DIR, f"ml_{dataset_name}" if dataset_name == "global" else "ml_indie_milestones")
    train_dir = os.path.join(data_dir, "train")
    val_dir = os.path.join(data_dir, "val")

    if not os.path.exists(train_dir):
        print(f"❌ Training directory not found: {train_dir}. Run 9_prepare_ml_dataset.py first.")
        return

    # Image transformations: Resize preserving standard 2:1 ratio (224x112 or 224x224)
    data_transforms = {
        "train": transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.RandomHorizontalFlip(p=0.3),
            transforms.ColorJitter(brightness=0.1, contrast=0.1, saturation=0.1),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
        "val": transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ]),
    }

    # Load datasets
    image_datasets = {
        "train": datasets.ImageFolder(train_dir, data_transforms["train"]),
        "val": datasets.ImageFolder(val_dir, data_transforms["val"]),
    }

    dataloaders = {
        "train": DataLoader(image_datasets["train"], batch_size=batch_size, shuffle=True, num_workers=2),
        "val": DataLoader(image_datasets["val"], batch_size=batch_size, shuffle=False, num_workers=2),
    }

    class_names = image_datasets["train"].classes
    num_classes = len(class_names)

    print(f"   Classes ({num_classes}): {class_names}")
    print(f"   Train samples: {len(image_datasets['train']):,} | Val samples: {len(image_datasets['val']):,}")

    # Load pretrained MobileNetV3-Small
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)

    # Replace classifier head for our number of classes
    in_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(in_features, num_classes)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_acc = 0.0
    best_model_path = os.path.join(OUTPUT_DIR, f"{dataset_name}_model.pth")
    meta_path = os.path.join(OUTPUT_DIR, f"{dataset_name}_classes.json")

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump({"dataset": dataset_name, "classes": class_names, "num_classes": num_classes}, f, indent=2)

    start_time = time.time()

    for epoch in range(epochs):
        print(f"\nEpoch {epoch+1}/{epochs}")
        print("-" * 35)

        for phase in ["train", "val"]:
            if phase == "train":
                model.train()
            else:
                model.eval()

            running_loss = 0.0
            running_corrects = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)

                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == "train"):
                    outputs = model(inputs)
                    _, preds = torch.max(outputs, 1)
                    loss = criterion(outputs, labels)

                    if phase == "train":
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += torch.sum(preds == labels.data)

            if phase == "train":
                scheduler.step()

            epoch_loss = running_loss / len(image_datasets[phase])
            epoch_acc = (running_corrects.float() / len(image_datasets[phase])).item()

            print(f"{phase.capitalize():5s} Loss: {epoch_loss:.4f}  Acc: {epoch_acc:.4f} ({running_corrects}/{len(image_datasets[phase])})")

            # Save best checkpoint
            if phase == "val" and epoch_acc > best_acc:
                best_acc = epoch_acc
                torch.save(model.state_dict(), best_model_path)
                print(f"  ⭐ Saved new best model checkpoint (Val Acc: {best_acc:.4f})")

    elapsed = time.time() - start_time
    print(f"\n{'='*55}")
    print(f"🎉 Training Complete in {elapsed/60:.1f} minutes!")
    print(f"   Best Val Accuracy: {best_acc:.4f}")
    print(f"   Saved Checkpoint:  {best_model_path}")
    print(f"   Classes Index:     {meta_path}")
    print(f"{'='*55}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Capsule Vision Neural Network")
    parser.add_argument("--dataset", choices=["indie", "global"], default="indie",
                        help="Which model to train: 'indie' (milestone brackets) or 'global' (macro sales tiers)")
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs. Default: 10")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size. Default: 32")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate. Default: 0.001")
    args = parser.parse_args()

    train_model(dataset_name=args.dataset, epochs=args.epochs, batch_size=args.batch_size, lr=args.lr)
