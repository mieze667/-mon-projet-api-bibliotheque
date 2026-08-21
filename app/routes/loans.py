from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError

from app.schemas import LoanSchema, LoanCreateSchema
from app.services import loan_service
from app.models import User
from app.routes.helpers import paginate_args, paginated_response, role_required

bp = Blueprint("loans", __name__, url_prefix="/api/v1/loans")
schema = LoanSchema()
create_schema = LoanCreateSchema()


@bp.post("")
@jwt_required()
def borrow():
    """Emprunter un livre. 409 si indisponible ou si limite d'emprunts atteinte.
    ---
    tags: [Loans]
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [book_id]
          properties:
            book_id:
              type: integer
              example: 1
    responses:
      201:
        description: Emprunt créé
      409:
        description: Livre indisponible ou quota de 3 emprunts atteint
      422:
        description: Données invalides
    """
    try:
        data = create_schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Données invalides", "status_code": 422, "details": err.messages}), 422

    user = User.query.get_or_404(get_jwt_identity())
    loan = loan_service.borrow_book(user, data["book_id"])
    return jsonify(schema.dump(loan)), 201


@bp.patch("/<int:loan_id>/return")
@jwt_required()
def return_loan(loan_id):
    """Retourner un livre emprunté.
    ---
    tags: [Loans]
    parameters:
      - name: loan_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Retour enregistré
      404:
        description: Emprunt introuvable
      409:
        description: Livre déjà retourné
    """
    user = User.query.get_or_404(get_jwt_identity())
    loan = loan_service.return_book(user, loan_id)
    return jsonify(schema.dump(loan))


@bp.get("/mine")
@jwt_required()
def my_loans():
    """Mes emprunts (l'utilisateur ne voit que les siens).
    ---
    tags: [Loans]
    """
    user = User.query.get_or_404(get_jwt_identity())
    page, per_page = paginate_args()
    pagination = loan_service.list_my_loans(user, page, per_page)
    return jsonify(paginated_response(pagination, schema))


@bp.get("")
@role_required("staff")
def all_loans():
    """Tous les emprunts (staff uniquement).
    ---
    tags: [Loans]
    """
    page, per_page = paginate_args()
    pagination = loan_service.list_all_loans(page, per_page)
    return jsonify(paginated_response(pagination, schema))
