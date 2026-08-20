from app.extensions import db


class Author(db.Model):
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    nationality = db.Column(db.String(80))
    bio = db.Column(db.Text)

    # eager (joined) car un livre affiche presque toujours son auteur -> évite le N+1
    books = db.relationship("Book", backref="author", lazy="joined")
