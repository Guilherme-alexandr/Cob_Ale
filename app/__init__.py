from flask import Flask
from .config import Config
from .database import db, ma
from .routes import cliente_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    ma.init_app(app)

    app.register_blueprint(cliente_bp, url_prefix="/clientes")

    with app.app_context():
        db.create_all()

    return app
