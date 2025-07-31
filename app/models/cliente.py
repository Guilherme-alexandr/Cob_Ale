from ..database import db

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    numero = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)
