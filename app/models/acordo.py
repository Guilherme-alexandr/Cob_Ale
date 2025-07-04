from app.database import db
from datetime import datetime

class Acordo(db.Model):
    __tablename__ = "acordo"

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.String(6), db.ForeignKey("contrato.numero_contrato"), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    vencimento = db.Column(db.DateTime, nullable=False)
    tipo_pagamento = db.Column(db.String(20), nullable=False)
    qtd_parcelas = db.Column(db.Integer, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default="em andamento")

    contrato = db.relationship("Contrato", backref=db.backref("acordo", uselist=False))