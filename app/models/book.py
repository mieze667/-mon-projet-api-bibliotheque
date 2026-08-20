from app.extensions import db


class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    year = db.Column(db.Integer)
    genre = db.Column(db.String(80))
    available = db.Column(db.Boolean, default=True, nullable=False)

    author_id = db.Column(db.Integer, db.ForeignKey("authors.id"), nullable=False)

    # lazy="select" : on ne charge les emprunts d'un livre que si explicitement demandé
    loans = db.relationship("Loan", backref="book", lazy="select")
