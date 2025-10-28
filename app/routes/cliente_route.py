from flask import Blueprint, request, jsonify
from app.controllers import cliente_controller

cliente_bp = Blueprint("clientes", __name__)

@cliente_bp.route("/", methods=["POST"])
def criar():
    data = request.get_json()
    return cliente_controller.criar_cliente(data)

@cliente_bp.route("/", methods=["GET"])
def listar():
    return cliente_controller.listar_clientes()

@cliente_bp.route("/<int:id>", methods=["GET"])
def obter(id):
    return cliente_controller.obter_cliente(id)

@cliente_bp.route("/<int:id>", methods=["PUT"])
def atualizar(id):
    data = request.get_json()
    return cliente_controller.atualizar_cliente(id, data)

@cliente_bp.route("/<int:id>", methods=["DELETE"])
def deletar(id):
    return cliente_controller.deletar_cliente(id)

@cliente_bp.route("/buscar_por_cpf/<string:cpf>", methods=["GET"])
def buscar_por_cpf(cpf):
    return cliente_controller.buscar_clientes_por_cpf(cpf)

@cliente_bp.route("/buscar_por_nome/<string:nome>", methods=["GET"])
def buscar_por_nome(nome):
    return cliente_controller.buscar_clientes_por_nome(nome)

@cliente_bp.route("/todos", methods=["DELETE"])
def deletar_todos():
    return jsonify(cliente_controller.excluir_todos_clientes())

