from app.database import db
from app.models.usuario import Usuario
from flask_jwt_extended import create_access_token
from datetime import timedelta

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