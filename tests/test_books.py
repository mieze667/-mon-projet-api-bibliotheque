def create_author(client, staff_token, auth_header):
    res = client.post("/api/v1/authors", json={"name": "Victor Hugo"}, headers=auth_header(staff_token))
    return res.get_json()["id"]


def test_create_book_requires_staff(client, member_token, auth_header):
    res = client.post("/api/v1/books", json={
        "title": "Les Misérables", "isbn": "1234567890", "author_id": 1,
    }, headers=auth_header(member_token))
    assert res.status_code == 403


def test_create_and_get_book(client, staff_token, auth_header):
    author_id = create_author(client, staff_token, auth_header)
    res = client.post("/api/v1/books", json={
        "title": "Les Misérables", "isbn": "1234567890", "author_id": author_id,
    }, headers=auth_header(staff_token))
    assert res.status_code == 201
    book_id = res.get_json()["id"]
    assert res.get_json()["available"] is True

    res2 = client.get(f"/api/v1/books/{book_id}")
    assert res2.status_code == 200
    assert res2.get_json()["title"] == "Les Misérables"


def test_get_unknown_book_404(client):
    res = client.get("/api/v1/books/999")
    assert res.status_code == 404


def test_list_books_pagination(client, staff_token, auth_header):
    author_id = create_author(client, staff_token, auth_header)
    for i in range(3):
        client.post("/api/v1/books", json={
            "title": f"Livre {i}", "isbn": f"111111111{i}", "author_id": author_id,
        }, headers=auth_header(staff_token))

    res = client.get("/api/v1/books?page=1&per_page=2")
    body = res.get_json()
    assert res.status_code == 200
    assert len(body["data"]) == 2
    assert body["pagination"]["total_items"] == 3


def test_delete_book_with_loan_history_is_conflict(client, staff_token, member_token, auth_header):
    author_id = create_author(client, staff_token, auth_header)
    book_res = client.post("/api/v1/books", json={
        "title": "Les Misérables", "isbn": "9999999999", "author_id": author_id,
    }, headers=auth_header(staff_token))
    book_id = book_res.get_json()["id"]

    client.post("/api/v1/loans", json={"book_id": book_id}, headers=auth_header(member_token))

    res = client.delete(f"/api/v1/books/{book_id}", headers=auth_header(staff_token))
    assert res.status_code == 409


def test_delete_book_without_loans_succeeds(client, staff_token, auth_header):
    author_id = create_author(client, staff_token, auth_header)
    book_res = client.post("/api/v1/books", json={
        "title": "Livre neuf", "isbn": "8888888888", "author_id": author_id,
    }, headers=auth_header(staff_token))
    book_id = book_res.get_json()["id"]

    res = client.delete(f"/api/v1/books/{book_id}", headers=auth_header(staff_token))
    assert res.status_code == 204
