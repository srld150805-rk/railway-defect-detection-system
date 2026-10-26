"""Experimental YOLO segmentation inference service for RDDS."""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SegmentationService:
    def __init__(self, model_path, threshold=0.25):
        self.model_path = Path(model_path).resolve()
        self.threshold = float(threshold)
        self.model = None

        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("Confidence threshold must be between 0 and 1.")

        if not self.model_path.is_file():
            logger.warning("Segmentation model file not found: %s", self.model_path)
            return

        try:
            from ultralytics import YOLO
            self.model = YOLO(str(self.model_path))
            logger.info("Loaded experimental segmentation model: %s", self.model_path)
        except Exception:
            logger.exception("Unable to load segmentation model: %s", self.model_path)
            self.model = None

    @property
    def available(self):
        return self.model is not None

    def segment(self, image_path, annotated_path):
        if self.model is None:
            raise RuntimeError(
                "Segmentation model unavailable. Place rdds_yolo11n_seg_best.pt "
                f"at {self.model_path} or configure SEGMENTATION_MODEL_PATH."
            )

        image_path = Path(image_path).resolve()
        annotated_path = Path(annotated_path).resolve()
        if not image_path.is_file():
            raise FileNotFoundError(f"Input image not found: {image_path}")
        annotated_path.parent.mkdir(parents=True, exist_ok=True)

        results = self.model.predict(
            source=str(image_path), imgsz=640, conf=self.threshold, verbose=False
        )
        result = results[0]
        detections = []

        # Segmentation predictions also provide boxes; persist them in the existing
        # Detection table while the rendered output image retains the pixel masks.
        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls[0].item())
                confidence = float(box.conf[0].item())
                coords = [round(float(value), 2) for value in box.xyxy[0].tolist()]
                detections.append({
                    "class": result.names[class_id],
                    "confidence": round(confidence, 4),
                    "bbox": coords,
                })

        result.save(filename=str(annotated_path))
        logger.info("Segmentation completed: %s | %d instances", image_path.name, len(detections))
        return detections
