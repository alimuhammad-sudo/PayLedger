from app.auth.security import COOKIE_NAME, issue_token
from tests.conftest import PASSWORD


def test_login_sets_httponly_cookie_and_returns_user(client, admin):
    r = client.post(
        "/api/auth/login", json={"email": "admin@acme-hr.example", "password": PASSWORD}
    )

    assert r.status_code == 200
    assert r.json() == {"id": admin.id, "email": "admin@acme-hr.example", "full_name": "Ada Admin",
                        "role": "admin"}  # fmt: skip
    cookie = r.headers["set-cookie"]
    assert cookie.startswith(f"{COOKIE_NAME}=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie


def test_email_is_case_insensitive(client, admin):
    r = client.post(
        "/api/auth/login", json={"email": "ADMIN@acme-hr.example", "password": PASSWORD}
    )
    assert r.status_code == 200


def test_wrong_password_and_unknown_email_give_the_same_answer(client, admin):
    wrong = client.post("/api/auth/login", json={"email": admin.email, "password": "nope"})
    unknown = client.post(
        "/api/auth/login", json={"email": "who@acme-hr.example", "password": "nope"}
    )

    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"message": "Email or password is incorrect."}


def test_me_needs_a_session(client):
    r = client.get("/api/auth/me")
    assert r.status_code == 401
    assert r.json()["message"] == "Please sign in."


def test_me_returns_the_signed_in_user(as_viewer):
    assert as_viewer.get("/api/auth/me").json()["role"] == "viewer"


def test_logout_clears_the_session(as_admin):
    assert as_admin.post("/api/auth/logout").status_code == 204
    assert as_admin.get("/api/auth/me").status_code == 401


def test_tampered_cookie_is_rejected(client, admin):
    client.cookies.set(COOKIE_NAME, "not-a-token")
    assert client.get("/api/auth/me").status_code == 401


def test_expired_session_says_so(client, admin, settings):
    client.cookies.set(COOKIE_NAME, issue_token(admin.id, "admin", settings.secret_key, hours=-1))
    r = client.get("/api/auth/me")
    assert r.status_code == 401
    assert "expired" in r.json()["message"]


def test_token_signed_with_another_key_is_rejected(client, admin):
    client.cookies.set(COOKIE_NAME, issue_token(admin.id, "admin", "some-other-key" * 4, hours=1))
    assert client.get("/api/auth/me").status_code == 401


def test_health_is_public(client):
    assert client.get("/api/health").json() == {"status": "ok"}
