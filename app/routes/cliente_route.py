from flask import Blueprint, request, jsonify
from app.controllers import cliente_controller

cliente_bp = Blueprint("clientes", __name__)

@cliente_bp.route("/", methods=["POST"])
def criar():
    data = request.get_json()
    cliente = cliente_controller.criar_cliente(data)
    return jsonify({
        "id": cliente.id,
        "nome": cliente.nome,
        "cpf": cliente.cpf,
        "numero": cliente.numero,
        "email": cliente.email
    }), 201

@cliente_bp.route("/", methods=["GET"])
def listar():
    clientes = cliente_controller.listar_clientes()
    return jsonify([{
        "id": c.id,
        "nome": c.nome,
        "cpf": c.cpf,
        "numero": c.numero,
        "email": c.email
    } for c in clientes])

@cliente_bp.route("/<int:id>", methods=["GET"])
def obter(id):
    cliente = cliente_controller.obter_cliente(id)
    if not cliente:
        return jsonify({"error": "Cliente não encontrado"}), 404
    return jsonify({
        "id": cliente.id,
        "nome": cliente.nome,
        "cpf": cliente.cpf,
        "numero": cliente.numero,
        "email": cliente.email
    })

@cliente_bp.route("/buscar_por_nome/<string:nome>", methods=["GET"])
def buscar_por_nome(nome):
    clientes = cliente_controller.buscar_clientes_por_nome(nome)
    if not clientes:
        return jsonify({"error": "Nenhum cliente encontrado"}), 404
    return jsonify([{
        "id": c.id,
        "nome": c.nome,
        "cpf": c.cpf,
        "numero": c.numero,
        "email": c.email
    } for c in clientes])

@cliente_bp.route("/<int:id>", methods=["PUT"])
def atualizar(id):
    data = request.get_json()
    cliente = cliente_controller.atualizar_cliente(id, data)
    if not cliente:
        return jsonify({"error": "Cliente não encontrado"}), 404
    return jsonify({
        "id": cliente.id,
        "nome": cliente.nome,
        "cpf": cliente.cpf,
        "numero": cliente.numero,
        "email": cliente.email
    })

@cliente_bp.route("/<int:id>", methods=["DELETE"])
def deletar(id):
    cliente = cliente_controller.deletar_cliente(id)
    if not cliente:
        return jsonify({"error": "Cliente não encontrado"}), 404
    return jsonify({"message": "Cliente deletado com sucesso"}), 204

@cliente_bp.route("/buscar_por_cpf/<string:cpf>", methods=["GET"])
def buscar_por_cpf(cpf):
    cliente = cliente_controller.buscar_cliente_por_cpf(cpf)
    if not cliente:
        return jsonify({"error": "Cliente não encontrado"}), 404
    return jsonify({
        "id": cliente.id,
        "nome": cliente.nome,
        "cpf": cliente.cpf,
        "numero": cliente.numero,
        "email": cliente.email
    })