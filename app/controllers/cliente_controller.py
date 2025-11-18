from flask import jsonify
from app.database import db
from app.models.cliente import Cliente, Endereco
from app.models.contrato import Contrato
import os
from docx import Document
import re


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
        return {"erro": "Cliente não encontrado."}
    
    contratos = Contrato.query.filter_by(cliente_id=id).all()
    if contratos:
        for contrato in contratos:
            db.session.delete(contrato)
        
        db.session.commit()
    db.session.delete(cliente)
    db.session.commit()
    return {"mensagem": "Cliente e seus contratos excluídos com sucesso."}


def buscar_clientes_por_cpf(cpf: str):
    if not cpf:
        raise ValueError("CPF não pode ser vazio.")
    clientes = Cliente.query.filter(Cliente.cpf.like(f"{cpf}%")).all()
    return [cliente_to_dict(c) for c in clientes]

def buscar_clientes_por_nome(nome: str):
    if not nome:
        raise ValueError("Nome não pode ser vazio.")
    clientes = Cliente.query.filter(Cliente.nome.ilike(f"%{nome}%")).all()
    return [cliente_to_dict(c) for c in clientes]

def buscar_clientes_por_telefone(telefone):
    cliente = Cliente.query.filter_by(telefone=telefone).first()
    if not cliente:
        return []
    return [cliente_to_dict(cliente)]

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


def validar_telefone(telefone):
    return bool(re.match(r'^\d{10,11}$', telefone))

def importar_clientes_docx(caminho_arquivo, app):
    with app.app_context():
        doc = Document(caminho_arquivo)
        clientes_importados = 0
        clientes_atualizados = 0

        for tabela in doc.tables:
            for i, linha in enumerate(tabela.rows):
                if i == 0:
                    continue

                cells = [c.text.strip() for c in linha.cells]

                if len(cells) < 4:
                    print(f"Linha {i+1} inválida (faltando colunas). Ignorada.")
                    continue

                nome = cells[0]
                cpf = cells[1]
                telefone = cells[2]
                email = cells[3]
                rua = cells[4] if len(cells) > 4 else ""
                numero_end = cells[5].strip() if len(cells) > 5 else None
                cidade = cells[6] if len(cells) > 6 else ""
                estado = cells[7] if len(cells) > 7 else ""
                cep = cells[8] if len(cells) > 8 else ""

                if not nome or not cpf:
                    print(f"Registro inválido na linha {i + 1}")
                    continue

                if not validar_telefone(telefone):
                    print(f"Telefone inválido na linha {i + 1}. Ignorado.")
                    continue

                cliente = Cliente.query.filter_by(cpf=cpf).first()
                if cliente is not None:
                    cliente.nome = nome
                    cliente.telefone = telefone
                    cliente.email = email

                    if rua or numero_end or cidade or estado or cep:
                        Endereco.query.filter_by(cliente_id=cliente.id).delete()
                        endereco = Endereco(
                            rua=rua,
                            numero=int(numero_end) if numero_end and numero_end.isdigit() else None,
                            cidade=cidade,
                            estado=estado,
                            cep=cep,
                            cliente_id=cliente.id
                        )
                        db.session.add(endereco)

                    clientes_atualizados += 1
                    print(f"Cliente com CPF {cpf} atualizado.")
                else:
                    cliente = Cliente(
                        nome=nome,
                        cpf=cpf,
                        telefone=telefone,
                        email=email
                    )
                    db.session.add(cliente)
                    db.session.flush()

                    if rua or numero_end or cidade or estado or cep:
                        endereco = Endereco(
                            rua=rua,
                            numero=int(numero_end) if numero_end and numero_end.isdigit() else None,
                            cidade=cidade,
                            estado=estado,
                            cep=cep,
                            cliente_id=cliente.id
                        )
                        db.session.add(endereco)

                    clientes_importados += 1
                    print(f"Cliente com CPF {cpf} adicionado.")

        db.session.commit()
        print(f"Importação concluída: {clientes_importados} clientes adicionados, {clientes_atualizados} clientes atualizados.")