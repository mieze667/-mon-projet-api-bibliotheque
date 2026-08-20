def test_create_author_requires_staff(client, member_token, auth_header):
    res = client.post(
        "/api/v1/authors",
        json={"name": "Victor Hugo"},
        headers=auth_header(member_token),
    )
    assert res.status_code == 403


def test_create_and_get_author(client, staff_token, auth_header):
    res = client.post(
        "/api/v1/authors",
        json={"name": "Victor Hugo", "nationality": "française"},
        headers=auth_header(staff_token),
    )
    assert res.status_code == 201
    author_id = res.get_json()["id"]

    res2 = client.get(f"/api/v1/authors/{author_id}")
    assert res2.status_code == 200
    assert res2.get_json()["name"] == "Victor Hugo"


def test_get_unknown_author_404(client):
    res = client.get("/api/v1/authors/999")
    assert res.status_code == 404


def test_list_authors_pagination(client, staff_token, auth_header):
    for i in range(3):
        client.post(
            "/api/v1/authors",
            json={"name": f"Auteur {i}"},
            headers=auth_header(staff_token),
        )

    res = client.get("/api/v1/authors?page=1&per_page=2")
    body = res.get_json()
    assert res.status_code == 200
    assert len(body["data"]) == 2
    assert body["pagination"]["total_items"] == 3


def test_author_books_listing(client, staff_token, auth_header):
    author_res = client.post(
        "/api/v1/authors",
        json={"name": "Victor Hugo"},
        headers=auth_header(staff_token),
    )
    author_id = author_res.get_json()["id"]

    client.post(
        "/api/v1/books",
        json={"title": "Les Misérables", "isbn": "1234567890", "author_id": author_id},
        headers=auth_header(staff_token),
    )

    res = client.get(f"/api/v1/authors/{author_id}/books")
    assert res.status_code == 200
    titles = [book["title"] for book in res.get_json()]
    assert "Les Misérables" in titles


def test_update_author_requires_staff(client, staff_token, member_token, auth_header):
    author_res = client.post(
        "/api/v1/authors",
        json={"name": "Victor Hugo"},
        headers=auth_header(staff_token),
    )
    author_id = author_res.get_json()["id"]

    denied = client.put(
        f"/api/v1/authors/{author_id}",
        json={"name": "Victor H."},
        headers=auth_header(member_token),
    )
    assert denied.status_code == 403

    allowed = client.put(
        f"/api/v1/authors/{author_id}",
        json={"name": "Victor H."},
        headers=auth_header(staff_token),
    )
    assert allowed.status_code == 200
    assert allowed.get_json()["name"] == "Victor H."


def test_delete_author_requires_staff(client, staff_token, member_token, auth_header):
    author_res = client.post(
        "/api/v1/authors",
        json={"name": "À supprimer"},
        headers=auth_header(staff_token),
    )
    author_id = author_res.get_json()["id"]

    denied = client.delete(f"/api/v1/authors/{author_id}", headers=auth_header(member_token))
    assert denied.status_code == 403

    allowed = client.delete(f"/api/v1/authors/{author_id}", headers=auth_header(staff_token))
    assert allowed.status_code == 204
