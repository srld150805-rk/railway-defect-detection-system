"""Create clearly labelled development accounts for local demonstrations."""

from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    accounts = [
        ("Demo Admin", "admin@example.test", "ADMIN"),
        ("Demo Inspector", "inspector@example.test", "INSPECTOR"),
        ("Demo User", "user@example.test", "USER"),
    ]
    for name, email, role in accounts:
        if not User.query.filter_by(email=email).first():
            user = User(name=name, email=email, role=role)
            user.set_password("change-this-demo-password")
            db.session.add(user)
    db.session.commit()
    print("Development accounts created with password: change-this-demo-password")