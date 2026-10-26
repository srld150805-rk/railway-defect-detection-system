from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from sqlalchemy import func

from app import db
from app.models import Grievance, Inspection, User

bp = Blueprint("main", __name__)


@bp.post("/preferences/language")
def set_language():
    language = request.form.get("language", "en")
    if language not in {"en", "hi", "kn"}:
        language = "en"
    session["language"] = language
    return redirect(request.referrer or url_for("main.home"))


@bp.get("/")
def home():
    return render_template("home.html")


@bp.get("/dashboard")
@login_required
def dashboard():
    inspections = Inspection.query.filter_by(user_id=current_user.id)
    grievances = Grievance.query.filter_by(user_id=current_user.id)
    if current_user.role == "ADMIN":
        inspections = Inspection.query
        grievances = Grievance.query
    stats = {
        "inspections": inspections.count(),
        "detections": inspections.with_entities(func.coalesce(func.sum(Inspection.total_detections), 0)).scalar(),
        "grievances": grievances.filter(Grievance.status.in_(["SUBMITTED", "UNDER_REVIEW", "IN_PROGRESS"])).count(),
    }
    recent = inspections.order_by(Inspection.created_at.desc()).limit(5).all()
    return render_template("dashboard.html", stats=stats, recent=recent)


@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        if not name or not email:
            flash("Name and email are required.", "error")
        else:
            existing = db.session.scalar(db.select(User).where(User.email == email, User.id != current_user.id))
            if existing:
                flash("That email is already in use.", "error")
            else:
                current_user.name = name
                current_user.email = email
                db.session.commit()
                flash("Profile updated successfully.", "success")
                return redirect(url_for("main.profile"))
    return render_template("profile.html", user=current_user)
