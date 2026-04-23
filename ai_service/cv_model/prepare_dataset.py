from __future__ import annotations

import random
import shutil
from pathlib import Path

# Update these paths on your laptop before running.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT_ROOT / "data" / "CaseStudyDataset"
OUTPUT_DIR = PROJECT_ROOT / "data" / "fruit_split"

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15
SEED = 42
ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def create_dirs(classes: list[str]) -> None:
    for split in ["train", "val", "test"]:
        for cls in classes:
            (OUTPUT_DIR / split / cls).mkdir(parents=True, exist_ok=True)


def list_images(folder: Path) -> list[Path]:
    return [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in ALLOWED_SUFFIXES]


def copy_group(files: list[Path], split: str, cls: str) -> None:
    target_dir = OUTPUT_DIR / split / cls
    for src in files:
        shutil.copy2(src, target_dir / src.name)


def split_class(class_dir: Path) -> tuple[list[Path], list[Path], list[Path]]:
    images = list_images(class_dir)
    random.shuffle(images)
    count = len(images)
    train_end = int(count * TRAIN_RATIO)
    val_end = train_end + int(count * VAL_RATIO)
    return images[:train_end], images[train_end:val_end], images[val_end:]


def main() -> None:
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(f"Source dataset folder not found: {SOURCE_DIR}")

    if abs((TRAIN_RATIO + VAL_RATIO + TEST_RATIO) - 1.0) > 1e-9:
        raise ValueError("Train/val/test ratios must sum to 1.0")

    random.seed(SEED)
    classes = sorted([p.name for p in SOURCE_DIR.iterdir() if p.is_dir()])
    if not classes:
        raise ValueError("No class folders were found in the source dataset.")

    create_dirs(classes)
    summary: list[tuple[str, int, int, int, int]] = []

    for cls in classes:
        class_dir = SOURCE_DIR / cls
        train_files, val_files, test_files = split_class(class_dir)
        copy_group(train_files, "train", cls)
        copy_group(val_files, "val", cls)
        copy_group(test_files, "test", cls)
        summary.append((cls, len(train_files), len(val_files), len(test_files), len(train_files) + len(val_files) + len(test_files)))

    print("Dataset split complete")
    print(f"Source: {SOURCE_DIR}")
    print(f"Output: {OUTPUT_DIR}")
    for cls, train_n, val_n, test_n, total in summary:
        print(f"{cls}: train={train_n}, val={val_n}, test={test_n}, total={total}")


if __name__ == "__main__":
    main()
