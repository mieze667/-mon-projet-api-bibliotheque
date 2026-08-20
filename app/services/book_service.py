from app.extensions import db
from app.models import Book
from app.errors import ApiError


def list_books(page, per_page, q=None, genre=None, available=None):
    query = Book.query
    if q:
        query = query.filter(Book.title.ilike(f"%{q}%"))
    if genre:
        query = query.filter(Book.genre == genre)
    if available is not None:
        query = query.filter(Book.available == available)
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_book_or_404(book_id):
    book = Book.query.get(book_id)
    if book is None:
        raise ApiError("Livre introuvable", 404)
    return book


def create_book(data):
    book = Book(**data)
    db.session.add(book)
    db.session.commit()
    return book


def update_book(book_id, data):
    book = get_book_or_404(book_id)
    for key, value in data.items():
        setattr(book, key, value)
    db.session.commit()
    return book


def delete_book(book_id):
    book = get_book_or_404(book_id)
    db.session.delete(book)
    db.session.commit()
