from app.database import db
from datetime import datetime

class Acordo(db.Model):
    __tablename__ = "acordos"

    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.String(6), db.ForeignKey("contrato.numero_contrato"), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    vencimento = db.Column(db.DateTime, nullable=False)
    tipo_pagamento = db.Column(db.String(20), nullable=False)  # ex: "à vista", "parcelado"
    qtd_parcelas = db.Column(db.Integer, nullable=False, default=1)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default="em andamento")  # em andamento, quebrado, finalizado

    # se seu banco suportar JSON, troque para db.JSON
    parcelamento_json = db.Column(db.Text, nullable=True)

    # relacionamento
    contrato = db.relationship("Contrato", backref=db.backref("acordos", lazy=True))

    def to_dict(self, include_boletos=False):
        data = {
            "id": self.id,
            "contrato_id": self.contrato_id,
            "tipo_pagamento": self.tipo_pagamento,
            "qtd_parcelas": self.qtd_parcelas,
            "valor_total": float(self.valor_total),
            "vencimento": self.vencimento.strftime("%Y-%m-%d"),
            "status": self.status,
            "data_criacao": self.data_criacao.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if include_boletos:
            data["boletos"] = [boleto.to_dict() for boleto in self.boletos]
        return data

    def __repr__(self):
        return f"<Acordo {self.id} - Contrato {self.contrato_id} - Status {self.status}>"

class Boleto(db.Model):
    __tablename__ = "boletos"

    id = db.Column(db.Integer, primary_key=True)
    acordo_id = db.Column(db.Integer, db.ForeignKey("acordos.id"), nullable=False)
    pdf_arquivo = db.Column(db.LargeBinary, nullable=True)  # <- aqui salva o PDF
    nome_arquivo = db.Column(db.String(255), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    enviado = db.Column(db.Boolean, default=False)

    # relacionamento
    acordo = db.relationship("Acordo", backref=db.backref("boletos", lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "acordo_id": self.acordo_id,
            "nome_arquivo": self.nome_arquivo,
            "criado_em": self.criado_em.strftime("%Y-%m-%d %H:%M:%S"),
            "enviado": self.enviado
        }

    def __repr__(self):
        return f"<Boleto {self.id} - Acordo {self.acordo_id} - Enviado {self.enviado}>"
