"""
Authentication + authorization tests.

Uses the `client` fixture (pre-authenticated as REVIEWER — see conftest.py)
only where reviewer access is the point; otherwise uses `anon_client`
(no token) or `citizen_client` (CITIZEN token) to exercise the actual
access-control boundaries.
"""
import jwt

from app.core.security import create_access_token
from tests.factories import make_analyzed_report

SIGNUP_URL = "/api/auth/signup"
LOGIN_URL = "/api/auth/login"
ME_URL = "/api/auth/me"


# --------------------------------------------------------------------------
# Signup
# --------------------------------------------------------------------------

def test_signup_success(anon_client):
    resp = anon_client.post(SIGNUP_URL, json={"email": "new@example.com", "password": "Passw0rd!", "display_name": "New User"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["email"] == "new@example.com"
    assert body["user"]["role"] == "CITIZEN"
    assert "access_token" in body
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]


def test_signup_duplicate_email_rejected(anon_client):
    anon_client.post(SIGNUP_URL, json={"email": "dupe@example.com", "password": "Passw0rd!"})
    resp = anon_client.post(SIGNUP_URL, json={"email": "dupe@example.com", "password": "Different1!"})
    assert resp.status_code == 409


def test_signup_invalid_email_rejected(anon_client):
    resp = anon_client.post(SIGNUP_URL, json={"email": "not-an-email", "password": "Passw0rd!"})
    assert resp.status_code == 422


def test_signup_short_password_rejected(anon_client):
    resp = anon_client.post(SIGNUP_URL, json={"email": "shortpw@example.com", "password": "short"})
    assert resp.status_code == 422


def test_signup_cannot_choose_reviewer_role(anon_client):
    """The SignupRequest schema has no `role` field — an extra one is simply ignored, never honored."""
    resp = anon_client.post(
        SIGNUP_URL,
        json={"email": "wannabe-reviewer@example.com", "password": "Passw0rd!", "role": "REVIEWER"},
    )
    assert resp.status_code == 201
    assert resp.json()["user"]["role"] == "CITIZEN"


# --------------------------------------------------------------------------
# Login
# --------------------------------------------------------------------------

def test_login_success(anon_client):
    anon_client.post(SIGNUP_URL, json={"email": "login@example.com", "password": "Passw0rd!"})
    resp = anon_client.post(LOGIN_URL, json={"email": "login@example.com", "password": "Passw0rd!"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(anon_client):
    anon_client.post(SIGNUP_URL, json={"email": "wrongpw@example.com", "password": "Passw0rd!"})
    resp = anon_client.post(LOGIN_URL, json={"email": "wrongpw@example.com", "password": "WrongPassword1!"})
    assert resp.status_code == 401


def test_login_nonexistent_account(anon_client):
    resp = anon_client.post(LOGIN_URL, json={"email": "ghost@example.com", "password": "Passw0rd!"})
    assert resp.status_code == 401


# --------------------------------------------------------------------------
# /auth/me + token validation
# --------------------------------------------------------------------------

def test_me_returns_current_user(client, reviewer_user):
    resp = client.get(ME_URL)
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(reviewer_user.id)
    assert body["role"] == "REVIEWER"
    assert "password" not in body
    assert "password_hash" not in body


def test_me_without_token_is_401(anon_client):
    resp = anon_client.get(ME_URL)
    assert resp.status_code == 401


def test_me_with_garbage_token_is_401(anon_client):
    resp = anon_client.get(ME_URL, headers={"Authorization": "Bearer not-a-real-token"})
    assert resp.status_code == 401


def test_me_with_expired_token_is_401(anon_client, reviewer_user):
    import datetime as dt

    from app.config import get_settings

    settings = get_settings()
    now = dt.datetime.now(dt.timezone.utc)
    expired_payload = {
        "sub": str(reviewer_user.id),
        "role": reviewer_user.role.value,
        "type": "access",
        "iat": now - dt.timedelta(hours=2),
        "exp": now - dt.timedelta(hours=1),
    }
    expired_token = jwt.encode(expired_payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    resp = anon_client.get(ME_URL, headers={"Authorization": f"Bearer {expired_token}"})
    assert resp.status_code == 401


# --------------------------------------------------------------------------
# Authorization: role enforcement on protected endpoints
# --------------------------------------------------------------------------

def test_unauthenticated_cannot_access_dashboard(anon_client):
    assert anon_client.get("/api/dashboard/summary").status_code == 401


def test_unauthenticated_cannot_access_cases(anon_client):
    assert anon_client.get("/api/cases").status_code == 401


def test_unauthenticated_cannot_create_report(anon_client, sample_image_bytes):
    resp = anon_client.post(
        "/api/reports",
        data={"latitude": "23.0", "longitude": "72.5"},
        files={"image": ("stream.png", sample_image_bytes, "image/png")},
    )
    assert resp.status_code == 401


def test_citizen_cannot_access_dashboard(citizen_client):
    assert citizen_client.get("/api/dashboard/summary").status_code == 403


def test_citizen_cannot_access_cases(citizen_client):
    assert citizen_client.get("/api/cases").status_code == 403


def test_citizen_cannot_verify_report(citizen_client, db_session):
    report = make_analyzed_report(db_session)
    resp = citizen_client.post(f"/api/reports/{report.id}/verify", json={"status": "VERIFIED"})
    assert resp.status_code == 403


def test_citizen_can_submit_report(citizen_client, sample_image_bytes):
    resp = citizen_client.post(
        "/api/reports",
        data={"latitude": "23.0", "longitude": "72.5"},
        files={"image": ("stream.png", sample_image_bytes, "image/png")},
    )
    assert resp.status_code == 201


def test_citizen_can_view_own_report(citizen_client, sample_image_bytes):
    create_resp = citizen_client.post(
        "/api/reports",
        data={"latitude": "23.0", "longitude": "72.5"},
        files={"image": ("stream.png", sample_image_bytes, "image/png")},
    )
    report_id = create_resp.json()["id"]
    resp = citizen_client.get(f"/api/reports/{report_id}")
    assert resp.status_code == 200


def test_citizen_cannot_view_others_report(citizen_client, db_session):
    report = make_analyzed_report(db_session)  # created with no user_id (factory bypasses the API)
    resp = citizen_client.get(f"/api/reports/{report.id}")
    assert resp.status_code == 403


def test_citizen_cannot_list_all_reports(citizen_client):
    assert citizen_client.get("/api/reports").status_code == 403


def test_citizen_own_reports_endpoint(citizen_client, sample_image_bytes):
    citizen_client.post(
        "/api/reports",
        data={"latitude": "23.0", "longitude": "72.5"},
        files={"image": ("stream.png", sample_image_bytes, "image/png")},
    )
    resp = citizen_client.get("/api/reports/me")
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


# --------------------------------------------------------------------------
# Security hygiene
# --------------------------------------------------------------------------

def test_password_hash_never_returned_on_signup(anon_client):
    resp = anon_client.post(SIGNUP_URL, json={"email": "hashcheck@example.com", "password": "Passw0rd!"})
    assert "password_hash" not in resp.text
    assert "Passw0rd!" not in resp.text


def test_password_hash_never_returned_on_me(client):
    resp = client.get(ME_URL)
    assert "password_hash" not in resp.text
    assert "password" not in resp.json()


def test_jwt_secret_never_exposed(client, anon_client):
    from app.config import get_settings

    secret = get_settings().jwt_secret_key
    assert secret not in client.get("/health").text
    assert secret not in anon_client.get("/api/auth/me").text


def test_plaintext_password_not_persisted(anon_client, db_session):
    anon_client.post(SIGNUP_URL, json={"email": "plaintext@example.com", "password": "Passw0rd!"})
    from app.models.user import User

    user = db_session.query(User).filter(User.email == "plaintext@example.com").first()
    assert user.password_hash != "Passw0rd!"
    assert user.password_hash.startswith("$2b$")  # bcrypt hash prefix
