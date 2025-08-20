from flask import Blueprint, request, jsonify, make_response, render_template, current_app
from flask_cors import cross_origin
from functools import wraps
from weasyprint import HTML
from app.controllers import acordo_controller
from app.models.acordo import Acordo, Boleto, db


# Decorator para tratar exceções de forma padronizada
def safe_route(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"erro": str(e)}), 500
    return wrapper


acordo_bp = Blueprint("acordos", __name__)


# ------------------- CRUD Acordos -------------------

@acordo_bp.route("/", methods=["POST"])
@safe_route
def criar():
    data = request.get_json()
    resultado = acordo_controller.criar_acordo(data)
    return jsonify(resultado), 201


@acordo_bp.route("/", methods=["GET"])
@safe_route
def listar():
    acordos = acordo_controller.listar_acordos()
    return jsonify([acordo.to_dict() for acordo in acordos]), 200


@acordo_bp.route("/<int:id>", methods=["GET"])
@safe_route
def obter(id):
    acordo = acordo_controller.obter_acordo(id)
    if not acordo:
        return jsonify({"erro": "Acordo não encontrado"}), 404
    return jsonify(acordo.to_dict()), 200


@acordo_bp.route("/buscar_por_contrato/<string:numero_contrato>", methods=["GET"])
@safe_route
def obter_por_contrato(numero_contrato):
    acordo = acordo_controller.obter_acordo_por_contrato(numero_contrato)
    if not acordo:
        return jsonify({"erro": "Acordo não encontrado"}), 404
    return jsonify(acordo.to_dict()), 200


@acordo_bp.route("/<int:id>", methods=["PUT"])
@safe_route
def atualizar(id):
    data = request.get_json()
    resultado = acordo_controller.atualizar_acordo(id, data)
    if not resultado:
        return jsonify({"erro": "Acordo não encontrado"}), 404
    return jsonify(resultado.to_dict()), 200


@acordo_bp.route("/<int:id>", methods=["DELETE"])
@safe_route
def deletar(id):
    resultado = acordo_controller.deletar_acordo(id)
    if not resultado:
        return jsonify({"erro": "Acordo não encontrado"}), 404
    return jsonify({"mensagem": "Acordo deletado com sucesso"}), 200


# ------------------- Simulação -------------------

@acordo_bp.route("/simular", methods=["POST"])
@cross_origin()
@safe_route
def simular_acordo():
    payload = request.get_json()
    resultado = acordo_controller.simular_acordo(payload)
    return jsonify(resultado), 200


# ------------------- Boletos -------------------

@acordo_bp.route("/info_boleto/<int:acordo_id>", methods=["GET"])
@safe_route
def info_boleto(acordo_id):
    boleto_info, status = acordo_controller.info_boleto(acordo_id)
    return jsonify(boleto_info), status


@acordo_bp.route("/gerar_boleto/<int:acordo_id>", methods=["GET"])
@safe_route
def gerar_boleto(acordo_id):
    pdf, nome_arquivo = acordo_controller.gerar_boleto(acordo_id)
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename={nome_arquivo}"
    return response


@acordo_bp.route("/enviar_boleto", methods=["POST"])
@safe_route
def enviar_boleto():
    """
    Envia um boleto. 
    JSON esperado:
    {
        "acordo_id": <id opcional>,
        "boleto_id": <id obrigatório>
    }
    """
    data = request.get_json()
    acordo_id = data.get("acordo_id")
    boleto_id = data.get("boleto_id")

    if not boleto_id:
        return jsonify({"erro": "boleto_id é obrigatório"}), 400

    resultado = acordo_controller.enviar_boleto(acordo_id=acordo_id, boleto_id=boleto_id)
    return jsonify(resultado), 200


@acordo_bp.route("/boletos/<int:acordo_id>", methods=["GET"])
@safe_route
def listar_boletos(acordo_id):
    boletos = acordo_controller.listar_boletos_por_pasta(acordo_id)
    return jsonify({
        "acordo_id": acordo_id,
        "boletos": boletos
    })


@acordo_bp.route("/boletos/deletar", methods=["DELETE"])
@safe_route
def deletar_boletos():
    return acordo_controller.deletar_todos_boletos()
