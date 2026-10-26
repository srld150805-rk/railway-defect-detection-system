import uuid
from pathlib import Path

from PIL import Image
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def save_image(file_storage, upload_root):
    original_name = secure_filename(file_storage.filename or "")
    extension = Path(original_name).suffix.lower().lstrip(".")
    if not original_name or extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Upload a JPG, JPEG, PNG, or WEBP image.")
    try:
        image = Image.open(file_storage.stream)
        image.verify()
        file_storage.stream.seek(0)
    except Exception as exc:
        raise ValueError("The uploaded file is not a valid image.") from exc
    filename = f"{uuid.uuid4().hex}.{extension}"
    destination = Path(upload_root) / "original" / filename
    file_storage.save(destination)
    return filename, destination
