from app.extensions import db
from app.models import User
from app.errors import ApiError


def register_user(data):
    if User.query.filter_by(email=data["email"]).first():
        raise ApiError("Cet email est déjà utilisé", 409)
    if User.query.filter_by(username=data["username"]).first():
        raise ApiError("Ce nom d'utilisateur est déjà pris", 409)

    user = User(
        email=data["email"],
        username=data["username"],
        role=data.get("role", "member"),
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return user


def authenticate(email, password):
    user = User.query.filter_by(email=email).first()
    if user is None or not user.check_password(password):
        raise ApiError("Email ou mot de passe incorrect", 401)
    return user
