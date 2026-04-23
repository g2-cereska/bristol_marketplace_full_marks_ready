from __future__ import annotations

import json
from pathlib import Path

import torch
from PIL import Image
from torchvision import models, transforms

ARTIFACT_DIR = Path(__file__).resolve().parent
MODEL_PATH = ARTIFACT_DIR / "best_model.pth"
LABEL_MAP_PATH = ARTIFACT_DIR / "label_map.json"
IMAGE_SIZE = 224

TRANSFORM = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
])


class CVPredictor:
    def __init__(self) -> None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")
        if not LABEL_MAP_PATH.exists():
            raise FileNotFoundError(f"Label map not found: {LABEL_MAP_PATH}")

        raw_map = json.loads(LABEL_MAP_PATH.read_text())
        self.labels = [raw_map[str(i)] for i in range(len(raw_map))]
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = models.resnet18(weights=None)
        self.model.fc = torch.nn.Linear(self.model.fc.in_features, len(self.labels))
        self.model.load_state_dict(torch.load(MODEL_PATH, map_location=self.device))
        self.model.eval()
        self.model.to(self.device)

    def predict(self, image_path: str | Path) -> dict[str, object]:
        image = Image.open(image_path).convert("RGB")
        tensor = TRANSFORM(image).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits = self.model(tensor)
            probs = torch.softmax(logits, dim=1)[0].cpu().tolist()
        best_index = max(range(len(probs)), key=lambda idx: probs[idx])
        top3 = sorted(
            [{"label": self.labels[i], "probability": round(float(probs[i]), 4)} for i in range(len(probs))],
            key=lambda item: item["probability"],
            reverse=True,
        )[:3]
        return {
            "predicted_label": self.labels[best_index],
            "confidence": round(float(probs[best_index]), 4),
            "top_3": top3,
        }


if __name__ == "__main__":
    predictor = CVPredictor()
    sample = input("Enter image path: ").strip()
    print(json.dumps(predictor.predict(sample), indent=2))
