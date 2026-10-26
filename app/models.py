from datetime import datetime, timezone
from enum import Enum

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db


def utcnow():
    return datetime.now(timezone.utc)


class UserRole(str, Enum):
    USER = "USER"
    INSPECTOR = "INSPECTOR"
    ADMIN = "ADMIN"


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=UserRole.USER.value)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    inspections = db.relationship("Inspection", back_populates="user", cascade="all, delete-orphan")
    reports = db.relationship("Report", back_populates="reporter")
    grievances = db.relationship("Grievance", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Inspection(db.Model):
    __tablename__ = "inspections"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    image_filename = db.Column(db.String(255), nullable=False)
    original_image_path = db.Column(db.String(500), nullable=False)
    annotated_image_path = db.Column(db.String(500))
    inspection_date = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="PROCESSING")
    total_detections = db.Column(db.Integer, nullable=False, default=0)
    model_name = db.Column(db.String(120))
    confidence_threshold = db.Column(db.Float)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    user = db.relationship("User", back_populates="inspections")
    detections = db.relationship("Detection", back_populates="inspection", cascade="all, delete-orphan")
    reports = db.relationship("Report", back_populates="inspection", cascade="all, delete-orphan")


class Detection(db.Model):
    __tablename__ = "detections"
    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey("inspections.id"), nullable=False, index=True)
    defect_class = db.Column(db.String(120), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    x1 = db.Column(db.Float, nullable=False)
    y1 = db.Column(db.Float, nullable=False)
    x2 = db.Column(db.Float, nullable=False)
    y2 = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    inspection = db.relationship("Inspection", back_populates="detections")


class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.Integer, primary_key=True)
    inspection_id = db.Column(db.Integer, db.ForeignKey("inspections.id"), nullable=False)
    reported_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False, default="MEDIUM", index=True)
    location = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False, default="OPEN", index=True)
    admin_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    inspection = db.relationship("Inspection", back_populates="reports")
    reporter = db.relationship("User", back_populates="reports")


class Grievance(db.Model):
    __tablename__ = "grievances"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(40), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="MEDIUM", index=True)
    status = db.Column(db.String(20), nullable=False, default="SUBMITTED", index=True)
    admin_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
    resolved_at = db.Column(db.DateTime(timezone=True))
    user = db.relationship("User", back_populates="grievances")
