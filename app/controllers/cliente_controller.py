from app.database import db
from app.models.cliente import Cliente

def criar_cliente(data):
    cliente = Cliente(**data)
    db.session.add(cliente)
    db.session.commit()
    return cliente

def listar_clientes():
    return Cliente.query.all()

def obter_cliente(id):
    return Cliente.query.get(id)

def atualizar_cliente(id, data):
    cliente = Cliente.query.get(id)
    if not cliente:
        return None
    for key, value in data.items():
        setattr(cliente, key, value) 
    db.session.commit()
    return cliente

def deletar_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        return None
    db.session.delete(cliente)
    db.session.commit()
    return cliente

def buscar_cliente_por_cpf(cpf):
    return Cliente.query.filter_by(cpf=cpf).first()

def buscar_clientes_por_nome(nome):
    return Cliente.query.filter(Cliente.nome.ilike(f"%{nome}%")).all()
