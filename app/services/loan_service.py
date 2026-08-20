from datetime import datetime, timedelta
from app.extensions import db
from app.models import Loan
from app.errors import ApiError
from app.services.book_service import get_book_or_404

MAX_ACTIVE_LOANS = 3
LOAN_DURATION_DAYS = 14


def borrow_book(user, book_id):
    book = get_book_or_404(book_id)

    if not book.available:
        raise ApiError("Ce livre n'est pas disponible", 409)

    active_loans = Loan.query.filter_by(user_id=user.id, returned_at=None).count()
    if active_loans >= MAX_ACTIVE_LOANS:
        raise ApiError(
            f"Vous avez déjà {MAX_ACTIVE_LOANS} emprunts actifs, retournez un livre avant d'en emprunter un autre",
            409,
        )

    loan = Loan(
        book_id=book.id,
        user_id=user.id,
        due_date=datetime.utcnow() + timedelta(days=LOAN_DURATION_DAYS),
    )
    book.available = False
    db.session.add(loan)
    db.session.commit()
    return loan


def return_book(user, loan_id):
    loan = Loan.query.get(loan_id)
    if loan is None:
        raise ApiError("Emprunt introuvable", 404)

    if loan.user_id != user.id and not user.is_staff:
        raise ApiError("Vous n'êtes pas autorisé à retourner cet emprunt", 403)

    if loan.returned_at is not None:
        raise ApiError("Ce livre a déjà été retourné", 409)

    loan.returned_at = datetime.utcnow()
    loan.book.available = True
    db.session.commit()
    return loan


def list_my_loans(user, page, per_page):
    return Loan.query.filter_by(user_id=user.id).paginate(
        page=page, per_page=per_page, error_out=False
    )


def list_all_loans(page, per_page):
    return Loan.query.paginate(page=page, per_page=per_page, error_out=False)
