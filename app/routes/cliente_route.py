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
