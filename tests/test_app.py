import io

import pytest

from app import create_app, db
from config import Config


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    USE_MOCK_DETECTOR = True


@pytest.fixture
def client(tmp_path):
    TestConfig.UPLOAD_FOLDER = str(tmp_path / "uploads")
    app = create_app(TestConfig)
    with app.test_client() as client:
        with app.app_context():
            db.drop_all()
            db.create_all()
        yield client


def register(client, email="user@example.com"):
    return client.post("/register", data={"name": "Test User", "email": email, "password": "password123", "confirmation": "password123"}, follow_redirects=True)


def login(client, email="user@example.com"):
    return client.post("/login", data={"email": email, "password": "password123"}, follow_redirects=True)


def test_registration_login_and_dashboard(client):
    response = register(client)
    assert b"Account created" in response.data
    response = login(client)
    assert b"Good to see you" in response.data
    assert b"authenticated-nav" in response.data
    assert b"guest-nav" not in response.data


def test_inspection_upload_creates_result(client):
    register(client)
    login(client)
    from PIL import Image
    image = Image.new("RGB", (200, 120), "white")
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    stream.seek(0)
    response = client.post("/api/inspection/analyze", data={"image": (stream, "track.png")}, content_type="multipart/form-data")
    assert response.status_code == 200
    assert response.json["success"] is True
    assert response.json["detections"]


def test_history_api_returns_real_saved_inspection_and_filters(client):
    register(client)
    login(client)
    from PIL import Image
    image = Image.new("RGB", (200, 120), "white")
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    stream.seek(0)
    response = client.post("/api/inspection/analyze", data={"image": (stream, "track.png")}, content_type="multipart/form-data")
    inspection_id = response.json["inspection_id"]

    history = client.get("/api/history")
    assert history.status_code == 200
    saved = history.json["inspections"][0]
    assert saved["id"] == inspection_id
    assert saved["inspection_status"] == "COMPLETED"
    assert saved["image_filename"].endswith(".png")
    assert saved["detections"][0]["defect_name"] == "demo_surface_anomaly"
    assert 0 <= saved["detections"][0]["confidence"] <= 1

    filtered = client.get("/api/history?defect_name=demo_surface_anomaly")
    assert [item["id"] for item in filtered.json["inspections"]] == [inspection_id]
    assert client.get(f"/api/history/{inspection_id}").json["inspection"]["id"] == inspection_id
    assert client.get("/api/history/99999").status_code == 404


def test_failed_inference_does_not_save_inspection(client, monkeypatch):
    register(client)
    login(client)
    from PIL import Image
    from app import db
    from app.models import Inspection
    from app.services.detection_service import DetectionService

    def fail_detection(self, image_path, annotated_path):
        raise RuntimeError("inference failed")

    monkeypatch.setattr(DetectionService, "detect", fail_detection)
    image = Image.new("RGB", (200, 120), "white")
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    stream.seek(0)
    response = client.post("/api/inspection/analyze", data={"image": (stream, "track.png")}, content_type="multipart/form-data")
    assert response.status_code == 503
    with client.application.app_context():
        assert db.session.query(Inspection).count() == 0


def test_successful_inspection_with_no_detections_is_saved(client, monkeypatch):
    register(client)
    login(client)
    from PIL import Image
    from app.services.detection_service import DetectionService

    def no_detections(self, image_path, annotated_path):
        return []

    monkeypatch.setattr(DetectionService, "detect", no_detections)
    image = Image.new("RGB", (200, 120), "white")
    stream = io.BytesIO()
    image.save(stream, format="PNG")
    stream.seek(0)
    response = client.post("/api/inspection/analyze", data={"image": (stream, "track.png")}, content_type="multipart/form-data")
    assert response.status_code == 200
    assert response.json["detections"] == []
    saved = client.get(f"/api/history/{response.json['inspection_id']}").json["inspection"]
    assert saved["inspection_status"] == "COMPLETED"
    assert saved["detections"] == []


def test_language_preference_renders_translated_navigation(client):
    with client.session_transaction() as session:
        session["language"] = "hi"
    response = client.get("/register")
    assert response.status_code == 200
    assert "भाषा".encode("utf-8") in response.data
    assert b"sign in" in response.data.lower()
    assert b"no account?" not in response.data.lower()


def test_profile_page_and_header_toggles(client):
    register(client)
    login(client)
    response = client.get("/profile")
    assert response.status_code == 200
    assert b"profile-toggle" in response.data
    assert b"theme-toggle" in response.data
    assert b"person" in response.data.lower()


def test_profile_settings_form_and_header_order(client):
    register(client)
    login(client)
    response = client.get("/profile")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert html.index("theme-toggle") < html.index("profile-toggle")
    assert 'name="name"' in html
    assert 'name="email"' in html
    assert 'type="submit"' in html
    assert '/logout' in html


def test_guest_navbar_has_sign_in_prompt_without_menu(client):
    response = client.get("/register")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert 'menu-button' not in html
    assert 'Create account' in html or 'create_account' in html
    assert 'No account?' not in html
    assert 'sign in' in html.lower()
    assert '/login' in html
