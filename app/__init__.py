from flask import Flask, send_from_directory
from flask_cors import CORS
import os
from flask_jwt_extended import JWTManager
from .config import Config
from .database import db, ma
from flask_migrate import Migrate

from swagger.swagger_config import configure_swagger

from app.routes.cliente_route import cliente_bp
from app.routes.contrato_route import contrato_bp
from app.routes.acordo_route import acordo_bp
from app.routes.importadores_route import import_bp
from app.routes.usuario_route import usuario_bp

migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

    app.config.from_object(Config)
    configure_swagger(app)

    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)

    jwt.init_app(app)

    app.register_blueprint(cliente_bp, url_prefix="/clientes")
    app.register_blueprint(contrato_bp, url_prefix="/contratos")
    app.register_blueprint(acordo_bp, url_prefix="/acordos")
    app.register_blueprint(import_bp)
    app.register_blueprint(usuario_bp, url_prefix="/usuarios")

    importadores_path = os.path.join(os.path.dirname(__file__), "..", "importadores")

    @app.route("/importadores/<path:filename>")
    def custom_static(filename):
        return send_from_directory(importadores_path, filename)

    with app.app_context():
        db.create_all()

    return app
