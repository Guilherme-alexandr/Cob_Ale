from flask import Blueprint, request, jsonify, make_response
from flask_cors import cross_origin
from functools import wraps
from app.controllers import acordo_controller
import traceback


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
    pdf, nome_arquivo, boleto_id = acordo_controller.gerar_boleto(acordo_id)
    response = make_response(pdf)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename={nome_arquivo}"
    response.headers["X-Boleto-Id"] = str(boleto_id)
    return response


@acordo_bp.route("/enviar_boleto/<int:acordo_id>", methods=["POST"])
@safe_route
def enviar_boleto(acordo_id):
    try:
        resultado = acordo_controller.enviar_boleto(acordo_id)
        return jsonify(resultado), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 400


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

@acordo_bp.route("/codigobr/<int:acordo_id>", methods=["GET"])
def gerar_code(acordo_id):
    codigo_barras, linha_digitavel = acordo_controller.gerar_linha_digitavel(acordo_id)
    return jsonify({
        "codigo_barras": codigo_barras,
        "linha_digitavel": linha_digitavel
    }), 200

