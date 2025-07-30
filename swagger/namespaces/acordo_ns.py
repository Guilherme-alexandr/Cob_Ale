from flask import request
from flask_restx import Namespace, Resource, fields
from app.controllers import acordo_controller

acordo_ns = Namespace("acordos", description="Operações com acordos")

parcelamento_model = acordo_ns.model("Parcelamento", {
    "entrada": fields.Float(description="Valor da entrada"),
    "quantidade_parcelas": fields.Integer(description="Quantidade de parcelas"),
    "valor_parcela": fields.Float(description="Valor de cada parcela"),
})

acordo_model = acordo_ns.model("Acordo", {
    "id": fields.Integer(readOnly=True, description="ID do acordo"),
    "contrato_id": fields.String(required=True, description="Número do contrato (6 dígitos)", default="000001"),
    "tipo_pagamento": fields.String(required=True, description="Tipo de pagamento ('avista' ou 'parcelado')", default="parcelado"),
    "qtd_parcelas": fields.Integer(required=True, description="Quantidade de parcelas", default=4),
    "valor_total": fields.Float(readOnly=True, description="Valor total do acordo"),
    "vencimento": fields.Date(required=True, description="Data de vencimento", default="2025-08-10"),
    "status": fields.String(readOnly=True, description="Status do acordo"),
    "parcelamento": fields.Nested(parcelamento_model, description="Detalhes do parcelamento", skip_none=True)
})

@acordo_ns.route("/")
class AcordoList(Resource):
    @acordo_ns.marshal_list_with(acordo_model)
    def get(self):
        """Listar todos os acordos"""
        return acordo_controller.listar_acordos()

    @acordo_ns.expect(acordo_model, validate=True)
    def post(self):
        """Criar um novo acordo"""
        data = request.get_json()
        resultado = acordo_controller.criar_acordo(data)
        acordo = resultado["acordo"]
        # Construir a resposta com o modelo esperado
        response = acordo.copy()
        response["parcelamento"] = acordo.get("parcelamento", None)
        return response, 201


@acordo_ns.route("/<int:id>")
@acordo_ns.param("id", "ID do acordo")
class AcordoDetail(Resource):
    @acordo_ns.marshal_with(acordo_model)
    def get(self, id):
        """Obter acordo pelo ID"""
        acordo = acordo_controller.obter_acordo(id)
        if not acordo:
            acordo_ns.abort(404, "Acordo não encontrado")
        return acordo.to_dict()

    @acordo_ns.expect(acordo_model)
    @acordo_ns.marshal_with(acordo_model)
    def put(self, id):
        """Atualizar acordo"""
        data = request.get_json()
        acordo = acordo_controller.atualizar_acordo(id, data)
        if not acordo:
            acordo_ns.abort(404, "Acordo não encontrado")
        return acordo.to_dict()

    def delete(self, id):
        """Deletar acordo"""
        resultado = acordo_controller.deletar_acordo(id)
        if not resultado:
            acordo_ns.abort(404, "Acordo não encontrado")
        return {"mensagem": "Acordo deletado com sucesso"}, 204
