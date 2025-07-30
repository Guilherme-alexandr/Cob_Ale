from app.database import db
from datetime import datetime

class Contrato(db.Model):
    __tablename__ = "contrato"

    numero_contrato = db.Column(db.String(6), primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey("cliente.id"), nullable=False)
    vencimento = db.Column(db.DateTime, default=datetime.utcnow)
    valor_total = db.Column(db.Float, nullable=False)
    filial = db.Column(db.String(100), nullable=False)

    cliente = db.relationship("Cliente", backref=db.backref("contratos", lazy=True))
