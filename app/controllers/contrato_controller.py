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
