from flask import current_app, render_template
from datetime import datetime, date
from app.database import db
from app.models.cliente import Cliente
from app.models.acordo import Acordo, Boleto
from app.models.contrato import Contrato
from importadores import boletos
from calculadora import calcular
from reportlab.graphics import renderPM
from reportlab.graphics.barcode import code128
from reportlab.graphics.shapes import Drawing
from reportlab.lib.units import mm
import json, os, io, base64, barcode
from barcode.writer import ImageWriter
from weasyprint import HTML


# ------------------- Helpers -------------------

def _pasta_boletos():
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
        desconto=resultado_calculo["valor_desconto"],
        juros=resultado_calculo["juros_total"],
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
            "juros": resultado_calculo["juros_total"],
            "desconto": resultado_calculo["valor_desconto"],
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
    if "desconto" in data:
        acordo.desconto = data["desconto"]
    if "juros" in data:
        acordo.juros = data["juros"]
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

    for boleto in acordo.boletos:
        for arquivo in os.listdir(pasta_boletos):
            if arquivo.startswith(f"boleto_{acordo.id}") and arquivo.endswith(".pdf"):
                try:
                    os.remove(os.path.join(pasta_boletos, arquivo))
                except Exception as e:
                    print(f"Erro ao apagar {arquivo}: {e}")

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
    
    endereco = cliente.enderecos[0] if cliente.enderecos else None

    qtd_parcelas = acordo.qtd_parcelas if acordo.qtd_parcelas > 0 else 1
    valor_parcela = (json.loads(acordo.parcelamento_json).get("valor_parcela", acordo.valor_total / qtd_parcelas) 
                     if acordo.parcelamento_json else acordo.valor_total / qtd_parcelas)
    entrada = (json.loads(acordo.parcelamento_json).get("entrada", 0) 
               if acordo.parcelamento_json else 0)

    demonstrativo = (
        f"Acordo formalizado para pagamento: R$ {entrada:.2f} "
        f"+ {acordo.qtd_parcelas} parcelas: R$ {valor_parcela:.2f}; "
        f"vencimento {acordo.vencimento.strftime('%d/%m/%Y')}"
    )
    codigo_barras, linha_digitavel = gerar_linha_digitavel(acordo.id)

    boleto_info = {
        "sacado": cliente.nome,
        "vencimento": acordo.vencimento.strftime("%d/%m/%Y"),
        "valor_documento": round(acordo.valor_total, 2),
        "filial_loja": contrato.filial,
        "demonstrativo": demonstrativo,
        "desconto": float(acordo.desconto or 0),
        "juros": float(acordo.juros or 0),
        "nosso_numero": str(acordo.id).zfill(11),
        "linha_digitavel": linha_digitavel,
        "codigo_barras": codigo_barras,

        "cep_sacado": endereco.cep if endereco else "00000-000",
        "endereco_sacado": f"{endereco.rua}, {endereco.numero}" if endereco else "Endereço não informado",
        "cidade_sacado": endereco.cidade if endereco else "Cidade não informada",
        "estado_sacado": endereco.estado if endereco else "UF"
    }

    return boleto_info, 200


def gerar_boleto(acordo_id):
    acordo = Acordo.query.get_or_404(acordo_id)
    boleto = Boleto.query.filter_by(acordo_id=acordo.id).first()

    pasta = _pasta_boletos()
    if not os.path.exists(pasta):
        os.makedirs(pasta)

    nome_arquivo = f"boleto_{acordo.id}.pdf"
    caminho_pdf = os.path.join(pasta, nome_arquivo)

    if boleto and os.path.exists(caminho_pdf):
        with open(caminho_pdf, "rb") as f:
            return f.read(), boleto.nome_arquivo

    boleto_info, status = info_boleto(acordo_id)
    if status != 200:
        raise ValueError("Erro ao gerar informações do boleto.")

    codigo_barras, linha_digitavel = gerar_linha_digitavel(acordo)
    boleto_info["linha_digitavel"] = linha_digitavel
    boleto_info["codigo_barras"] = codigo_barras

    if not codigo_barras.isdigit():
        raise ValueError("Código de barras deve ser uma sequência numérica.")

    barcode_class = barcode.get_barcode_class("code128")
    barcode_obj = barcode_class(codigo_barras, writer=ImageWriter())
    buf_bar = io.BytesIO()
    barcode_obj.write(buf_bar)
    barcode_b64 = base64.b64encode(buf_bar.getvalue()).decode("utf-8")

    logo_path = os.path.join(current_app.root_path, "..", "importadores", "img", "logo_CobAle.png")
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode("utf-8")

    html = render_template("boleto.html", boleto=boleto_info, barcode_img=barcode_b64, logo_b64=logo_b64)
    pdf = HTML(string=html).write_pdf()

    if not pdf or not isinstance(pdf, bytes):
        raise ValueError("Erro ao gerar o PDF do boleto.")

    with open(caminho_pdf, "wb") as f:
        f.write(pdf)

    if not boleto:
        boleto = Boleto(
            acordo_id=acordo.id,
            nome_arquivo=nome_arquivo,
            criado_em=datetime.utcnow(),
            enviado=False
        )
        db.session.add(boleto)
    else:
        boleto.nome_arquivo = nome_arquivo
        boleto.criado_em = datetime.utcnow()

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao salvar boleto no banco: {e}")
        raise

    return pdf, nome_arquivo


