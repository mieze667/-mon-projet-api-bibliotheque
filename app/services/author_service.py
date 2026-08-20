from app.extensions import db
from app.models import Author
from app.errors import ApiError


def list_authors(page, per_page):
    return Author.query.paginate(page=page, per_page=per_page, error_out=False)


def get_author_or_404(author_id):
    author = Author.query.get(author_id)
    if author is None:
        raise ApiError("Auteur introuvable", 404)
    return author


def create_author(data):
    author = Author(**data)
    db.session.add(author)
    db.session.commit()
    return author


def update_author(author_id, data):
    author = get_author_or_404(author_id)
    for key, value in data.items():
        setattr(author, key, value)
    db.session.commit()
    return author


def delete_author(author_id):
    author = get_author_or_404(author_id)
    db.session.delete(author)
    db.session.commit()
