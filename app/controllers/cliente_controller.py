from flask import jsonify
from app.database import db
from app.models.cliente import Cliente, Endereco
from app.models.contrato import Contrato
from datetime import datetime, timedelta
import os
import re
from docx import Document
from flask_jwt_extended import create_access_token

def criar_cliente(data):
    dt_nasc = datetime.strptime(data["data_nascimento"], "%Y-%m-%d").date() if data.get("data_nascimento") else None

    cliente = Cliente(
        nome=data["nome"],
        cpf=data["cpf"],
        telefone=data["telefone"],
        email=data["email"],
        data_nascimento=dt_nasc
    )
    db.session.add(cliente)
    
    for e in data.get("enderecos", []):
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
    return cliente.to_dict()

def listar_clientes():
    clientes = Cliente.query.all()
    return [c.to_dict() for c in clientes]

def obter_cliente(id):
    cliente = Cliente.query.get(id)
    return cliente.to_dict() if cliente else None

def atualizar_cliente(id, data):
    cliente = Cliente.query.get(id)
    if not cliente:
        return None

    # Atualização básica
    cliente.nome = data.get("nome", cliente.nome)
    cliente.cpf = data.get("cpf", cliente.cpf)
    cliente.telefone = data.get("telefone", cliente.telefone)
    cliente.email = data.get("email", cliente.email)
    
    if "data_nascimento" in data:
        cliente.data_nascimento = datetime.strptime(data["data_nascimento"], "%Y-%m-%d").date()

    if "enderecos" in data:
        for e in data["enderecos"]:
            end_obj = Endereco.query.filter_by(id=e.get("id"), cliente_id=cliente.id).first()
            if end_obj:
                end_obj.rua = e.get("rua", end_obj.rua)
                end_obj.numero = e.get("numero", end_obj.numero)
                end_obj.cidade = e.get("cidade", end_obj.cidade)
                end_obj.estado = e.get("estado", end_obj.estado)
                end_obj.cep = e.get("cep", end_obj.cep)

    db.session.commit()
    return cliente.to_dict()

def deletar_cliente(id):
    cliente = Cliente.query.get(id)
    if not cliente:
        return {"erro": "Cliente não encontrado."}
    
    Contrato.query.filter_by(cliente_id=id).delete()
    
    db.session.delete(cliente)
    db.session.commit()
    return {"mensagem": "Cliente e dependências excluídos com sucesso."}

def buscar_clientes_por_cpf(cpf: str):
    clientes = Cliente.query.filter(Cliente.cpf.like(f"{cpf}%")).all()
    return [c.to_dict() for c in clientes]

def buscar_clientes_por_nome(nome: str):
    clientes = Cliente.query.filter(Cliente.nome.ilike(f"%{nome}%")).all()
    return [c.to_dict() for c in clientes]

def login_cliente(data):
    cpf = data.get("cpf")
    data_nasc_str = data.get("data_nascimento")
    
    cliente = Cliente.query.filter_by(cpf=cpf).first()
    if not cliente or cliente.data_nascimento.strftime('%Y-%m-%d') != data_nasc_str:
        return {"erro": "Credenciais inválidas."}, 401
    
    access_token = create_access_token(
        identity=str(cliente.id),
        additional_claims={"nome": cliente.nome, "tipo": "cliente"},
        expires_delta=timedelta(days=30)
    )
    
    return {
        "mensagem": "Login realizado com sucesso.",
        "token": access_token,
        "cliente": cliente.to_dict()
    }, 200


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
                data_nascimento = datetime.strptime(cells[4], "%d/%m/%Y").date()
                rua = cells[5] if len(cells) > 4 else ""
                numero_end = cells[6].strip() if len(cells) > 5 else None
                cidade = cells[7] if len(cells) > 6 else ""
                estado = cells[8] if len(cells) > 7 else ""
                cep = cells[9] if len(cells) > 8 else ""

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
                    cliente.data_nascimento = data_nascimento

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
                        email=email,
                        data_nascimento=data_nascimento
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