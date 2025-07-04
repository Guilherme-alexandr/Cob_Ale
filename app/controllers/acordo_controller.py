from app.database import db
from app.models.acordo import Acordo
from app.models.contrato import Contrato
from datetime import datetime

def criar(data):

    contrato = Contrato.query.filter_by(numero_contrato=data["contrato_id"]).first()
    if not contrato:
        raise ValueError("Contrato não encontrado.")

    if data["tipo_pagamento"] not in ["avista", "parcelado"]:
        raise ValueError("Tipo de pagamento deve ser 'avista' ou 'parcelado'.")

    if not (1 <= int(data["qtd_parcelas"]) <= 24):
        raise ValueError("Quantidade de parcelas deve estar entre 1 e 24.")

    try:
        vencimento = datetime.strptime(data["vencimento"], "%Y-%m-%d")
    except ValueError:
        raise ValueError("Formato de data inválido para vencimento. Use 'YYYY-MM-DD'.")

    acordo = Acordo(
        contrato_id=data["contrato_id"],
        tipo_pagamento=data["tipo_pagamento"],
        qtd_parcelas=data["qtd_parcelas"],
        valor_total=data["valor_total"],
        vencimento=vencimento,
        status="em andamento"
    )

    db.session.add(acordo)
    db.session.commit()

    return acordo

def listar():
    return Acordo.query.all()

def obter_acordo(id):
    acordo = Acordo.query.get(id)
    if not acordo:
        raise ValueError("Acordo não encontrado.")
    return acordo

def atualizar_acordo(id, data):
    acordo = Acordo.query.get(id)
    if not acordo:
        raise ValueError("Acordo não encontrado.")

    if "contrato_id" in data:
        contrato = Contrato.query.filter_by(numero_contrato=data["contrato_id"]).first()
        if not contrato:
            raise ValueError("Contrato não encontrado.")
        acordo.contrato_id = data["contrato_id"]

    if "tipo_pagamento" in data:
        if data["tipo_pagamento"] not in ["avista", "parcelado"]:
            raise ValueError("Tipo de pagamento deve ser 'avista' ou 'parcelado'.")
        acordo.tipo_pagamento = data["tipo_pagamento"]

    if "qtd_parcelas" in data:
        qtd_parcelas = int(data["qtd_parcelas"])
        if not (1 <= qtd_parcelas <= 24):
            raise ValueError("Quantidade de parcelas deve estar entre 1 e 24.")
        acordo.qtd_parcelas = qtd_parcelas

    if "valor_total" in data:
        acordo.valor_total = data["valor_total"]

    if "vencimento" in data:
        try:
            vencimento = datetime.strptime(data["vencimento"], "%Y-%m-%d")
            acordo.vencimento = vencimento
        except ValueError:
            raise ValueError("Formato de data inválido para vencimento. Use 'YYYY-MM-DD'.")

    db.session.commit()
    return acordo

def deletar_acordo(id):
    acordo = Acordo.query.get(id)
    if not acordo:
        raise ValueError("Acordo não encontrado.")
    
    db.session.delete(acordo)
    db.session.commit()
    return True