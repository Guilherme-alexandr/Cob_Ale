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
    try:
        clientes = cliente_controller.buscar_clientes_por_cpf(cpf)
        if not clientes:
            return jsonify({"error": "Nenhum cliente encontrado com este CPF"}), 404
        return jsonify(clientes)
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        print("Erro ao buscar clientes por CPF:", e)
        return jsonify({"erro": "Erro interno no servidor"}), 500

@cliente_bp.route("/buscar_por_nome/<string:nome>", methods=["GET"])
def buscar_por_nome(nome):
    try:
        clientes = cliente_controller.buscar_clientes_por_nome(nome)
        if not clientes:
            return jsonify({"error": "Nenhum cliente encontrado com este nome"}), 404
        return jsonify(clientes)
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        print("Erro ao buscar clientes por nome:", e)
        return jsonify({"erro": "Erro interno no servidor"}), 500
    
@cliente_bp.route("/buscar_por_telefone/<string:telefone>", methods=["GET"])
def buscar_por_telefone(telefone):
    try:
        clientes = cliente_controller.buscar_clientes_por_telefone(telefone)
        if not clientes:
            return jsonify({"error": "Nenhum cliente encontrado com esse telefone"}), 404
        return jsonify(clientes)
    except Exception as e:
        print("Erro ao buscar cliente por telefone:", e)
        return jsonify({"erro": "Erro interno no servidor"}), 500


@cliente_bp.route("/todos", methods=["DELETE"])
def deletar_todos():
    return jsonify(cliente_controller.excluir_todos_clientes())

