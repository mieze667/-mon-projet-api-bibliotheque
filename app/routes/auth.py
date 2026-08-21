from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt,
)
from marshmallow import ValidationError

from app.schemas import UserRegisterSchema, UserLoginSchema, UserPublicSchema
from app.services.auth_service import register_user, authenticate
from app.models import User
from app.extensions import limiter

bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

register_schema = UserRegisterSchema()
login_schema = UserLoginSchema()
public_schema = UserPublicSchema()


def _tokens_for(user):
    extra_claims = {"role": user.role}
    access = create_access_token(identity=str(user.id), additional_claims=extra_claims)
    refresh = create_refresh_token(identity=str(user.id), additional_claims=extra_claims)
    return access, refresh


@bp.post("/register")
def register():
    """Inscription d'un nouvel utilisateur.
    ---
    tags: [Auth]
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [email, username, password]
          properties:
            email:
              type: string
              example: staff@lib.com
            username:
              type: string
              example: staff1
            password:
              type: string
              example: secret123
            role:
              type: string
              enum: [member, staff]
              example: staff
    responses:
      201:
        description: Utilisateur créé, jetons renvoyés
    """
    try:
        data = register_schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Données invalides", "status_code": 422, "details": err.messages}), 422

    user = register_user(data)
    access, refresh = _tokens_for(user)
    return jsonify({
        "user": public_schema.dump(user),
        "access_token": access,
        "refresh_token": refresh,
    }), 201


@bp.post("/login")
@limiter.limit("5 per minute")
def login():
    """Connexion, renvoie un access token et un refresh token.
    Limitée à 5 tentatives par minute et par IP pour freiner le brute-force.
    ---
    tags: [Auth]
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [email, password]
          properties:
            email:
              type: string
              example: staff@lib.com
            password:
              type: string
              example: secret123
    responses:
      200:
        description: Connexion réussie
      401:
        description: Identifiants invalides
      429:
        description: Trop de tentatives (limite 5/minute)
    """
    try:
        data = login_schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Données invalides", "status_code": 422, "details": err.messages}), 422

    user = authenticate(data["email"], data["password"])
    access, refresh = _tokens_for(user)
    return jsonify({"access_token": access, "refresh_token": refresh})


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """Génère un nouveau access token à partir du refresh token.
    ---
    tags: [Auth]
    """
    identity = get_jwt_identity()
    claims = get_jwt()
    access = create_access_token(identity=identity, additional_claims={"role": claims.get("role")})
    return jsonify({"access_token": access})


@bp.get("/me")
@jwt_required()
def me():
    """Profil de l'utilisateur connecté.
    ---
    tags: [Auth]
    """
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify(public_schema.dump(user))
