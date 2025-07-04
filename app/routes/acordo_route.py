from flask import Blueprint, request, jsonify
from app.controllers import acordo_controller

acordo_bp = Blueprint('acordos', __name__)

@acordo_bp.route("/", methods=["POST"])
def criar():
    try:
        data = request.get_json()
        acordo = acordo_controller.criar(data)

        return jsonify({
            "id": acordo.id,
            "contrato_id": acordo.contrato_id,
            "tipo_pagamento": acordo.tipo_pagamento,
            "qtd_parcelas": acordo.qtd_parcelas,
            "valor_total": acordo.valor_total,
            "vencimento": acordo.vencimento.strftime("%Y-%m-%d"),
            "status": acordo.status
        }), 201

    except ValueError as e:
        return jsonify({"erro": str(e)}), 400
    except Exception as e:
        return jsonify({"erro": "Erro interno ao criar acordo."}), 500
    
@acordo_bp.route("/", methods=["GET"])
def listar():
    acordos = acordo_controller.listar()
    return jsonify([{
        "id": a.id,
        "contrato_id": a.contrato_id,
        "tipo_pagamento": a.tipo_pagamento,
        "qtd_parcelas": a.qtd_parcelas,
        "valor_total": a.valor_total,
        "vencimento": a.vencimento.strftime("%Y-%m-%d"),
        "status": a.status
    } for a in acordos])

@acordo_bp.route("/<int:id>", methods=["GET"])
def obter_acordo(id):
    acordo = acordo_controller.obter_acordo(id)
    if not acordo:
        return jsonify({"error": "Acordo não encontrado"}), 404
    return jsonify({
        "id": acordo.id,
        "contrato_id": acordo.contrato_id,
        "tipo_pagamento": acordo.tipo_pagamento,
        "qtd_parcelas": acordo.qtd_parcelas,
        "valor_total": acordo.valor_total,
        "vencimento": acordo.vencimento.strftime("%Y-%m-%d"),
        "status": acordo.status
    })

@acordo_bp.route("/<int:id>", methods=["PUT"])
def atualizar_acordo(id):
    data = request.get_json()
    acordo = acordo_controller.atualizar_acordo(id, data)
    if not acordo:
        return jsonify({"error": "Acordo não encontrado"}), 404
    return jsonify({
        "id": acordo.id,
        "contrato_id": acordo.contrato_id,
        "tipo_pagamento": acordo.tipo_pagamento,
        "qtd_parcelas": acordo.qtd_parcelas,
        "valor_total": acordo.valor_total,
        "vencimento": acordo.vencimento.strftime("%Y-%m-%d"),
        "status": acordo.status
    })

@acordo_bp.route("/<int:id>", methods=["DELETE"])
def deletar_acordo(id):
    acordo = acordo_controller.deletar_acordo(id)
    if not acordo:
        return jsonify({"error": "Acordo não encontrado"}), 404
    return jsonify({"message": "Acordo deletado com sucesso"}), 200
