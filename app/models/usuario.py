from ..database import db
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.Text, nullable=False)
    cargo = db.Column(db.String(20), nullable=False) # operador, supervisor, gerente

    def set_senha(self, senha):
        self.senha = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha, senha)

    def to_dict(self):
        return {
            "id": self.id,
            "nome": self.nome,
            "login": self.login,
            "cargo": self.cargo
        }