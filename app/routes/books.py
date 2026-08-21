from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from app.schemas import BookSchema
from app.services import book_service
from app.routes.helpers import paginate_args, paginated_response, role_required

bp = Blueprint("books", __name__, url_prefix="/api/v1/books")
schema = BookSchema()


@bp.get("")
def list_books():
    """Liste paginée des livres, avec recherche et filtres.
    ---
    tags: [Books]
    parameters:
      - name: q
        in: query
        type: string
      - name: genre
        in: query
        type: string
      - name: available
        in: query
        type: boolean
      - name: page
        in: query
        type: integer
      - name: per_page
        in: query
        type: integer
    """
    page, per_page = paginate_args()
    q = request.args.get("q")
    genre = request.args.get("genre")
    available = request.args.get("available")
    if available is not None:
        available = available.lower() in ("1", "true", "yes")
    pagination = book_service.list_books(page, per_page, q=q, genre=genre, available=available)
    return jsonify(paginated_response(pagination, schema))


@bp.get("/<int:book_id>")
def get_book(book_id):
    """Détail d'un livre.
    ---
    tags: [Books]
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Livre trouvé
      404:
        description: Livre introuvable
    """
    book = book_service.get_book_or_404(book_id)
    return jsonify(schema.dump(book))


@bp.post("")
@role_required("staff")
def create_book():
    """Créer un livre (staff uniquement).
    ---
    tags: [Books]
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required: [title, isbn, author_id]
          properties:
            title:
              type: string
              example: Les Misérables
            isbn:
              type: string
              example: "9780451419439"
            year:
              type: integer
              example: 1862
            genre:
              type: string
              example: Roman
            author_id:
              type: integer
              example: 1
    responses:
      201:
        description: Livre créé
      403:
        description: Réservé au staff
      422:
        description: Données invalides
    """
    try:
        data = schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Données invalides", "status_code": 422, "details": err.messages}), 422
    book = book_service.create_book(data)
    return jsonify(schema.dump(book)), 201


@bp.put("/<int:book_id>")
@role_required("staff")
def update_book(book_id):
    """Modifier un livre (staff uniquement).
    ---
    tags: [Books]
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            isbn:
              type: string
            year:
              type: integer
            genre:
              type: string
            available:
              type: boolean
    responses:
      200:
        description: Livre mis à jour
      403:
        description: Réservé au staff
      404:
        description: Livre introuvable
    """
    try:
        data = schema.load(request.get_json(force=True) or {}, partial=True)
    except ValidationError as err:
        return jsonify({"error": "Données invalides", "status_code": 422, "details": err.messages}), 422
    book = book_service.update_book(book_id, data)
    return jsonify(schema.dump(book))


@bp.delete("/<int:book_id>")
@role_required("staff")
def delete_book(book_id):
    """Supprimer un livre (staff uniquement, 403 sinon).
    ---
    tags: [Books]
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
    responses:
      204:
        description: Livre supprimé
      403:
        description: Réservé au staff
      404:
        description: Livre introuvable
      409:
        description: Le livre a un historique d'emprunts, suppression refusée
    """
    book_service.delete_book(book_id)
    return "", 204
