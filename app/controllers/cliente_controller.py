from flask import jsonify
from app.database import db
from app.models.cliente import Cliente, Endereco

def criar_cliente(data):
    cliente = Cliente(
        nome=data["nome"],
        cpf=data["cpf"],
        telefone=data["telefone"],
        email=data["email"]
    )

    db.session.add(cliente)

    enderecos = data.get("enderecos", [])
    for e in enderecos:
        endereco = Endereco(
            rua=e["rua"],
            numero=e["numero"],
            cidade=e["cidade"],
            estado=e["estado"],
            cep=e["cep"],
            cliente=cliente
        )
        db.session.add(endereco)
    
    db.session.commit()
    return cliente_to_dict(cliente)


def listar_clientes():
    clientes = Cliente.query.all()
    return [cliente_to_dict(c) for c in clientes]


def obter_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        return None
    return cliente_to_dict(cliente)


def atualizar_cliente(id, data):
    cliente = Cliente.query.get(id)
    if not cliente:
        return None

    cliente.nome = data.get("nome", cliente.nome)
    cliente.cpf = data.get("cpf", cliente.cpf)
    cliente.telefone = data.get("telefone", cliente.telefone)
    cliente.email = data.get("email", cliente.email)

    if "enderecos" in data:
        for e in data["enderecos"]:
            endereco = Endereco.query.filter_by(id=e.get("id"), cliente_id=cliente.id).first()
            if endereco:
                endereco.rua = e.get("rua", endereco.rua)
                endereco.numero = e.get("numero", endereco.numero)
                endereco.cidade = e.get("cidade", endereco.cidade)
                endereco.estado = e.get("estado", endereco.estado)
                endereco.cep = e.get("cep", endereco.cep)

    db.session.commit()
    return cliente_to_dict(cliente)


def deletar_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        return None
    db.session.delete(cliente)
    db.session.commit()
    return {"mensagem": "Cliente deletado com sucesso"}


def buscar_clientes_por_cpf(cpf):
    clientes = Cliente.query.filter(Cliente.cpf.like(f"{cpf}%")).all()
    if not clientes:
        return []
    return [cliente_to_dict(c) for c in clientes]


def buscar_clientes_por_nome(nome):
    clientes = Cliente.query.filter(Cliente.nome.ilike(f"%{nome}%")).all()
    return jsonify([cliente_to_dict(c) for c in clientes])

def excluir_todos_clientes():
    try:
        num_rows = Cliente.query.delete()
        db.session.commit()
        return {"mensagem": f"{num_rows} clientes foram excluídos com sucesso."}
    except Exception as e:
        db.session.rollback()
        return {"erro": str(e)}


def cliente_to_dict(cliente):
    return {
        "id": cliente.id,
        "nome": cliente.nome,
        "cpf": cliente.cpf,
        "telefone": cliente.telefone,
        "email": cliente.email,
        "enderecos": [
            {
                "id": e.id,
                "rua": e.rua,
                "numero": e.numero,
                "cidade": e.cidade,
                "estado": e.estado,
                "cep": e.cep
            } for e in cliente.enderecos
        ]
    }
