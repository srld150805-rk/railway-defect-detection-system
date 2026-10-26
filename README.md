# Railway Defect Detection System

Railway Defect Detection System is a Flask-based railway image inspection and issue-management application. It stores authenticated inspection records, runs a replaceable YOLO-family detection service, visualizes annotated evidence, and supports human-reviewed reports and grievances.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python run.py
```

Open `http://127.0.0.1:5000`. The database is created in `instance/railway.db` on first startup. For real AI inference, place the trained `.pt` file at the configured `MODEL_PATH`; the default is `models/railway_defect_model.pt`. The app does not fabricate predictions when a model is missing. For an explicit local UI smoke test only, set `USE_MOCK_DETECTOR=true` in `.env`.

## SQLite inspection history

The app uses its existing Flask-SQLAlchemy SQLite database (`DATABASE_URL`, defaulting to the project instance directory). Startup calls `create_all`, which creates missing tables without erasing existing inspection data. `inspections` stores one row per successful analyzed upload, and `detections` stores zero or more real model detections linked by `inspection_id`, including the model class name, confidence from 0 to 1, and bounding-box coordinates. A successful inspection with no detections is stored with `COMPLETED` status and an empty detections list. Inference or database failures return an error and roll back the inspection transaction.

Authenticated API endpoints are `GET /api/history`, `GET /api/history?defect_name=<model-class>`, and `GET /api/history/<id>`. Records are scoped to the signed-in user; administrators can see all records. The existing `/inspections` page refreshes from this API. The existing `/api/inspections` route remains available for compatibility. There is no history deletion endpoint.

To verify persistence, sign in, submit an image using the configured YOLO model, then refresh `/inspections` or call `/api/history`. Restart `python run.py` and fetch the history again. The SQLite tables can be inspected with `sqlite3 instance/railway.db` (when the default URL is in use) and `.tables` / `SELECT * FROM inspections;` / `SELECT * FROM detections;`. Set a strong `SECRET_KEY` and disable `USE_MOCK_DETECTOR` for deployment; the demo detector is not a source of real predictions.

## Configuration

`SECRET_KEY`, `DATABASE_URL`, `UPLOAD_FOLDER`, `MODEL_PATH`, `CONFIDENCE_THRESHOLD`, `MAX_CONTENT_LENGTH`, and `USE_MOCK_DETECTOR` are supported. Uploaded originals and annotated images are stored under `uploads/` and are excluded from git.

## Architecture

- `app/models.py`: SQLAlchemy entities and relationships for users, inspections, detections, reports, and grievances.
- `app/routes/`: authentication, dashboard, inspection, report, grievance, and admin endpoints.
- `app/services/detection_service.py`: model loading and application-neutral detection output.
- `app/services/image_service.py`: extension, decoded-image, filename, and storage validation.
- `app/templates/` and `app/static/`: shared responsive server-rendered interface.

All protected records enforce ownership on the server. Passwords are hashed, forms use CSRF protection, and uploaded paths are generated rather than derived from user filenames.

## Appearance and language

Use the theme control in the shared navigation to switch between light and dark mode. The choice is remembered in the browser with `localStorage`. Use the language selector to switch the interface between English, Hindi, and Kannada; the selected language is stored in the Flask session and applies across pages.

## Tests and limitations

Run `pytest` after installing dependencies. This starter includes the complete core workflow and data model, but production deployment should add rate limiting, object storage, formal Alembic migration files, malware scanning, and a fuller admin audit log before safety-critical use. AI results are decision support and do not certify track safety.
