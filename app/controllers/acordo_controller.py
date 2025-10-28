from flask import current_app
from datetime import datetime, date
from app.database import db
from app.models.cliente import Cliente
from app.models.acordo import Acordo, Boleto
from app.models.contrato import Contrato
from importadores import boletos
from calculadora import calcular
import json, os, barcode
from barcode.writer import ImageWriter
from docxtpl import DocxTemplate, InlineImage
from docx2pdf import convert
from docx.shared import Mm
import pythoncom
pythoncom.CoInitialize()
pythoncom.CoUninitialize()

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
    try:
        current_app.logger.info(f"🧾 [DEBUG] Buscando info do boleto para acordo_id={acordo_id}")
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
        current_app.logger.info(f"✅ Cliente: {cliente.nome}")

        qtd_parcelas = acordo.qtd_parcelas if acordo.qtd_parcelas > 0 else 1
        valor_parcela = (
            json.loads(acordo.parcelamento_json).get("valor_parcela", acordo.valor_total / qtd_parcelas)
            if acordo.parcelamento_json else acordo.valor_total / qtd_parcelas
        )
        entrada = (
            json.loads(acordo.parcelamento_json).get("entrada", 0)
            if acordo.parcelamento_json else 0
        )

        demonstrativo = (
            f"Acordo formalizado para pagamento: R$ {entrada:.2f} "
            f"+ {acordo.qtd_parcelas} parcelas: R$ {valor_parcela:.2f}; "
            f"vencimento {acordo.vencimento.strftime('%d/%m/%Y')}"
        )
        current_app.logger.info(f"🧩 Demonstrativo: {demonstrativo}")

        current_app.logger.info("🧩 Gerando linha digitável...")
        codigo_barras, linha_digitavel = gerar_linha_digitavel(acordo)
        nosso_numero = str(acordo.id).zfill(11)
        current_app.logger.info(f"🔥 Código de barras: {codigo_barras} | Linha digitável: {linha_digitavel} | Nosso número: {nosso_numero}")

        base_dir = os.path.dirname(__file__)
        caminho_img = os.path.join(base_dir, f"codigo_barras_{acordo.id}.png")

        info = {
            "acordo_id": acordo.id,
            "cliente": cliente.nome,
            "contrato": getattr(contrato, "numero", "N/A"),
            "sacado": cliente.nome,
            "vencimento": acordo.vencimento.strftime("%d/%m/%Y"),
            "valor_documento": float(acordo.valor_total),
            "filial_loja": getattr(contrato, "filial", "N/A"),
            "demonstrativo": demonstrativo,
            "desconto": float(acordo.desconto or 0),
            "juros": float(acordo.juros or 0),
            "nosso_numero": nosso_numero,
            "linha_digitavel": linha_digitavel,
            "codigo_barras": codigo_barras,
            "cep_sacado": endereco.cep if endereco else "00000-000",
            "endereco_sacado": f"{endereco.rua}, {endereco.numero}" if endereco else "Endereço não informado",
            "cidade_sacado": endereco.cidade if endereco else "Cidade não informada",
            "estado_sacado": endereco.estado if endereco else "UF",
            "data_documento": datetime.utcnow().strftime("%d/%m/%Y"),
            "data_processamento": datetime.utcnow().strftime("%d/%m/%Y"),
            "caminho_img": caminho_img
        }

        return info, 200

    except Exception as e:
        current_app.logger.error("🔥 ERRO DETALHADO info_boleto:")
        current_app.logger.exception(e)
        return {"erro": str(e)}, 500


