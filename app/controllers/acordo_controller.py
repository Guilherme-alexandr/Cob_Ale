from datetime import datetime
from app.database import db
from app.models.cliente import Cliente
from app.models.acordo import Acordo, Boleto
from app.models.contrato import Contrato
from importadores import boletos
from calculadora import calcular
import json, os


def calcular_dias_atraso(vencimento):
    hoje = datetime.utcnow()
    atraso = (hoje - vencimento).days
    return max(atraso, 0)

def criar_acordo(data):
    contrato = Contrato.query.filter_by(numero_contrato=data["contrato_id"]).first()
    if not contrato:
        raise ValueError("Contrato não encontrado.")

    tipo_pagamento = data.get("tipo_pagamento")
    qtd_parcelas = int(data.get("qtd_parcelas", 0))

    if tipo_pagamento == "parcelado" and qtd_parcelas < 2:
        raise ValueError("Parcelamento deve ser de no mínimo 2 parcelas.")

    dias_em_atraso = calcular_dias_atraso(contrato.vencimento)

    resultado_calculo = calcular({
    "valor_original": contrato.valor_total,
    "dias_em_atraso": dias_em_atraso,
    "tipo_pagamento": tipo_pagamento,
    "quantidade_parcelas": qtd_parcelas,
    "valor_entrada": data.get("valor_entrada")
})


    acordo = Acordo(
        contrato_id=contrato.numero_contrato,
        tipo_pagamento=tipo_pagamento,
        qtd_parcelas=qtd_parcelas,
        valor_total=resultado_calculo["valor_final"],
        vencimento=datetime.strptime(data["vencimento"], "%Y-%m-%d"),
        status="em andamento",
        parcelamento_json=json.dumps(resultado_calculo.get("parcelamento")) if resultado_calculo.get("parcelamento") else None
    )

    db.session.add(acordo)
    db.session.commit()

    return {
        "acordo": {
            "id": acordo.id,
            "valor_final": resultado_calculo["valor_final"],
            "dias_em_atraso": dias_em_atraso,
            "parcelamento": resultado_calculo.get("parcelamento")
        }
    }


def listar_acordos():
    return Acordo.query.all()

def obter_acordo(id):
    return Acordo.query.get(id)

def obter_acordo_por_contrato(numero_contrato):
    return Acordo.query.filter_by(contrato_id=numero_contrato).first()

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

def simular_acordo(payload):
    if not payload:
        raise ValueError("Payload não fornecido.")

    campos_obrigatorios = ["valor_original", "dias_em_atraso", "tipo_pagamento"]
    for campo in campos_obrigatorios:
        if campo not in payload:
            raise ValueError(f"Campo obrigatório '{campo}' ausente.")

    if payload.get("tipo_pagamento") == "parcelado" and "quantidade_parcelas" not in payload:
        raise ValueError("Campo 'quantidade_parcelas' é obrigatório para parcelamento.")

    resultado = calcular(payload)

    return resultado

def deletar_acordo(id):
    acordo = Acordo.query.get(id)
    if not acordo:
        return None

    db.session.delete(acordo)
    db.session.commit()
    return True

def gerar_boleto(acordo_id):
    acordo = Acordo.query.get(acordo_id)
    if not acordo:
        raise Exception("Acordo não encontrado")

    contrato = Contrato.query.filter_by(numero_contrato=acordo.contrato_id).first()
    if not contrato:
        raise Exception("Contrato não encontrado")

    cliente = Cliente.query.get(contrato.cliente_id)
    if not cliente:
        raise Exception("Cliente não encontrado")


    contrato_dict = {"numero_contrato": contrato.numero_contrato, "filial": contrato.filial}
    acordo_dict = {
        "id": acordo.id,
        "vencimento": acordo.vencimento.strftime("%Y-%m-%d"),
        "valor": acordo.valor_total
    }
    cliente_dict = {"nome": cliente.nome, "cpf": cliente.cpf, "email": cliente.email}

    pasta_boletos = r"C:\Users\guilh\OneDrive\Documentos\CobAle_boletos"
    os.makedirs(pasta_boletos, exist_ok=True) 

    nome_arquivo = f"boleto_{acordo.id}.pdf"
    caminho_pdf = os.path.join(pasta_boletos, nome_arquivo)

    boletos.gerar_boleto(contrato_dict, acordo_dict, cliente_dict, caminho_pdf)

    novo_boleto = Boleto(acordo_id=acordo.id, caminho_pdf=caminho_pdf)
    db.session.add(novo_boleto)
    db.session.commit()

    return {
        "mensagem": "Boleto gerado com sucesso",
        "boleto_id": novo_boleto.id,
        "caminho_pdf": caminho_pdf
    }


def enviar_boleto(boleto_id):
    boleto = Boleto.query.get(boleto_id)
    if not boleto:
        raise Exception("Boleto não encontrado")

    acordo = Acordo.query.get(boleto.acordo_id)
    contrato = Contrato.query.filter_by(numero_contrato=acordo.contrato_id).first()
    cliente = Cliente.query.get(contrato.cliente_id)

    boletos.enviar_boleto_email(cliente.email, boleto.caminho_pdf)

    boleto.enviado = True
    db.session.commit()

    return {"mensagem": f"Boleto enviado para {cliente.email}", "boleto_id": boleto.id}