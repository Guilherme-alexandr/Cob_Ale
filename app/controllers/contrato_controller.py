from app.database import db
from datetime import datetime
from app.models.contrato import Contrato

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

def deletar_contrato(numero_contrato):
    contrato = Contrato.query.get(numero_contrato)
    if not contrato:
        return None
    db.session.delete(contrato)
    db.session.commit()
    return contrato

def buscar_contratos_por_cliente(cliente_id):
    return Contrato.query.filter_by(cliente_id=cliente_id).all()

