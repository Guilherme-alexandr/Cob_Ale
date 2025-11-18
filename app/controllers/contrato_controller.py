from app.database import db
from datetime import datetime
from app.models.contrato import Contrato
import os
from docx import Document

def gerar_numero_contrato():
    ultimo = db.session.query(Contrato).order_by(Contrato.numero_contrato.desc()).first()
    if not ultimo:
        return "000001"
    proximo = int(ultimo.numero_contrato) + 1
    return f"{proximo:06d}"

def criar_contrato(data): 
    
    numero = gerar_numero_contrato()
    try:
        vencimento = datetime.strptime(data["vencimento"], "%Y-%m-%d")
    except ValueError:
        raise ValueError("Data de vencimento inválida. Use o formato YYYY-MM-DD.")
    contrato = Contrato(
        numero_contrato=numero,
        cliente_id=data["cliente_id"],
        valor_total=data["valor_total"],
        filial=data["filial"],
        vencimento=vencimento
    )
    db.session.add(contrato)
    db.session.commit()
    return contrato

def listar_contratos():
    return Contrato.query.all()

def obter_contrato(numero_contrato):
    return Contrato.query.get(numero_contrato)

def atualizar_contrato(numero_contrato, data):
    contrato = Contrato.query.get(numero_contrato)
    if not contrato:
        return None
    for key, value in data.items():
        setattr(contrato, key, value)
    db.session.commit()
    return contrato

def buscar_contratos_por_cliente(cliente_id):
    return Contrato.query.filter_by(cliente_id=cliente_id).all()

def buscar_contratos_por_filial(filial: str):
    if not filial:
        raise ValueError("Filial não pode ser vazia.")
    return Contrato.query.filter(Contrato.filial.ilike(f"%{filial}%")).all()

def buscar_contratos_por_valor(valor_minimo=None, valor_maximo=None):
    query = Contrato.query

    try:
        if valor_minimo is not None:
            valor_minimo = float(valor_minimo)
            query = query.filter(Contrato.valor_total >= valor_minimo)
        if valor_maximo is not None:
            valor_maximo = float(valor_maximo)
            query = query.filter(Contrato.valor_total <= valor_maximo)
    except ValueError:
        raise ValueError("Os valores mínimo e máximo devem ser numéricos.")

    contratos = query.all()
    return [contrato_to_dict(c) for c in contratos]


def buscar_contratos_por_vencimento(data_inicio=None, data_fim=None):
    query = Contrato.query

    try:
        if data_inicio and data_fim:
            dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            dt_fim = datetime.strptime(data_fim, "%Y-%m-%d")
            query = query.filter(Contrato.vencimento.between(dt_inicio, dt_fim))
        elif data_inicio:
            dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(db.func.date(Contrato.vencimento) == dt_inicio.date())
        else:
            raise ValueError("É necessário informar ao menos uma data de vencimento.")
    except ValueError:
        raise ValueError("Formato de data inválido. Use YYYY-MM-DD.")

    contratos = query.all()
    return [c.numero_contrato for c in contratos]

def deletar_contrato(numero_contrato):
    contrato = Contrato.query.get(numero_contrato)
    if not contrato:
        return None
    db.session.delete(contrato)
    db.session.commit()
    return contrato


def resetar_contratos():
    try:
        db.session.query(Contrato).delete()
        db.session.commit()
        return {"mensagem": "Todos os contratos foram excluídos com sucesso."}
    except Exception as e:
        db.session.rollback()
        return {"erro": f"Erro ao excluir contratos: {str(e)}"}


def importar_contratos_docx(caminho_arquivo, app):
    with app.app_context():
        doc = Document(caminho_arquivo)
        contratos_importados = 0
        contratos_atualizados = 0

        for tabela in doc.tables:
            for i, linha in enumerate(tabela.rows):
                if i == 0:
                    continue

                numero_contrato = linha.cells[0].text.strip()
                cliente_id = int(linha.cells[1].text.strip())
                vencimento_str = linha.cells[2].text.strip()
                valor_total = float(linha.cells[3].text.strip().replace(',', '.'))
                filial = linha.cells[4].text.strip()

                try:
                    vencimento = datetime.strptime(vencimento_str, "%Y-%m-%d")
                except ValueError:
                    print(f"Data inválida na linha {i + 1}: {vencimento_str}")
                    continue

                contrato = Contrato.query.filter_by(numero_contrato=numero_contrato).first()

                if contrato is not None:
                    contrato.cliente_id = cliente_id
                    contrato.vencimento = vencimento
                    contrato.valor_total = valor_total
                    contrato.filial = filial

                    contratos_atualizados += 1
                    print(f"Contrato {numero_contrato} atualizado.")
                else:
                    contrato = Contrato(
                        numero_contrato=numero_contrato,
                        cliente_id=cliente_id,
                        vencimento=vencimento,
                        valor_total=valor_total,
                        filial=filial
                    )
                    db.session.add(contrato)
                    contratos_importados += 1
                    print(f"Contrato {numero_contrato} adicionado.")

        db.session.commit()
        print(f"Importação concluída: {contratos_importados} contratos adicionados, {contratos_atualizados} contratos atualizados.")

def contrato_to_dict(contrato):
    return {
        "numero_contrato": contrato.numero_contrato,
        "cliente_id": contrato.cliente_id,
        "vencimento": contrato.vencimento.strftime("%Y-%m-%d"),
        "valor_total": contrato.valor_total,
        "filial": contrato.filial
    }