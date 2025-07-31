from flask import request
from flask_restx import Namespace, Resource, fields
from app.controllers import contrato_controller

contrato_ns = Namespace("contratos", description="Operações com contratos")

contrato_model = contrato_ns.model("Contrato", {
    "numero_contrato": fields.String(readOnly=True, description="Número do contrato (6 dígitos)"),
    "cliente_id": fields.Integer(required=True, description="ID do cliente", default=1),
    "vencimento": fields.Date(required=True, description="Data de vencimento", default="2025-05-30"),
    "valor_total": fields.Float(required=True, description="Valor total do contrato", default=450.75),
    "filial": fields.String(required=True, description="Filial ou loja do débito", default="Loja Central")
})

@contrato_ns.route("/")
class ContratoList(Resource):
    @contrato_ns.marshal_list_with(contrato_model)
    def get(self):
        """Listar todos os contratos"""
        return contrato_controller.listar_contratos()

    @contrato_ns.expect(contrato_model)
    @contrato_ns.marshal_with(contrato_model, code=201)
    def post(self):
        """Criar um novo contrato"""
        data = request.get_json()
        return contrato_controller.criar_contrato(data), 201


@contrato_ns.route("/<string:numero_contrato>")
@contrato_ns.param("numero_contrato", "Número do contrato (6 dígitos)")
class ContratoDetail(Resource):
    @contrato_ns.marshal_with(contrato_model)
    def get(self, numero_contrato):
        """Obter contrato pelo número"""
        contrato = contrato_controller.obter_contrato(numero_contrato)
        if not contrato:
            contrato_ns.abort(404, "Contrato não encontrado")
        return contrato

    @contrato_ns.expect(contrato_model)
    @contrato_ns.marshal_with(contrato_model)
    def put(self, numero_contrato):
        """Atualizar contrato"""
        data = request.get_json()
        contrato = contrato_controller.atualizar_contrato(numero_contrato, data)
        if not contrato:
            contrato_ns.abort(404, "Contrato não encontrado")
        return contrato

    def delete(self, numero_contrato):
        """Deletar contrato"""
        contrato = contrato_controller.deletar_contrato(numero_contrato)
        if not contrato:
            contrato_ns.abort(404, "Contrato não encontrado")
        return {"mensagem": "Contrato deletado com sucesso"}, 204


@contrato_ns.route("/buscar_por_cliente/<int:cliente_id>")
@contrato_ns.param("cliente_id", "ID do cliente")
class ContratoPorCliente(Resource):
    @contrato_ns.marshal_list_with(contrato_model)
    def get(self, cliente_id):
        """Buscar contratos pelo ID do cliente"""
        contratos = contrato_controller.buscar_contratos_por_cliente(cliente_id)
        if not contratos:
            contrato_ns.abort(404, "Nenhum contrato encontrado para este cliente")
        return contratos
