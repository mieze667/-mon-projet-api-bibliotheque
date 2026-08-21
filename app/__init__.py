import os
import logging
from flask import Flask, jsonify
from sqlalchemy import text

from app.config import config_by_name
from app.extensions import db, migrate, jwt, ma, cors, swagger, limiter
from app.errors import register_error_handlers


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": os.environ.get("CORS_ORIGINS", "*")}})
    limiter.init_app(app)

    if app.config.get("DEBUG"):
        swagger.template = {
            "security": [{"Bearer": []}],
        }
        swagger.init_app(app)

    logging.basicConfig(level=logging.INFO)

    @app.before_request
    def log_request():
        app.logger.info("%s %s", __import__("flask").request.method, __import__("flask").request.path)

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer-when-downgrade"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        if not app.config.get("DEBUG"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

    register_error_handlers(app)

    from app.routes.auth import bp as auth_bp
    from app.routes.books import bp as books_bp
    from app.routes.authors import bp as authors_bp
    from app.routes.loans import bp as loans_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)
    app.register_blueprint(authors_bp)
    app.register_blueprint(loans_bp)

    @app.get("/health")
    def health():
        try:
            db.session.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False
        status = 200 if db_ok else 503
        return jsonify({"status": "ok" if db_ok else "degraded", "database": db_ok}), status

    return app
