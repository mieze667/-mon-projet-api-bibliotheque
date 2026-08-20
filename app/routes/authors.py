from flask import Blueprint, request, jsonify
from marshmallow import ValidationError

from app.schemas import AuthorSchema
from app.services import author_service
from app.routes.helpers import paginate_args, paginated_response, role_required

bp = Blueprint("authors", __name__, url_prefix="/api/v1/authors")
schema = AuthorSchema()


@bp.get("")
def list_authors():
    page, per_page = paginate_args()
    pagination = author_service.list_authors(page, per_page)
    return jsonify(paginated_response(pagination, schema))


@bp.get("/<int:author_id>")
def get_author(author_id):
    author = author_service.get_author_or_404(author_id)
    return jsonify(schema.dump(author))


@bp.get("/<int:author_id>/books")
def get_author_books(author_id):
    from app.schemas import BookSchema
    author = author_service.get_author_or_404(author_id)
    return jsonify(BookSchema().dump(author.books, many=True))


@bp.post("")
@role_required("staff")
def create_author():
    try:
        data = schema.load(request.get_json(force=True) or {})
    except ValidationError as err:
        return jsonify({"error": "Données invalides", "status_code": 422, "details": err.messages}), 422
    author = author_service.create_author(data)
    return jsonify(schema.dump(author)), 201


@bp.put("/<int:author_id>")
@role_required("staff")
def update_author(author_id):
    try:
        data = schema.load(request.get_json(force=True) or {}, partial=True)
    except ValidationError as err:
        return jsonify({"error": "Données invalides", "status_code": 422, "details": err.messages}), 422
    author = author_service.update_author(author_id, data)
    return jsonify(schema.dump(author))


@bp.delete("/<int:author_id>")
@role_required("staff")
def delete_author(author_id):
    author_service.delete_author(author_id)
    return "", 204
