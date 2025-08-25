from ..database import db

class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=False)
    numero = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=False)

    enderecos = db.relationship("Endereco",  backref="cliente", cascade="all, delete-orphan", lazy=True)

class Endereco(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rua = db.Column(db.String(150), nullable=False)
    numero = db.Column(db.String(20),  nullable=False)
    cidade  = db.Column(db.String(100), nullable=False)
    estado =  db.Column(db.String(2), nullable=False)
    cep =  db.Column(db.String(8), nullable=False)

    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"), nullable=False)