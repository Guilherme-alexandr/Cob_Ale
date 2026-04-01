from flask import Blueprint, request, jsonify
from app.controllers.cliente_controller import (
    criar_cliente, listar_clientes, obter_cliente, 
    atualizar_cliente, deletar_cliente, buscar_clientes_por_cpf, login_cliente
)

cliente_bp = Blueprint('cliente_bp', __name__)

@cliente_bp.route('/clientes', methods=['POST'])
def rota_criar_cliente():
    data = request.get_json()
    try:
        novo_cliente = criar_cliente(data)
        return jsonify(novo_cliente), 201
    except Exception as e:
        return jsonify({"erro": str(e)}), 400

@cliente_bp.route('/clientes', methods=['GET'])
def rota_listar_clientes():
    cpf = request.args.get('cpf')
    if cpf:
        return jsonify(buscar_clientes_por_cpf(cpf)), 200
    
    return jsonify(listar_clientes()), 200

@cliente_bp.route('/clientes/<int:id>', methods=['GET'])
def rota_obter_cliente(id):
    cliente = obter_cliente(id)
    if not cliente:
        return jsonify({"erro": "Cliente não encontrado"}), 404
    return jsonify(cliente), 200

@cliente_bp.route('/clientes/<int:id>', methods=['PUT'])
def rota_atualizar_cliente(id):
    data = request.get_json()
    cliente_atualizado = atualizar_cliente(id, data)
    if not cliente_atualizado:
        return jsonify({"erro": "Cliente não encontrado"}), 404
    return jsonify(cliente_atualizado), 200

@cliente_bp.route('/clientes/<int:id>', methods=['DELETE'])
def rota_deletar_cliente(id):
    resultado = deletar_cliente(id)
    if "erro" in resultado:
        return jsonify(resultado), 404
    return jsonify(resultado), 200

@cliente_bp.route('/login', methods=['POST'])
def rota_login():
    data = request.get_json()
    resultado, status = login_cliente(data)
    return jsonify(resultado), status