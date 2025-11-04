from flask import Blueprint, request, jsonify
from app.controllers import usuario_controller
from importadores.role_required import role_required

usuario_bp = Blueprint("usuarios", __name__)

@usuario_bp.route("/criar", methods=["POST"])
def criar_usuario():
    data = request.json
    usuario = usuario_controller.criar_usuario(data)
    return jsonify(usuario), 201


@usuario_bp.route("/listar", methods=["GET"])
def listar_usuarios():
    usuarios = usuario_controller.listar_usuarios()
    return jsonify(usuarios), 200

@usuario_bp.route("/<int:id>", methods=["GET"])
def obter_usuario(id):
    usuario = usuario_controller.obter_usuario(id)
    if not usuario:
        return jsonify({"mensagem": "Usuário não encontrado."}), 404
    return jsonify(usuario), 200


@usuario_bp.route("atualizar/<int:id>", methods=["PUT"])
def atualizar_usuario(id):
    data = request.json
    usuario = usuario_controller.atualizar_usuario(id, data)
    if not usuario:
        return jsonify({"mensagem": "Usuário não encontrado."}), 404
    return jsonify(usuario), 200

@usuario_bp.route("/deletar/<int:id>", methods=["DELETE"])
def deletar_usuario(id):
    resultado = usuario_controller.deletar_usuario(id)
    if not resultado:
        return jsonify({"mensagem": "Usuário não encontrado."}), 404
    return jsonify({"mensagem": "Usuário deletado com sucesso"}), 200

@usuario_bp.route("/buscar_por_login", methods=["GET"])
def buscar_usuario_por_login():
    login = request.args.get("login")
    usuario = usuario_controller.buscar_usuario_por_login(login)
    if not usuario:
        return jsonify({"mensagem": "Usuário não encontrado."}), 404
    return jsonify(usuario), 200


@usuario_bp.route("/login", methods=["POST"])
def login_usuario():
    data = request.get_json()
    resposta, status = usuario_controller.login_usuario(data)
    return jsonify(resposta), status