def gerar_boleto_novo(acordo_id):
    try:
        info, status = info_boleto(acordo_id)
        if status != 200:
            return None, info.get("erro", "Erro ao gerar boleto"), None

        acordo = Acordo.query.get_or_404(acordo_id)
        boleto = Boleto.query.filter_by(acordo_id=acordo.id).first()

        pasta = _pasta_boletos()
        if not os.path.exists(pasta):
            os.makedirs(pasta)

        nome_arquivo = f"boleto_{acordo.id}.pdf"
        caminho_pdf = os.path.join(pasta, nome_arquivo)

        if boleto and os.path.exists(caminho_pdf):
            current_app.logger.info(f"📄 Boleto já existente encontrado: {caminho_pdf}")
            with open(caminho_pdf, "rb") as f:
                pdf_bytes = f.read()
            return pdf_bytes, nome_arquivo, boleto.id
        
        current_app.logger.info(f"[DEBUG] Iniciando geração de boleto para acordo_id={acordo_id}")

        base_dir = os.path.dirname(__file__)
        template_path = os.path.join(base_dir, r"C:\Users\guilh\Desktop\Meus projetos\Cob_Ale\importadores\Boleto CobAle.docx")
        current_app.logger.info(f"🗂️ Template path usado: {template_path}")
        doc = DocxTemplate(template_path)

        caminho_img_sem_ext = info["caminho_img"].replace(".png", "")
        ean = barcode.get("code128", info["codigo_barras"], writer=ImageWriter())
        ean.save(caminho_img_sem_ext)
        caminho_img_final = caminho_img_sem_ext + ".png"
        info["caminho_img"] = caminho_img_final

        if not os.path.exists(caminho_img_final):
            raise FileNotFoundError(f"Código de barras não foi gerado: {caminho_img_final}")

        info_boleto_docx = info.copy()
        info_boleto_docx["codigo_barras_img"] = InlineImage(doc, caminho_img_final, width=Mm(80))

        current_app.logger.info("📝 Renderizando DOCX...")
        doc.render(info_boleto_docx)

        temp_docx = os.path.join(base_dir, f"temp_boleto_{acordo.id}.docx")
        doc.save(temp_docx)

        try:
            pythoncom.CoInitialize()
            convert(temp_docx, caminho_pdf)
            current_app.logger.info(f"✅ PDF convertido com sucesso: {caminho_pdf}")
        except Exception as e:
            current_app.logger.error(f"❌ Erro ao converter DOCX para PDF: {e}", exc_info=True)
            raise
        finally:
            pythoncom.CoUninitialize()

        if os.path.exists(temp_docx):
            os.remove(temp_docx)
        if os.path.exists(caminho_img_final):
            os.remove(caminho_img_final)

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

        db.session.commit()

        with open(caminho_pdf, "rb") as f:
            pdf_bytes = f.read()

        current_app.logger.info(f"✅ Boleto gerado com sucesso: {caminho_pdf}")
        return pdf_bytes, nome_arquivo, boleto.id

    except Exception as e:
        current_app.logger.error("🔥 ERRO DETALHADO gerar_boleto_novo:")
        current_app.logger.exception(e)
        raise



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
        gerar_boleto_novo(acordo.id)

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
    

def gerar_linha_digitavel(acordo, banco="237", carteira="09", agencia="1234", conta="56789"):
    """
    Gera o código de barras e a linha digitável do boleto.

    :param acordo: Objeto Acordo
    :param banco: Código do banco (default 237 - Bradesco)
    :param carteira: Carteira do boleto
    :param agencia: Número da agência
    :param conta: Número da conta
    :return: tuple(codigo_barras, linha_digitavel)
    """

    # Dados do boleto
    codigo_banco = banco
    moeda = "9"
    data_base = date(1997, 10, 7)
    fator_vencimento = (acordo.vencimento.date() - data_base).days
    fator_vencimento = str(fator_vencimento).zfill(4)

    valor = int(round(acordo.valor_total * 100))  # valor em centavos
    valor_str = str(valor).zfill(10)

    nosso_numero = str(acordo.id).zfill(11)
    campo_livre = f"{carteira}{nosso_numero}{agencia}{conta}".ljust(25, "0")

    codigo_sem_dv = f"{codigo_banco}{moeda}{fator_vencimento}{valor_str}{campo_livre}"
    dv = calcular_dv(codigo_sem_dv)
    codigo_barras = f"{codigo_banco}{moeda}{dv}{fator_vencimento}{valor_str}{campo_livre}"

    # Formata linha digitável em blocos
    bloco1 = f"{codigo_barras[0:5]}.{codigo_barras[5:10]}"
    bloco2 = f"{codigo_barras[10:15]}.{codigo_barras[15:21]}"
    bloco3 = f"{codigo_barras[21:26]}.{codigo_barras[26:32]}"
    bloco4 = codigo_barras[32]
    bloco5 = codigo_barras[33:]

    linha_digitavel = f"{bloco1} {bloco2} {bloco3} {bloco4} {bloco5}"

    return codigo_barras, linha_digitavel


def calcular_dv(codigo):
    """
    Calcula o dígito verificador usando módulo 11.
    """
    pesos = [2,3,4,5,6,7,8,9]
    soma = sum(int(n) * pesos[i % len(pesos)] for i, n in enumerate(reversed(codigo)))
    resto = soma % 11
    dv = 11 - resto
    if dv > 9:
        dv = 0
    return str(dv)