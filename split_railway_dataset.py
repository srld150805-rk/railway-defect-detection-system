
from pathlib import Path
import random
import shutil

# Source dataset (leave it unchanged)
SOURCE = Path(r"C:\raildata\train")
# New output dataset
OUTPUT = Path(r"C:\rd_v2")

SEED = 42
random.seed(SEED)

image_dir = SOURCE / "images"
label_dir = SOURCE / "labels"

# Supported image formats
extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

images = sorted(
    p for p in image_dir.iterdir()
    if p.is_file() and p.suffix.lower() in extensions
)

if not images:
    raise RuntimeError(f"No images found in {image_dir}")

# Verify every image has a matching label file.
missing_labels = [
    p.name for p in images
    if not (label_dir / f"{p.stem}.txt").is_file()
]

if missing_labels:
    raise RuntimeError(
        f"{len(missing_labels)} images have no label file. "
        f"Example: {missing_labels[:5]}"
    )

# Split images: 70% train, 20% validation, 10% test.
random.shuffle(images)
n = len(images)
n_train = int(n * 0.70)
n_val = int(n * 0.20)

splits = {
    "train": images[:n_train],
    "val": images[n_train:n_train + n_val],
    "test": images[n_train + n_val:],
}

# Never overwrite an existing output dataset.
if OUTPUT.exists():
    raise FileExistsError(
        f"{OUTPUT} already exists. Rename it or choose a new output path."
    )

try:
    for split_name, split_images in splits.items():
        out_images = OUTPUT / split_name / "images"
        out_labels = OUTPUT / split_name / "labels"
        out_images.mkdir(parents=True)
        out_labels.mkdir(parents=True)

        for image_path in split_images:
            label_path = label_dir / f"{image_path.stem}.txt"
            shutil.copy2(image_path, out_images / image_path.name)
            shutil.copy2(label_path, out_labels / label_path.name)

    # Count annotations in each split.
    print("\nDataset split complete:")
    for split_name, split_images in splits.items():
        print(f"{split_name}: {len(split_images)} images")

    print(f"\nOutput: {OUTPUT}")
    print("Original dataset was not modified.")
except Exception:
    shutil.rmtree(OUTPUT, ignore_errors=True)
    raise
