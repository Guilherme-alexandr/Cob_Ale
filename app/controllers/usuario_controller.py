from app.database import db
from app.models.usuario import Usuario
from flask_jwt_extended import create_access_token
from datetime import timedelta
import os
from docx import Document
from werkzeug.security import generate_password_hash

def criar_usuario(data):
    usuario = Usuario(
        nome=data["nome"],
        login=data["login"],
        cargo=data["cargo"]
    )
    usuario.set_senha(data["senha"])
    db.session.add(usuario)
    db.session.commit()
    return usuario_to_dict(usuario)

def listar_usuarios():
    usuarios = Usuario.query.all()
    return [usuario_to_dict(u) for u in usuarios]

def obter_usuario(id):
    usuario = Usuario.query.get(id)
    if not usuario:
        return None
    return usuario_to_dict(usuario)

def atualizar_usuario(id, data):
    usuario = Usuario.query.get(id)
    if not usuario:
        return None

    usuario.nome = data.get("nome", usuario.nome)
    usuario.login = data.get("login", usuario.login)
    usuario.cargo = data.get("cargo", usuario.cargo)
    if "senha" in data and data["senha"]:
        usuario.set_senha(data["senha"])

    db.session.commit()
    return usuario.to_dict()

def deletar_usuario(id):
    usuario = Usuario.query.get(id)
    if not usuario:
        return None
    db.session.delete(usuario)
    db.session.commit()
    return {"mensagem": "Usuário deletado com sucesso."}

def buscar_usuario_por_login(login):
    usuario = Usuario.query.filter_by(login=login).first()
    if not usuario:
        return None
    return usuario_to_dict(usuario)


## LOGIN ##

def login_usuario(data):
    login = data.get("login")
    senha = data.get("senha")
    
    if not login or not senha:
        return {"erro": "Login e senha são obrigatórios."}, 400
    
    usuario = Usuario.query.filter_by(login=login).first()
    if not usuario or not usuario.verificar_senha(senha):
        return {"erro": "Credenciais inválidas."}, 401
    
    access_token = create_access_token(
        identity=str(usuario.id),
        additional_claims={
            "nome": usuario.nome,
            "login": usuario.login,
            "cargo": usuario.cargo
        },
        expires_delta=timedelta(days=1)
    )


    return {
        "mensagem": "Login realizado com sucesso.",
        "token": access_token,
        "usuario": usuario_to_dict(usuario)
    }, 200

def usuario_to_dict(usuario):
        return {
            "id": usuario.id,
            "nome": usuario.nome,
            "login": usuario.login,
            "cargo": usuario.cargo
        }


def importar_usuarios_docx(caminho_arquivo, app):
    with app.app_context():
        doc = Document(caminho_arquivo)
        usuarios_importados = 0
        erro_ocorrido = False

        for tabela in doc.tables:
            for i, linha in enumerate(tabela.rows):
                if i == 0:
                    continue
                
                try:
                    nome = linha.cells[0].text.strip()
                    login = linha.cells[1].text.strip()
                    senha = linha.cells[2].text.strip()
                    cargo = linha.cells[3].text.strip()

                    usuario_existente = Usuario.query.filter_by(login=login).first()
                    if usuario_existente:
                        print(f"Login duplicado encontrado para {login}. Usuário não será inserido.")
                        continue

                    usuario = Usuario(
                        nome=nome,
                        login=login,
                        cargo=cargo
                    )
                    usuario.set_senha(senha)

                    db.session.add(usuario)
                    usuarios_importados += 1
                except Exception as e:
                    erro_ocorrido = True
                    print(f"Erro ao processar a linha {i + 1}: {e}")

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao realizar commit: {e}")
            erro_ocorrido = True

        if erro_ocorrido:
            print(f"Importação concluída com {usuarios_importados} usuários, mas houve erros durante o processo.")
        else:
            print(f"Importação concluída: {usuarios_importados} usuários adicionados.")