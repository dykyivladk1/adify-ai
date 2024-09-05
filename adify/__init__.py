import logging

from flask import Flask

from .config import settings


def create_app() -> Flask:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings.validate()

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=settings.secret_key,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    from .routes import bp

    app.register_blueprint(bp)
    return app
