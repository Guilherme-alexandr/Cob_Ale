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

    parcelamento_json = db.Column(db.Text, nullable=True)

    contrato = db.relationship("Contrato", backref=db.backref("acordo", uselist=False))

    def to_dict(self):
        return {
            "id": self.id,
            "contrato_id": self.contrato_id,
            "tipo_pagamento": self.tipo_pagamento,
            "qtd_parcelas": self.qtd_parcelas,
            "valor_total": self.valor_total,
            "vencimento": self.vencimento.strftime("%Y-%m-%d"),
            "status": self.status
        }

class Boleto(db.Model):
    __tablename__ = "boletos"

    id = db.Column(db.Integer, primary_key= True)
    acordo_id = db.Column(db.Integer, db.ForeignKey("acordo.id"), nullable=False)
    caminho_pdf = db.Column(db.String, nullable= False)
    criado_em = db.Column(db.DateTime, default= datetime.utcnow)
    enviado = db.Column(db.Boolean, default= False)

    acordo = db.relationship("Acordo", backref= db.backref("boletos", lazy=True))