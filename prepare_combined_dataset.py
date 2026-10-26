
from pathlib import Path
import shutil
import random
import yaml

# Dataset locations
ROOT = Path(r"C:\Users\srld9\railways")
ORIGINAL = Path(r"C:\Users\srld9\Downloads\RSD-YOLO-Dataset-v1.0")
ROBOFLOW = Path(
    r"C:\Users\srld9\Downloads\Railway Defects.v1-rail-fracture-v1.yolov8"
)
OUTPUT = ROOT / "datasets" / "railway_combined_v1"

CLASS_NAMES = ["spalling", "wheel burn", "squat", "rail_fracture"]
RANDOM_SEED = 42

# Confirm required folders exist
required = [
    ORIGINAL / "images" / "train",
    ORIGINAL / "images" / "val",
    ORIGINAL / "images" / "test",
    ORIGINAL / "labels" / "train",
    ORIGINAL / "labels" / "val",
    ORIGINAL / "labels" / "test",
    ROBOFLOW / "data.yaml",
]

for path in required:
    if not path.exists():
        raise FileNotFoundError(f"Required path not found: {path}")

with open(ROBOFLOW / "data.yaml", encoding="utf-8-sig") as f:
    roboflow_config = yaml.safe_load(f)

names = roboflow_config["names"]
if isinstance(names, list):
    names = {i: name for i, name in enumerate(names)}
else:
    names = {int(k): v for k, v in names.items()}

# Map source class IDs to the four target classes.
# Include only the two explicit broken-rail classes.
source_to_target = {}
for class_id, name in names.items():
    normalized = str(name).strip().lower()
    if normalized in {"broken_rail_low", "broken_rail_medium"}:
        source_to_target[class_id] = 3

print("Broken-rail source classes:")
for class_id, name in names.items():
    if class_id in source_to_target:
        print(f"  {class_id}: {name} -> rail_fracture")

if not source_to_target:
    raise ValueError(
        "No broken_rail_low or broken_rail_medium classes found in data.yaml"
    )

# Do not overwrite an existing prepared dataset.
if OUTPUT.exists():
    raise FileExistsError(
        f"{OUTPUT} already exists. Rename or remove it only after checking it."
    )

random.seed(RANDOM_SEED)
image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
counts = {"train": 0, "val": 0, "test": 0}
label_counts = {"spalling": 0, "wheel burn": 0, "squat": 0, "rail_fracture": 0}

def find_label(label_dir, image_path):
    return label_dir / (image_path.stem + ".txt")

def read_original_labels(label_path):
    rows = []
    if not label_path.exists():
        return rows

    for line in label_path.read_text(encoding="utf-8-sig").splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        try:
            class_id = int(parts[0])
            coords = [float(v) for v in parts[1:]]
        except ValueError:
            continue

        if class_id in (0, 1, 2):
            rows.append(f"{class_id} " + " ".join(map(str, coords)))
            label_counts[CLASS_NAMES[class_id]] += 1
    return rows

def read_roboflow_labels(label_path):
    rows = []
    if not label_path.exists():
        return rows

    for line in label_path.read_text(encoding="utf-8-sig").splitlines():
        parts = line.split()
        if len(parts) != 5:
            continue
        try:
            class_id = int(parts[0])
            coords = [float(v) for v in parts[1:]]
        except ValueError:
            continue

        if class_id in source_to_target:
            # Validate normalized YOLO box values.
            x, y, w, h = coords
            if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < w <= 1 and 0 < h <= 1):
                continue
            rows.append(
                f"3 " + " ".join(f"{v:.6f}" for v in coords)
            )
            label_counts["rail_fracture"] += 1
    return rows


def add_split(source_root, split, source_kind):
    if source_kind == "original":
        image_dir = source_root / "images" / split
        label_dir = source_root / "labels" / split
    else:
        source_split = "valid" if split == "val" else split
        image_dir = source_root / source_split / "images"
        label_dir = source_root / source_split / "labels"
    if not image_dir.exists() or not label_dir.exists():
        raise FileNotFoundError(
            f"Expected images and labels at:\n{image_dir}\n{label_dir}"
        )

    destination_images = OUTPUT / "images" / split
    destination_labels = OUTPUT / "labels" / split
    destination_images.mkdir(parents=True, exist_ok=True)
    destination_labels.mkdir(parents=True, exist_ok=True)

    for image_path in sorted(image_dir.iterdir()):
        if image_path.suffix.lower() not in image_extensions:
            continue

        label_path = find_label(label_dir, image_path)

        if source_kind == "original":
            rows = read_original_labels(label_path)
        else:
            rows = read_roboflow_labels(label_path)

        if not rows:
            continue

        prefix = "rsdd" if source_kind == "original" else "rf"
        new_name = f"{prefix}_{image_path.name}"
        target_image = destination_images / new_name
        target_label = destination_labels / f"{Path(new_name).stem}.txt"

        shutil.copy2(image_path, target_image)
        target_label.write_text(
            "\n".join(rows) + "\n", encoding="utf-8"
        )
        counts[split] += 1


# Original dataset uses train/val/test.
for split in ("train", "val", "test"):
    add_split(ORIGINAL, split, "original")

# Roboflow dataset uses train/valid/test.

for source_split, target_split in (
    ("train", "train"),
    ("valid", "val"),
    ("test", "test"),
):
    add_split(ROBOFLOW, target_split, "roboflow")

# Write configuration for the prepared dataset.
data_yaml = {
    "path": str(OUTPUT).replace("\\", "/"),
    "train": "images/train",
    "val": "images/val",
    "test": "images/test",
    "nc": len(CLASS_NAMES),
    "names": CLASS_NAMES,
}

with open(OUTPUT / "data.yaml", "w", encoding="utf-8") as f:
    yaml.safe_dump(data_yaml, f, sort_keys=False, allow_unicode=True)

print("\nDataset preparation complete.")
print("Output:", OUTPUT)
print("Images included:", counts)
print("Annotated boxes included:", label_counts)
print("Classes:", CLASS_NAMES)
print("\nReview the output and class counts before training.")
