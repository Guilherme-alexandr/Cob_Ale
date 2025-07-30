from flask import Flask
from .config import Config
from .database import db, ma
from app.routes.cliente_route import cliente_bp
from app.routes.contrato_route import contrato_bp
from app.routes.acordo_route import acordo_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    ma.init_app(app)

    app.register_blueprint(cliente_bp, url_prefix="/clientes")
    app.register_blueprint(contrato_bp, url_prefix="/contratos")
    app.register_blueprint(acordo_bp, url_prefix="/acordos")

    with app.app_context():
        db.create_all()

    return app
