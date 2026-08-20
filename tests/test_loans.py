def setup_book(client, staff_token, auth_header):
    author = client.post("/api/v1/authors", json={"name": "Victor Hugo"}, headers=auth_header(staff_token)).get_json()
    book = client.post("/api/v1/books", json={
        "title": "Les Misérables", "isbn": "1234567890", "author_id": author["id"],
    }, headers=auth_header(staff_token)).get_json()
    return book["id"]


def test_borrow_book_success(client, staff_token, member_token, auth_header):
    book_id = setup_book(client, staff_token, auth_header)
    res = client.post("/api/v1/loans", json={"book_id": book_id}, headers=auth_header(member_token))
    assert res.status_code == 201
    assert res.get_json()["book_id"] == book_id


def test_borrow_unavailable_book_returns_409(client, staff_token, member_token, auth_header):
    book_id = setup_book(client, staff_token, auth_header)
    client.post("/api/v1/loans", json={"book_id": book_id}, headers=auth_header(member_token))
    # deuxième emprunt du même livre, déjà indisponible
    res = client.post("/api/v1/loans", json={"book_id": book_id}, headers=auth_header(staff_token))
    assert res.status_code == 409


def test_max_active_loans_enforced(client, staff_token, member_token, auth_header):
    author = client.post("/api/v1/authors", json={"name": "Victor Hugo"}, headers=auth_header(staff_token)).get_json()
    book_ids = []
    for i in range(4):
        b = client.post("/api/v1/books", json={
            "title": f"Livre {i}", "isbn": f"999999999{i}", "author_id": author["id"],
        }, headers=auth_header(staff_token)).get_json()
        book_ids.append(b["id"])

    for book_id in book_ids[:3]:
        res = client.post("/api/v1/loans", json={"book_id": book_id}, headers=auth_header(member_token))
        assert res.status_code == 201

    res = client.post("/api/v1/loans", json={"book_id": book_ids[3]}, headers=auth_header(member_token))
    assert res.status_code == 409


def test_return_book(client, staff_token, member_token, auth_header):
    book_id = setup_book(client, staff_token, auth_header)
    loan = client.post("/api/v1/loans", json={"book_id": book_id}, headers=auth_header(member_token)).get_json()

    res = client.patch(f"/api/v1/loans/{loan['id']}/return", headers=auth_header(member_token))
    assert res.status_code == 200
    assert res.get_json()["returned_at"] is not None

    book = client.get(f"/api/v1/books/{book_id}").get_json()
    assert book["available"] is True


def test_user_sees_only_own_loans(client, staff_token, member_token, auth_header):
    book_id = setup_book(client, staff_token, auth_header)
    client.post("/api/v1/loans", json={"book_id": book_id}, headers=auth_header(member_token))

    res = client.get("/api/v1/loans/mine", headers=auth_header(member_token))
    assert res.status_code == 200
    assert res.get_json()["pagination"]["total_items"] == 1

    res_staff = client.get("/api/v1/loans/mine", headers=auth_header(staff_token))
    assert res_staff.get_json()["pagination"]["total_items"] == 0
