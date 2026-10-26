from pathlib import Path

from flask import Flask, render_template, session
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config import Config
from app.i18n import TRANSLATIONS, translate

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to continue."


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    Path(app.config["UPLOAD_FOLDER"], "original").mkdir(parents=True, exist_ok=True)
    Path(app.config["UPLOAD_FOLDER"], "annotated").mkdir(parents=True, exist_ok=True)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)

    from app import models
    from app.routes import auth, main, inspections, grievances, admin
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(inspections.bp)
    app.register_blueprint(grievances.bp)
    app.register_blueprint(admin.bp)

    @app.context_processor
    def inject_enums():
        language = session.get("language", "en")
        return {"UserRole": models.UserRole, "language": language, "languages": {"en": "English", "hi": "हिन्दी", "kn": "ಕನ್ನಡ"}, "_": lambda key, **values: translate(language, key, **values)}

    with app.app_context():
        db.create_all()

    return app


@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return db.session.get(User, int(user_id))
