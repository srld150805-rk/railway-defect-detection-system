
import logging
from pathlib import Path

from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


class DetectionService:
    def __init__(self, model_path, threshold=0.25, use_mock=False):
        self.model_path = Path(model_path).resolve()
        self.threshold = float(threshold)
        self.use_mock = bool(use_mock)
        self.model = None

        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0 and 1.")

        if self.use_mock:
            logger.warning("Using DEMO detector, not the trained YOLO model.")
            return

        if not self.model_path.is_file():
            logger.error("Model file not found: %s", self.model_path)
            return

        try:
            from ultralytics import YOLO

            self.model = YOLO(str(self.model_path))
            logger.info(
                "Loaded YOLO model: %s | Classes: %s",
                self.model_path,
                self.model.names,
            )
        except Exception:
            logger.exception(
                "Unable to load detection model: %s",
                self.model_path,
            )
            self.model = None

    @property
    def available(self):
        return self.use_mock or self.model is not None

    def detect(self, image_path, annotated_path):
        if self.use_mock:
            return self._mock_detect(image_path, annotated_path)

        if self.model is None:
            raise RuntimeError(
                f"Detection model unavailable: {self.model_path}"
            )

        image_path = Path(image_path).resolve()
        annotated_path = Path(annotated_path).resolve()

        if not image_path.is_file():
            raise FileNotFoundError(
                f"Input image not found: {image_path}"
            )

        # Ensure the destination directory exists.
        annotated_path.parent.mkdir(parents=True, exist_ok=True)

        results = self.model.predict(
            source=str(image_path),
            imgsz=640,
            conf=self.threshold,
            verbose=False,
        )

        result = results[0]
        detections = []

        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                coords = [
                    round(float(value), 2)
                    for value in box.xyxy[0].tolist()
                ]

                detections.append({
                    "class": result.names[class_id],
                    "confidence": round(confidence, 4),
                    "bbox": coords,
                })

        # Save the image with YOLO's annotated bounding boxes.
        result.save(filename=str(annotated_path))

        logger.info(
            "Detection completed: %s | %d detections",
            image_path.name,
            len(detections),
        )

        return detections

    def _mock_detect(self, image_path, annotated_path):
        annotated_path = Path(annotated_path).resolve()
        annotated_path.parent.mkdir(parents=True, exist_ok=True)

        with Image.open(image_path) as source:
            image = source.convert("RGB")

        draw = ImageDraw.Draw(image)

        x1 = image.width * 0.2
        y1 = image.height * 0.25
        x2 = image.width * 0.55
        y2 = image.height * 0.65

        draw.rectangle(
            (x1, y1, x2, y2),
            outline="#e29b2d",
            width=4,
        )
        draw.text(
            (x1, max(0, y1 - 20)),
            "DEMO DETECTOR",
            fill="#e29b2d",
        )

        image.save(annotated_path)

        return [{
            "class": "demo_surface_anomaly",
            "confidence": 0.81,
            "bbox": [x1, y1, x2, y2],
        }]