def enviar_boleto(acordo_id):
    acordo = Acordo.query.get_or_404(acordo_id)

    contrato = Contrato.query.get(acordo.contrato_id)
    if not contrato:
        raise ValueError("Contrato não encontrado.")

    cliente = Cliente.query.get(contrato.cliente_id)
    if not cliente or not cliente.email:
        raise ValueError("Cliente não encontrado ou sem e-mail cadastrado.")

    pasta = _pasta_boletos()
    nome_arquivo = f"boleto_{acordo.id}.pdf"
    caminho_pdf = os.path.join(pasta, nome_arquivo)

    if not os.path.exists(caminho_pdf):
        print(f"[INFO] Boleto não encontrado em disco, gerando novamente: {caminho_pdf}")
        gerar_boleto(acordo.id)

    if not os.path.exists(caminho_pdf):
        raise FileNotFoundError(f"Boleto não encontrado nem gerado: {caminho_pdf}")

    try:
        boletos.enviar_boleto_email(cliente.email, caminho_pdf)
    except Exception as e:
        raise RuntimeError(f"Erro ao enviar o e-mail: {e}")

    boleto = Boleto.query.filter_by(acordo_id=acordo.id).first()
    if boleto:
        boleto.enviado = True
        db.session.commit()

    return {
        "mensagem": f"Boleto enviado com sucesso para {cliente.email}",
        "acordo_id": acordo.id,
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
    

def gerar_linha_digitavel(acordo_id, banco="237", carteira="09", agencia="1234", conta="56789"):
    acordo = Acordo.query.get_or_404(acordo_id)
    codigo_banco = banco
    moeda = "9"
    data_base = date(1997, 10, 7)
    fator_vencimento = (acordo.vencimento.date() - data_base).days
    fator_vencimento = str(fator_vencimento).zfill(4)
    valor = int(acordo.valor_total * 100)
    valor_str = str(valor).zfill(10)
    nosso_numero = str(acordo.id).zfill(11)
    campo_livre = f"{carteira}{nosso_numero}{agencia}{conta}".ljust(25, "0")
    codigo_sem_dv = f"{codigo_banco}{moeda}{fator_vencimento}{valor_str}{campo_livre}"
    dv = calcular_dv(codigo_sem_dv)
    codigo_barras = f"{codigo_banco}{moeda}{dv}{fator_vencimento}{valor_str}{campo_livre}"
    linha_digitavel = (
        f"{codigo_barras[0:5]}.{codigo_barras[5:10]} "
        f"{codigo_barras[10:15]}.{codigo_barras[15:21]} "
        f"{codigo_barras[21:26]}.{codigo_barras[26:32]} "
        f"{codigo_barras[32]} "
        f"{codigo_barras[33:]}"
    )
    
    print(f"Código de Barras: {codigo_barras} | Linha Digitável: {linha_digitavel}")
    current_app.logger.info(f"Código de Barras: {codigo_barras} | Linha Digitável: {linha_digitavel}")
    return codigo_barras, linha_digitavel

def calcular_dv(codigo):

    pesos = [2,3,4,5,6,7,8,9]
    soma = 0
    for i, n in enumerate(reversed(codigo)):
        soma += int(n) * pesos[i % len(pesos)]
    resto = soma % 11
    dv = 11 - resto
    if dv > 9:
        dv = 0
    return str(dv)