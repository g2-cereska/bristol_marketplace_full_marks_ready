from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_recall_fscore_support
from torch import nn, optim
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "fruit_split"
ARTIFACT_DIR = Path(__file__).resolve().parent
PLOTS_DIR = ARTIFACT_DIR / "plots"
MODEL_PATH = ARTIFACT_DIR / "best_model.pth"
LABEL_MAP_PATH = ARTIFACT_DIR / "label_map.json"
METRICS_PATH = ARTIFACT_DIR / "cv_metrics.json"

IMAGE_SIZE = 224
BATCH_SIZE = 32
EPOCHS = 5
LEARNING_RATE = 1e-3
SEED = 42


def build_dataloaders() -> tuple[dict[str, datasets.ImageFolder], dict[str, DataLoader]]:
    transforms_map = {
        "train": transforms.Compose([
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(10),
            transforms.ToTensor(),
        ]),
        "val": transforms.Compose([
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
        ]),
        "test": transforms.Compose([
            transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
            transforms.ToTensor(),
        ]),
    }

    image_datasets = {
        split: datasets.ImageFolder(DATA_DIR / split, transform=transforms_map[split])
        for split in ["train", "val", "test"]
    }
    dataloaders = {
        split: DataLoader(image_datasets[split], batch_size=BATCH_SIZE, shuffle=(split == "train"))
        for split in ["train", "val", "test"]
    }
    return image_datasets, dataloaders



def plot_curve(values_train: list[float], values_val: list[float], ylabel: str, filename: Path) -> None:
    plt.figure(figsize=(8, 5))
    plt.plot(values_train, label=f"train {ylabel.lower()}")
    plt.plot(values_val, label=f"val {ylabel.lower()}")
    plt.xlabel("Epoch")
    plt.ylabel(ylabel)
    plt.title(f"Training vs Validation {ylabel}")
    plt.legend()
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()



def plot_confusion(cm, labels: list[str], filename: Path) -> None:
    plt.figure(figsize=(10, 8))
    plt.imshow(cm)
    plt.xticks(range(len(labels)), labels, rotation=90)
    plt.yticks(range(len(labels)), labels)
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")
    for i in range(len(labels)):
        for j in range(len(labels)):
            plt.text(j, i, str(cm[i, j]), ha="center", va="center")
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()



def evaluate(model, loader, device):
    model.eval()
    y_true = []
    y_pred = []
    with torch.no_grad():
        for inputs, labels in loader:
            inputs = inputs.to(device)
            outputs = model(inputs)
            preds = torch.argmax(outputs, dim=1).cpu().tolist()
            y_pred.extend(preds)
            y_true.extend(labels.tolist())
    return y_true, y_pred



def main() -> None:
    torch.manual_seed(SEED)
    PLOTS_DIR.mkdir(parents=True, exist_ok=True)

    if not DATA_DIR.exists():
        raise FileNotFoundError(f"Split dataset folder not found: {DATA_DIR}")

    image_datasets, dataloaders = build_dataloaders()
    class_names = image_datasets["train"].classes
    LABEL_MAP_PATH.write_text(json.dumps({i: name for i, name in enumerate(class_names)}, indent=2))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    model.fc = nn.Linear(model.fc.in_features, len(class_names))
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    train_losses: list[float] = []
    val_losses: list[float] = []
    train_accs: list[float] = []
    val_accs: list[float] = []
    best_val_acc = 0.0

    for epoch in range(EPOCHS):
        print(f"Epoch {epoch + 1}/{EPOCHS}")
        for phase in ["train", "val"]:
            model.train(mode=(phase == "train"))
            running_loss = 0.0
            running_corrects = 0
            total = 0

            for inputs, labels in dataloaders[phase]:
                inputs = inputs.to(device)
                labels = labels.to(device)
                optimizer.zero_grad()

                with torch.set_grad_enabled(phase == "train"):
                    outputs = model(inputs)
                    loss = criterion(outputs, labels)
                    preds = torch.argmax(outputs, dim=1)
                    if phase == "train":
                        loss.backward()
                        optimizer.step()

                running_loss += loss.item() * inputs.size(0)
                running_corrects += (preds == labels).sum().item()
                total += labels.size(0)

            epoch_loss = running_loss / total
            epoch_acc = running_corrects / total
            print(f"{phase}: loss={epoch_loss:.4f}, acc={epoch_acc:.4f}")

            if phase == "train":
                train_losses.append(epoch_loss)
                train_accs.append(epoch_acc)
            else:
                val_losses.append(epoch_loss)
                val_accs.append(epoch_acc)
                if epoch_acc > best_val_acc:
                    best_val_acc = epoch_acc
                    torch.save(model.state_dict(), MODEL_PATH)

    print(f"Best validation accuracy: {best_val_acc:.4f}")
    plot_curve(train_accs, val_accs, "Accuracy", PLOTS_DIR / "cv_accuracy_curve.png")
    plot_curve(train_losses, val_losses, "Loss", PLOTS_DIR / "cv_loss_curve.png")

    model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
    y_true, y_pred = evaluate(model, dataloaders["test"], device)

    accuracy = accuracy_score(y_true, y_pred)
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="weighted", zero_division=0)
    cm = confusion_matrix(y_true, y_pred)
    report = classification_report(y_true, y_pred, target_names=class_names, output_dict=True, zero_division=0)
    plot_confusion(cm, class_names, PLOTS_DIR / "cv_confusion_matrix.png")

    metrics = {
        "dataset": {
            "train_size": len(image_datasets["train"]),
            "val_size": len(image_datasets["val"]),
            "test_size": len(image_datasets["test"]),
            "classes": class_names,
        },
        "model": {
            "name": "resnet18",
            "epochs": EPOCHS,
            "image_size": IMAGE_SIZE,
            "batch_size": BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "device": str(device),
        },
        "results": {
            "accuracy": round(float(accuracy), 4),
            "precision_weighted": round(float(precision), 4),
            "recall_weighted": round(float(recall), 4),
            "f1_weighted": round(float(f1), 4),
            "confusion_matrix": cm.tolist(),
            "classification_report": report,
        },
        "artifacts": {
            "model_path": str(MODEL_PATH),
            "label_map_path": str(LABEL_MAP_PATH),
            "confusion_matrix_plot": str(PLOTS_DIR / "cv_confusion_matrix.png"),
            "accuracy_curve_plot": str(PLOTS_DIR / "cv_accuracy_curve.png"),
            "loss_curve_plot": str(PLOTS_DIR / "cv_loss_curve.png"),
        },
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    print(f"Saved metrics to {METRICS_PATH}")


if __name__ == "__main__":
    main()
