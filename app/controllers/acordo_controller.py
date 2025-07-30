import requests
from datetime import datetime
from app.database import db
from app.models.acordo import Acordo
from app.models.contrato import Contrato

def calcular_dias_atraso(vencimento):
    hoje = datetime.utcnow()
    atraso = (hoje - vencimento).days
    return max(atraso, 0)

def chamar_calculadora(valor_original, dias_em_atraso, tipo_pagamento, qtd_parcelas):
    payload = {
        "valor_original": valor_original,
        "dias_em_atraso": dias_em_atraso,
        "tipo_pagamento": tipo_pagamento,
        "quantidade_parcelas": qtd_parcelas
    }

    response = requests.post("http://127.0.0.1:5001/calcular", json=payload)

    if response.status_code != 200:
        raise ValueError("Erro ao calcular valor do acordo.")

    return response.json()

def criar_acordo(data):
    contrato = Contrato.query.filter_by(numero_contrato=data["contrato_id"]).first()
    if not contrato:
        raise ValueError("Contrato não encontrado.")

    tipo_pagamento = data.get("tipo_pagamento")
    qtd_parcelas = int(data.get("qtd_parcelas", 0))

    if tipo_pagamento == "parcelado" and qtd_parcelas < 2:
        raise ValueError("Parcelamento deve ser de no mínimo 2 parcelas.")

    dias_em_atraso = calcular_dias_atraso(contrato.vencimento)

    resultado_calculo = chamar_calculadora(
        valor_original=contrato.valor_total,
        dias_em_atraso=dias_em_atraso,
        tipo_pagamento=tipo_pagamento,
        qtd_parcelas=qtd_parcelas
    )

    acordo = Acordo(
        contrato_id=contrato.numero_contrato,
        tipo_pagamento=tipo_pagamento,
        qtd_parcelas=qtd_parcelas,
        valor_total=resultado_calculo["valor_final"],
        vencimento=datetime.strptime(data["vencimento"], "%Y-%m-%d"),
        status="em andamento"
    )

    db.session.add(acordo)
    db.session.commit()

    return {
        "acordo": {
            "id": acordo.id,
            "valor_final": resultado_calculo["valor_final"],
            "dias_em_atraso": dias_em_atraso,
            "parcelamento": resultado_calculo.get("parcelamento", None)
        }
    }

def listar_acordos():
    return Acordo.query.all()

def obter_acordo(id):
    return Acordo.query.get(id)

def atualizar_acordo(id, data):
    acordo = Acordo.query.get(id)
    if not acordo:
        return None
    if "tipo_pagamento" in data:
        acordo.tipo_pagamento = data["tipo_pagamento"]
    if "qtd_parcelas" in data:
        acordo.qtd_parcelas = data["qtd_parcelas"]
    if "valor_total" in data:
        acordo.valor_total = data["valor_total"]
    if "vencimento" in data:
        acordo.vencimento = datetime.strptime(data["vencimento"], "%Y-%m-%d")
    if "status" in data:
        acordo.status = data["status"]

    db.session.commit()
    return acordo

def deletar_acordo(id):
    acordo = Acordo.query.get(id)
    if not acordo:
        return None

    db.session.delete(acordo)
    db.session.commit()
    return True