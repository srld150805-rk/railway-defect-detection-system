import logging
from pathlib import Path

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, url_for, send_from_directory
from flask_login import current_user, login_required
from sqlalchemy import or_

from app import db
from app.models import Detection, Inspection
from app.services.detection_service import DetectionService
from app.services.segmentation_service import SegmentationService
from app.services.image_service import save_image

bp = Blueprint("inspections", __name__)
logger = logging.getLogger(__name__)


def detector():
    service = current_app.extensions.get("detection_service")
    if service is None:
        service = DetectionService(current_app.config["MODEL_PATH"], current_app.config["CONFIDENCE_THRESHOLD"], current_app.config["USE_MOCK_DETECTOR"])
        current_app.extensions["detection_service"] = service
    return service


def segmentation_service():
    service = current_app.extensions.get("segmentation_service")
    if service is None:
        service = SegmentationService(
            current_app.config["SEGMENTATION_MODEL_PATH"],
            current_app.config["CONFIDENCE_THRESHOLD"],
        )
        current_app.extensions["segmentation_service"] = service
    return service


def owned_inspection(inspection_id):
    inspection = db.get_or_404(Inspection, inspection_id)
    if current_user.role != "ADMIN" and inspection.user_id != current_user.id:
        from flask import abort
        abort(403)
    return inspection


@bp.get("/inspection")
@login_required
def new_inspection():
    return render_template("inspection/new.html")


@bp.post("/api/inspection/analyze")
@login_required
def analyze():
    upload = request.files.get("image")
    if not upload or not upload.filename:
        return jsonify(success=False, error="Select an image to analyze."), 400
    mode = request.form.get("mode", "detection").strip().lower()
    if mode not in {"detection", "segmentation"}:
        return jsonify(success=False, error="Choose detection or segmentation mode."), 400

    try:
        filename, original_path = save_image(upload, current_app.config["UPLOAD_FOLDER"])
    except ValueError as exc:
        return jsonify(success=False, error=str(exc)), 400

    inspection = Inspection(user_id=current_user.id, image_filename=filename, original_image_path=str(original_path), status="PROCESSING", confidence_threshold=current_app.config["CONFIDENCE_THRESHOLD"])
    annotated_path = Path(current_app.config["UPLOAD_FOLDER"]) / "annotated" / filename
    try:
        if mode == "segmentation":
            service = segmentation_service()
            detections = service.segment(original_path, annotated_path)
            model_name = "YOLO11n-seg (experimental)"
        else:
            detections = detector().detect(original_path, annotated_path)
            model_name = "explicit-demo-detector" if current_app.config["USE_MOCK_DETECTOR"] else "configured-yolo-model"
        db.session.add(inspection)
        db.session.flush()
        inspection.annotated_image_path = str(annotated_path)
        inspection.total_detections = len(detections)
        inspection.status = "COMPLETED"
        inspection.model_name = model_name
        for item in detections:
            box = item["bbox"]
            db.session.add(Detection(inspection_id=inspection.id, defect_class=item["class"], confidence=item["confidence"], x1=box[0], y1=box[1], x2=box[2], y2=box[3]))
        db.session.commit()
    except Exception:
        db.session.rollback()
        logger.exception("Inspection processing or persistence failed")
        return jsonify(success=False, error="The inspection could not be completed or saved. Please try again later."), 503
    return jsonify(success=True, inspection_id=inspection.id, mode=mode, detections=detections)


@bp.get("/inspection/<int:inspection_id>")
@login_required
def detail(inspection_id):
    return render_template("inspection/detail.html", inspection=owned_inspection(inspection_id))
    
@bp.get("/api/inspection/<int:inspection_id>")
@login_required
def api_detail(inspection_id):
    inspection = owned_inspection(inspection_id)
    return jsonify(success=True, inspection_id=inspection.id, status=inspection.status, detections=[
        {"class": item.defect_class, "confidence": item.confidence, "bbox": [item.x1, item.y1, item.x2, item.y2]}
        for item in inspection.detections
    ])

@bp.get("/api/inspections")
@login_required
def api_history():
    query = Inspection.query if current_user.role == "ADMIN" else Inspection.query.filter_by(user_id=current_user.id)
    return jsonify(success=True, inspections=[
        {"id": item.id, "status": item.status, "total_detections": item.total_detections, "created_at": item.created_at.isoformat()}
        for item in query.order_by(Inspection.created_at.desc()).all()
    ])


def serialize_inspection(item):
    return {
        "id": item.id,
        "image_filename": item.image_filename,
        "inspected_at": item.created_at.isoformat(),
        "inspection_status": item.status,
        "model_name": item.model_name,
        "detections": [
            {
                "defect_name": detection.defect_class,
                "confidence": detection.confidence,
                "bbox": [detection.x1, detection.y1, detection.x2, detection.y2],
            }
            for detection in item.detections
        ],
    }


@bp.get("/api/history")
@login_required
def history_api():
    query = Inspection.query if current_user.role == "ADMIN" else Inspection.query.filter_by(user_id=current_user.id)
    defect_name = request.args.get("defect_name", "").strip()
    if defect_name:
        if len(defect_name) > 120:
            return jsonify(success=False, error="Invalid defect name."), 400
        query = query.filter(Inspection.detections.any(Detection.defect_class == defect_name))
    records = query.order_by(Inspection.created_at.desc(), Inspection.id.desc()).all()
    return jsonify(success=True, inspections=[serialize_inspection(item) for item in records])


@bp.get("/api/history/<int:inspection_id>")
@login_required
def history_api_detail(inspection_id):
    inspection = owned_inspection(inspection_id)
    return jsonify(success=True, inspection=serialize_inspection(inspection))


@bp.get("/inspections")
@login_required
def history():
    query = Inspection.query if current_user.role == "ADMIN" else Inspection.query.filter_by(user_id=current_user.id)
    term = request.args.get("q", "").strip()
    if term.isdigit():
        query = query.filter(Inspection.id == int(term))
    inspections = query.order_by(Inspection.created_at.desc()).all()
    return render_template("inspection/history.html", inspections=inspections, term=term)


@bp.get("/uploads/<kind>/<path:filename>")
@login_required
def uploaded_file(kind, filename):
    if kind not in {"original", "annotated"}:
        from flask import abort
        abort(404)
    return send_from_directory(Path(current_app.config["UPLOAD_FOLDER"]) / kind, filename)
