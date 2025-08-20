from flask import current_app, render_template
from datetime import datetime
from app.database import db
from app.models.cliente import Cliente
from app.models.acordo import Acordo, Boleto
from app.models.contrato import Contrato
from importadores import boletos
from calculadora import calcular
import json, os, io, base64, qrcode, barcode
from barcode.writer import ImageWriter
from weasyprint import HTML


# ------------------- Helpers -------------------

def _pasta_boletos():
    """Retorna o caminho absoluto da pasta de boletos"""
    pasta = os.path.join(current_app.root_path, "..", "boletos")
    os.makedirs(pasta, exist_ok=True)
    return os.path.abspath(pasta)


def _calcular_dias_atraso(vencimento):
    hoje = datetime.utcnow()
    atraso = (hoje - vencimento).days
    return max(atraso, 0)


# ------------------- Acordos -------------------

def criar_acordo(data):
    contrato = Contrato.query.filter_by(numero_contrato=data["contrato_id"]).first()
    if not contrato:
        raise ValueError("Contrato não encontrado.")

    tipo_pagamento = data.get("tipo_pagamento")
    qtd_parcelas = int(data.get("qtd_parcelas", 0))

    if tipo_pagamento == "parcelado" and qtd_parcelas < 2:
        raise ValueError("Parcelamento deve ser de no mínimo 2 parcelas.")

    dias_em_atraso = _calcular_dias_atraso(contrato.vencimento)

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


def deletar_acordo(id):
    acordo = Acordo.query.get(id)
    if not acordo:
        return None

    pasta_boletos = _pasta_boletos()

    # Remover PDFs da pasta
    for boleto in acordo.boletos:
        for arquivo in os.listdir(pasta_boletos):
            if arquivo.startswith(f"boleto_{acordo.id}") and arquivo.endswith(".pdf"):
                try:
                    os.remove(os.path.join(pasta_boletos, arquivo))
                except Exception as e:
                    print(f"Erro ao apagar {arquivo}: {e}")

    # Remover registros do banco
    for boleto in acordo.boletos:
        db.session.delete(boleto)

    db.session.delete(acordo)
    db.session.commit()
    return True


# ------------------- Simulação -------------------

def simular_acordo(payload):
    if not payload:
        raise ValueError("Payload não fornecido.")

    campos_obrigatorios = ["valor_original", "dias_em_atraso", "tipo_pagamento"]
    for campo in campos_obrigatorios:
        if campo not in payload:
            raise ValueError(f"Campo obrigatório '{campo}' ausente.")

    if payload.get("tipo_pagamento") == "parcelado" and "quantidade_parcelas" not in payload:
        raise ValueError("Campo 'quantidade_parcelas' é obrigatório para parcelamento.")

    return calcular(payload)


# ------------------- Boletos -------------------

def info_boleto(acordo_id):
    acordo = Acordo.query.get(acordo_id)
    if not acordo:
        return {"erro": "Acordo não encontrado"}, 404

    contrato = acordo.contrato
    if not contrato:
        return {"erro": "Contrato não encontrado"}, 404

    cliente = contrato.cliente
    if not cliente:
        return {"erro": "Cliente não encontrado"}, 404

    if acordo.parcelamento_json:
        parcelamento = json.loads(acordo.parcelamento_json)
        valor_parcela = parcelamento.get("valor_parcela", acordo.valor_total / acordo.qtd_parcelas)
        entrada = parcelamento.get("entrada", 0)
    else:
        valor_parcela = acordo.valor_total / acordo.qtd_parcelas
        entrada = 0

    demonstrativo = (
        f"Acordo formalizado para pagamento: R$ {entrada:.2f} "
        f"+ {acordo.qtd_parcelas} parcelas: R$ {valor_parcela:.2f}; "
        f"vencimento {acordo.vencimento.strftime('%d/%m/%Y')}"
    )

    boleto_info = {
        "sacado": cliente.nome,
        "vencimento": acordo.vencimento.strftime("%d/%m/%Y"),
        "valor_documento": round(acordo.valor_total, 2),
        "filial_loja": contrato.filial,
        "demonstrativo": demonstrativo,
        "descontos_abatimento": 0,
        "mora_multa": 0,
        "nosso_numero": str(acordo.id).zfill(7),
        "linha_digitavel": str(acordo.id).zfill(11),
        "cep_sacado": "00000-000",
        "endereco_sacado": "Rua Fictícia, 123",
        "cidade_sacado": "Cidade Exemplo",
        "estado_sacado": "UF",
    }

    return boleto_info, 200


