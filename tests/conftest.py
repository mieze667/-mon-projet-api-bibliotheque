import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


def register_and_login(client, email="member@test.com", role="member"):
    client.post("/api/v1/auth/register", json={
        "email": email, "username": email.split("@")[0], "password": "password123", "role": role,
    })
    res = client.post("/api/v1/auth/login", json={"email": email, "password": "password123"})
    return res.get_json()["access_token"]


@pytest.fixture
def staff_token(client):
    return register_and_login(client, email="staff@test.com", role="staff")


@pytest.fixture
def member_token(client):
    return register_and_login(client, email="member@test.com", role="member")


@pytest.fixture
def auth_header():
    def _header(token):
        return {"Authorization": f"Bearer {token}"}
    return _header
