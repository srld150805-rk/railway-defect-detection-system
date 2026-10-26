
from pathlib import Path
import shutil
import yaml

OLD = Path(r"C:\Users\srld9\Downloads\RSD-YOLO-Dataset-v1.0")
NEW = Path(r"C:\rd_v2")
OUT = Path(r"C:\railway_7class")

CLASSES = [
    "spalling",
    "wheel_burn",
    "squat",
    "missing_fastener",
    "missing_fishplate_bolt",
    "rail_break",
    "railway_joint_defect",
]

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

if OUT.exists():
    raise FileExistsError(
        f"{OUT} already exists. Stop; do not delete it automatically."
    )


def get_images(folder):
    return sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def remap_label(src, dst, offset, limit):
    lines = []

    for line in src.read_text(encoding="utf-8").splitlines():
        parts = line.split()

        # Preserve empty label files.
        if not parts:
            continue

        class_id = int(parts[0])
        if not 0 <= class_id < limit:
            raise ValueError(
                f"Unexpected class ID {class_id} in {src}"
            )

        parts[0] = str(class_id + offset)
        lines.append(" ".join(parts))

    dst.write_text(
        "\n".join(lines) + ("\n" if lines else ""),
        encoding="utf-8",
    )


def copy_split(source, split, target, offset, limit, prefix):
    # Original dataset and new dataset use different layouts.
    if offset == 0:
        img_dir = source / "images" / split
        lab_dir = source / "labels" / split
    else:
        img_dir = source / split / "images"
        lab_dir = source / split / "labels"

    if not img_dir.is_dir() or not lab_dir.is_dir():
        raise FileNotFoundError(
            f"Missing image or label folder for {split}: "
            f"{img_dir} / {lab_dir}"
        )

    out_img = target / split / "images"
    out_lab = target / split / "labels"
    out_img.mkdir(parents=True, exist_ok=True)
    out_lab.mkdir(parents=True, exist_ok=True)

    images = get_images(img_dir)

    for img in images:
        label = lab_dir / f"{img.stem}.txt"
        if not label.is_file():
            raise FileNotFoundError(f"Missing label for {img}")

        new_stem = f"{prefix}_{img.stem}"
        out_image = out_img / f"{new_stem}{img.suffix.lower()}"
        out_label = out_lab / f"{new_stem}.txt"

        shutil.copy2(img, out_image)
        remap_label(label, out_label, offset, limit)

    return len(images)


def main():
    if not OLD.is_dir() or not NEW.is_dir():
        raise FileNotFoundError("A source dataset folder was not found.")

    # Check source image-label counts before creating output.
    for split in ("train", "val", "test"):
        for source, is_old in ((OLD, True), (NEW, False)):
            if is_old:
                img_dir = source / "images" / split
                lab_dir = source / "labels" / split
            else:
                img_dir = source / split / "images"
                lab_dir = source / split / "labels"

            images = get_images(img_dir)
            missing = [
                img.name for img in images
                if not (lab_dir / f"{img.stem}.txt").is_file()
            ]
            if missing:
                raise FileNotFoundError(
                    f"{split}: {len(missing)} missing labels; "
                    f"examples: {missing[:3]}"
                )

    OUT.mkdir(parents=True)
    try:
        for split in ("train", "val", "test"):
            old_count = copy_split(
                OLD, split, OUT, 0, 3, "old"
            )
            new_count = copy_split(
                NEW, split, OUT, 3, 4, "new"
            )
            print(
                f"{split}: {old_count} original + "
                f"{new_count} new = {old_count + new_count}"
            )

        config = {
            "path": str(OUT).replace("\\", "/"),
            "train": "train/images",
            "val": "val/images",
            "test": "test/images",
            "nc": len(CLASSES),
            "names": CLASSES,
        }

        with (OUT / "data.yaml").open(
            "w", encoding="utf-8"
        ) as file:
            yaml.safe_dump(config, file, sort_keys=False)

        print(f"\nCombined dataset created: {OUT}")
        print("Source datasets and existing model were not modified.")

    except Exception:
        # Remove only the output created by this run.
        shutil.rmtree(OUT, ignore_errors=True)
        raise


if __name__ == "__main__":
    main()
