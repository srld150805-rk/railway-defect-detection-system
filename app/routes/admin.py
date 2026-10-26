from functools import wraps

from flask import Blueprint, abort, redirect, render_template, url_for
from flask_login import current_user, login_required

from app import db
from app.models import Grievance, Inspection, User

bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "ADMIN":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


@bp.get("")
@admin_required
def dashboard():
    return render_template("admin/dashboard.html", users=User.query.count(), inspections=Inspection.query.count(), grievances=Grievance.query.filter(Grievance.status.in_(["SUBMITTED", "UNDER_REVIEW", "IN_PROGRESS"])).count())


@bp.get("/users")
@admin_required
def users():
    return render_template("admin/users.html", users=User.query.order_by(User.created_at.desc()).all())


@bp.post("/users/<int:user_id>/toggle")
@admin_required
def toggle_user(user_id):
    user = db.get_or_404(User, user_id)
    if user.id == current_user.id:
        return redirect(url_for("admin.users"))
    user.is_active = not user.is_active
    db.session.commit()
    return redirect(url_for("admin.users"))
