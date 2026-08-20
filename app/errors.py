from flask import jsonify


class ApiError(Exception):
    """Erreur métier volontaire, convertie en réponse JSON cohérente."""

    def __init__(self, message, status_code=400, payload=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload or {}

    def to_dict(self):
        body = dict(self.payload)
        body["error"] = self.message
        body["status_code"] = self.status_code
        return body


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        response = jsonify(err.to_dict())
        response.status_code = err.status_code
        return response

    @app.errorhandler(404)
    def handle_404(err):
        return jsonify({"error": "Ressource introuvable", "status_code": 404}), 404

    @app.errorhandler(405)
    def handle_405(err):
        return jsonify({"error": "Méthode non autorisée", "status_code": 405}), 405

    @app.errorhandler(422)
    def handle_422(err):
        messages = getattr(err, "data", {}).get("messages", str(err))
        return jsonify({"error": "Données invalides", "status_code": 422, "details": messages}), 422

    @app.errorhandler(429)
    def handle_429(err):
        return jsonify({
            "error": "Trop de tentatives, réessayez plus tard",
            "status_code": 429,
        }), 429

    @app.errorhandler(500)
    def handle_500(err):
        return jsonify({"error": "Erreur interne du serveur", "status_code": 500}), 500
