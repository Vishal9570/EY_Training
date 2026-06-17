from flask import Flask
from app.routes import prediction_bp
from app.errors import register_error_handlers
from app.logging_config import configure_logging


def create_app():
    app = Flask(__name__)

    configure_logging()

    app.register_blueprint(prediction_bp)

    register_error_handlers(app)

    return app