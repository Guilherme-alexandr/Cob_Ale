from app.database import db
from app.models.cliente import Cliente

def criar_cliente(data):
    cliente = Cliente(**data)
    db.session.add(cliente)
    db.session.commit()
    return cliente

def listar_clientes():
    return Cliente.query.all()
