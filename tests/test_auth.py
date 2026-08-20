def test_register_success(client):
    res = client.post("/api/v1/auth/register", json={
        "email": "a@test.com", "username": "alice", "password": "password123",
    })
    assert res.status_code == 201
    body = res.get_json()
    assert "access_token" in body
    assert body["user"]["role"] == "member"


def test_register_duplicate_email(client):
    payload = {"email": "a@test.com", "username": "alice", "password": "password123"}
    client.post("/api/v1/auth/register", json=payload)
    res = client.post("/api/v1/auth/register", json={**payload, "username": "alice2"})
    assert res.status_code == 409


def test_register_invalid_payload(client):
    res = client.post("/api/v1/auth/register", json={"email": "not-an-email"})
    assert res.status_code == 422


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "email": "a@test.com", "username": "alice", "password": "password123",
    })
    res = client.post("/api/v1/auth/login", json={"email": "a@test.com", "password": "wrong"})
    assert res.status_code == 401


def test_me_requires_token(client):
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 401


def test_me_with_token(client, member_token, auth_header):
    res = client.get("/api/v1/auth/me", headers=auth_header(member_token))
    assert res.status_code == 200
    assert res.get_json()["email"] == "member@test.com"


def test_login_rate_limited_after_five_attempts(client):
    client.post("/api/v1/auth/register", json={
        "email": "brute@test.com", "username": "brute", "password": "password123",
    })
    for _ in range(5):
        res = client.post("/api/v1/auth/login", json={
            "email": "brute@test.com", "password": "wrong",
        })
        assert res.status_code == 401

    blocked = client.post("/api/v1/auth/login", json={
        "email": "brute@test.com", "password": "wrong",
    })
    assert blocked.status_code == 429
    assert blocked.get_json()["status_code"] == 429
