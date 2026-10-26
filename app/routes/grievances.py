from datetime import datetime, timezone

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Grievance

bp = Blueprint("grievances", __name__)


@bp.get("/grievances")
@login_required
def index():
    grievances = Grievance.query if current_user.role == "ADMIN" else Grievance.query.filter_by(user_id=current_user.id)
    return render_template("grievances/index.html", grievances=grievances.order_by(Grievance.created_at.desc()).all())


@bp.route("/grievances/new", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        subject = request.form.get("subject", "").strip()
        description = request.form.get("description", "").strip()
        if not subject or not description:
            flash("Subject and description are required.", "error")
        else:
            grievance = Grievance(user_id=current_user.id, subject=subject, description=description, category=request.form.get("category", "OTHER"), priority=request.form.get("priority", "MEDIUM"))
            db.session.add(grievance)
            db.session.commit()
            flash("Grievance submitted successfully.", "success")
            return redirect(url_for("grievances.index"))
    return render_template("grievances/new.html")


@bp.get("/grievances/<int:grievance_id>")
@login_required
def detail(grievance_id):
    grievance = db.get_or_404(Grievance, grievance_id)
    if current_user.role != "ADMIN" and grievance.user_id != current_user.id:
        from flask import abort
        abort(403)
    return render_template("grievances/detail.html", grievance=grievance)


@bp.post("/grievances/<int:grievance_id>/status")
@login_required
def update_status(grievance_id):
    if current_user.role != "ADMIN":
        from flask import abort
        abort(403)
    grievance = db.get_or_404(Grievance, grievance_id)
    grievance.status = request.form.get("status", grievance.status)
    grievance.admin_response = request.form.get("admin_response", "").strip()
    grievance.resolved_at = datetime.now(timezone.utc) if grievance.status == "RESOLVED" else None
    db.session.commit()
    flash("Grievance updated.", "success")
    return redirect(url_for("grievances.detail", grievance_id=grievance.id))