def gerar_boleto(acordo_id):
    """Gera (ou busca do banco) o PDF de um boleto e retorna o binário + nome do arquivo"""
    acordo = Acordo.query.get_or_404(acordo_id)
    boleto = Boleto.query.filter_by(acordo_id=acordo.id).first()

    if boleto and boleto.pdf_arquivo:
        return boleto.pdf_arquivo, boleto.nome_arquivo

    boleto_info, status = info_boleto(acordo_id)
    if status != 200:
        raise ValueError("Erro ao gerar informações do boleto.")

    # QR Code
    qr = qrcode.QRCode(box_size=4, border=1)
    qr.add_data(f"https://www.seuboleto.com.br/gerar?codigo={boleto_info['nosso_numero']}")
    qr.make(fit=True)
    buf_qr = io.BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(buf_qr, format="PNG")
    qr_code_b64 = base64.b64encode(buf_qr.getvalue()).decode("utf-8")

    # Código de barras
    CODE128 = barcode.get_barcode_class("code128")
    bar = CODE128(boleto_info["nosso_numero"], writer=ImageWriter())
    buf_bar = io.BytesIO()
    bar.write(buf_bar)
    barcode_b64 = base64.b64encode(buf_bar.getvalue()).decode("utf-8")

    # Logo
    logo_path = os.path.join(current_app.root_path, "..", "importadores", "img", "logo_CobAle.png")
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("utf-8")

    # HTML → PDF
    html = render_template("boleto.html", boleto=boleto_info, qr_code=qr_code_b64, barcode_img=barcode_b64, logo_b64=logo_b64)
    pdf = HTML(string=html).write_pdf()

    # Salvar em disco
    pasta = _pasta_boletos()
    nome_arquivo = f"boleto_{acordo.id}.pdf"
    caminho_pdf = os.path.join(pasta, nome_arquivo)
    with open(caminho_pdf, "wb") as f:
        f.write(pdf)

    # Salvar no banco
    boleto = Boleto(acordo_id=acordo.id, pdf_arquivo=pdf, nome_arquivo=nome_arquivo, criado_em=datetime.utcnow(), enviado=False)
    db.session.add(boleto)
    db.session.commit()

    return pdf, nome_arquivo


def enviar_boleto(acordo_id=None, boleto_id=None):
    """Envia um boleto por email (acordo_id opcional, boleto_id obrigatório)"""
    if not boleto_id:
        raise ValueError("boleto_id é obrigatório")

    pasta = _pasta_boletos()
    arquivos = [f for f in os.listdir(pasta) if f.startswith("boleto_") and f.endswith(".pdf")]

    if not arquivos:
        raise ValueError("Nenhum boleto encontrado")

    if boleto_id < 1 or boleto_id > len(arquivos):
        raise ValueError("Boleto não encontrado")

    nome_arquivo = arquivos[boleto_id - 1]
    caminho_pdf = os.path.join(pasta, nome_arquivo)

    if not os.path.exists(caminho_pdf):
        raise ValueError(f"Arquivo {nome_arquivo} não encontrado")

    if acordo_id:
        acordo = Acordo.query.get(acordo_id)
        if not acordo:
            raise ValueError("Acordo não encontrado")
        contrato = Contrato.query.get(acordo.contrato_id)
        if not contrato:
            raise ValueError("Contrato do acordo não encontrado")
        cliente = Cliente.query.get(contrato.cliente_id)
    else:
        acordo = Acordo.query.first()
        cliente = acordo.contrato.cliente if acordo else None

    if not cliente:
        raise ValueError("Cliente não encontrado")

    boletos.enviar_boleto_email(cliente.email, caminho_pdf)

    return {
        "mensagem": f"Boleto enviado com sucesso para {cliente.email}",
        "acordo_id": acordo.id if acordo else None,
        "boleto_id": boleto_id,
        "arquivo": nome_arquivo,
    }


def listar_boletos_por_pasta(acordo_id):
    pasta = _pasta_boletos()
    arquivos = [f for f in os.listdir(pasta) if f.startswith(f"boleto_{acordo_id}") and f.endswith(".pdf")]

    return [{"boleto_id": idx, "nome_arquivo": arquivo} for idx, arquivo in enumerate(arquivos, start=1)]


def deletar_todos_boletos():
    try:
        pasta = _pasta_boletos()
        num_arquivos = 0
        if os.path.exists(pasta):
            for arquivo in os.listdir(pasta):
                if arquivo.endswith(".pdf"):
                    os.remove(os.path.join(pasta, arquivo))
                    num_arquivos += 1

        num_boletos_db = Boleto.query.count()
        Boleto.query.delete()
        db.session.commit()

        return {"mensagem": f"{num_arquivos} arquivos PDF deletados, {num_boletos_db} registros removidos do banco."}, 200

    except Exception as e:
        db.session.rollback()
        return {"erro": str(e)}, 500
