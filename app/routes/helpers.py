from functools import wraps
from flask import request
from flask_jwt_extended import get_jwt, verify_jwt_in_request
from app.errors import ApiError


def paginate_args():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 10, type=int), 100)
    return page, per_page


def paginated_response(pagination, schema):
    return {
        "data": schema.dump(pagination.items, many=True),
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total_items": pagination.total,
            "total_pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                raise ApiError("Accès refusé : rôle insuffisant", 403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
