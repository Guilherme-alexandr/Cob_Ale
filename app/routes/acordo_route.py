from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from app.controllers import acordo_controller


acordo_bp = Blueprint('acordos', __name__)

@acordo_bp.route("/", methods=["POST"])
def criar():
    try:
        data = request.get_json()
        resultado = acordo_controller.criar_acordo(data)
        return jsonify(resultado), 201
    except Exception as e:
        import traceback 
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500

@acordo_bp.route("/", methods=["GET"])
def listar():
    try:
        acordos = acordo_controller.listar_acordos()
        return jsonify([acordo.to_dict() for acordo in acordos]), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500

@acordo_bp.route("/<int:id>", methods=["GET"])
def obter(id):
    try:
        acordo = acordo_controller.obter_acordo(id)
        if not acordo:
            return jsonify({"erro": "Acordo não encontrado"}), 404
        return jsonify(acordo.to_dict()), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500

@acordo_bp.route("/buscar_por_contrato/<string:numero_contrato>", methods=["GET"])
def obter_por_contrato(numero_contrato):
    try:
        acordo = acordo_controller.obter_acordo_por_contrato(numero_contrato)
        if not acordo:
            return jsonify({"erro": "Acordo não encontrado"}), 404
        return jsonify(acordo.to_dict()), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500

@acordo_bp.route("/<int:id>", methods=["PUT"])
def atualizar(id):
    try:
        data = request.get_json()
        resultado = acordo_controller.atualizar_acordo(id, data)
        if not resultado:
            return jsonify({"erro": "Acordo não encontrado"}), 404
        return jsonify(resultado.to_dict()), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500

@acordo_bp.route("/<int:id>", methods=["DELETE"])
def deletar(id):
    try:
        resultado = acordo_controller.deletar_acordo(id)
        if not resultado:
            return jsonify({"erro": "Acordo não encontrado"}), 404
        return jsonify({"mensagem": "Acordo deletado com sucesso"}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 500
    
@acordo_bp.route('/simular', methods=['POST'])
@cross_origin()
def simular_acordo():
    try:
        payload = request.get_json()
        resultado = acordo_controller.simular_acordo(payload)
        return jsonify(resultado), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"erro": str(e)}), 400

