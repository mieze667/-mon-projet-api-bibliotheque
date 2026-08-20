import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(basedir, 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_MIN", 15))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 30))
    )
    DEBUG = False
    SWAGGER = {"title": "Bibliothèque API", "uiversion": 3, "specs_route": "/docs/"}
    RATELIMIT_STORAGE_URI = os.environ.get("RATELIMIT_STORAGE_URI", "memory://")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)


class ProductionConfig(BaseConfig):
    DEBUG = False


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
