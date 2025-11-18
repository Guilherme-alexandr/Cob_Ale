from flask import Blueprint, request, jsonify
from app.controllers import contrato_controller

contrato_bp = Blueprint("contratos", __name__)

@contrato_bp.route("/", methods=["POST"])
def criar(): 
    try:
        data = request.get_json()
        contrato = contrato_controller.criar_contrato(data)
        return jsonify({ 
            "numero_contrato": contrato.numero_contrato,
            "cliente_id": contrato.cliente_id,
            "vencimento": contrato.vencimento.strftime("%Y-%m-%d"),
            "valor_total": contrato.valor_total,
            "filial": contrato.filial
        }), 201
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": "Erro ao criar contrato."}), 500

@contrato_bp.route("/", methods=["GET"])
def listar():
    contratos = contrato_controller.listar_contratos()
    return jsonify([{
        "numero_contrato": c.numero_contrato,
        "cliente_id": c.cliente_id,
        "vencimento": c.vencimento.strftime("%Y-%m-%d"),
        "valor_total": c.valor_total,
        "filial": c.filial
    } for c in contratos])

@contrato_bp.route("/<string:numero_contrato>", methods=["GET"])
def obter(numero_contrato):
    contrato = contrato_controller.obter_contrato(numero_contrato)
    if not contrato:
        return jsonify({"error": "Contrato não encontrado"}), 404
    return jsonify({
        "numero_contrato": contrato.numero_contrato,
        "cliente_id": contrato.cliente_id,
        "vencimento": contrato.vencimento.strftime("%Y-%m-%d"),
        "valor_total": contrato.valor_total,
        "filial": contrato.filial
    })

@contrato_bp.route("/<string:numero_contrato>", methods=["PUT"])
def atualizar(numero_contrato):
    data = request.get_json()
    contrato = contrato_controller.atualizar_contrato(numero_contrato, data)
    if not contrato:
        return jsonify({"error": "Contrato não encontrado"}), 404
    return jsonify({
        "numero_contrato": contrato.numero_contrato,
        "cliente_id": contrato.cliente_id,
        "vencimento": contrato.vencimento.strftime("%Y-%m-%d"),
        "valor_total": contrato.valor_total,
        "filial": contrato.filial
    })

@contrato_bp.route("/<string:numero_contrato>", methods=["DELETE"])
def deletar(numero_contrato):
    contrato = contrato_controller.deletar_contrato(numero_contrato)
    if not contrato:
        return jsonify({"error": "Contrato não encontrado"}), 404
    return jsonify({"message": "Contrato deletado com sucesso"}), 204

@contrato_bp.route("/buscar_por_cliente/<int:cliente_id>", methods=["GET"])
def buscar_por_cliente(cliente_id):
    contratos = contrato_controller.buscar_contratos_por_cliente(cliente_id)
    if not contratos:
        return jsonify({"error": "Nenhum contrato encontrado para este cliente"}), 404
    return jsonify([{
        "numero_contrato": c.numero_contrato,
        "cliente_id": c.cliente_id,
        "vencimento": c.vencimento.strftime("%Y-%m-%d"),
        "valor_total": c.valor_total,
        "filial": c.filial
    } for c in contratos])

@contrato_bp.route("/buscar_por_filial/<string:filial>", methods=["GET"])
def buscar_por_filial(filial):
    try:
        contratos = contrato_controller.buscar_contratos_por_filial(filial)
        if not contratos:
            return jsonify({"error": "Nenhum contrato encontrado para esta filial"}), 404

        return jsonify([
            {
                "numero_contrato": c.numero_contrato,
                "cliente_id": c.cliente_id,
                "vencimento": c.vencimento.strftime("%Y-%m-%d"),
                "valor_total": c.valor_total,
                "filial": c.filial
            } for c in contratos
        ])
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        print("Erro ao buscar contratos por filial:", e)
        return jsonify({"erro": "Erro interno no servidor"}), 500
    
@contrato_bp.route("/buscar_por_valor", methods=["GET"])
def buscar_por_valor():
    try:
        valor_minimo = request.args.get("min")
        valor_maximo = request.args.get("max")

        contratos = contrato_controller.buscar_contratos_por_valor(valor_minimo, valor_maximo)
        if not contratos:
            return jsonify({"error": "Nenhum contrato encontrado dentro do intervalo especificado"}), 404

        return jsonify(contratos)
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        print("Erro ao buscar contratos por valor:", e)
        return jsonify({"erro": "Erro interno no servidor"}), 500


@contrato_bp.route('/buscar_por_vencimento', methods=['GET'])
def contratos_por_vencimento_route():
    data_inicio = request.args.get('inicio')
    data_fim = request.args.get('fim')

    try:
        contratos = contrato_controller.buscar_contratos_por_vencimento(data_inicio, data_fim)
        return jsonify(contratos), 200
    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        print("Erro:", e)
        return jsonify({"erro": "Erro interno no servidor"}), 500

    

@contrato_bp.route("/resetar", methods=["POST"])
def resetar():
    try:
        contrato_controller.resetar_contratos()
        return jsonify({"message": "Contratos resetados com sucesso"}), 200
    except Exception as e:
        return jsonify({"error": "Erro ao resetar contratos"}), 500
