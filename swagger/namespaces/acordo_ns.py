from flask import request, make_response, current_app
from flask_restx import Namespace, Resource, fields
from app.controllers import acordo_controller
from app.controllers.acordo_controller import simular_acordo
from weasyprint import HTML

acordo_ns = Namespace("acordos", description="Operações com acordos")

parcelamento_model = acordo_ns.model("Parcelamento", {
    "entrada": fields.Float(description="Valor da entrada"),
    "quantidade_parcelas": fields.Integer(description="Quantidade de parcelas"),
    "valor_parcela": fields.Float(description="Valor de cada parcela"),
    "valor_total_parcelas": fields.Float(description="Valor total das parcelas")  # incluímos total
})

acordo_model = acordo_ns.model("Acordo", {
    "id": fields.Integer(readOnly=True, description="ID do acordo"),
    "contrato_id": fields.String(required=True, description="Número do contrato (6 dígitos)", default="000001"),
    "tipo_pagamento": fields.String(required=True, description="Tipo de pagamento ('avista' ou 'parcelado')", default="parcelado"),
    "qtd_parcelas": fields.Integer(required=True, description="Quantidade de parcelas", default=4),
    "valor_total": fields.Float(readOnly=True, description="Valor total do acordo"),
    "desconto": fields.Float(readOnly=True, description="Valor do desconto aplicado no acordo"),
    "juros": fields.Float(readOnly=True, description="Valor do juros aplicado no acordo"),
    "vencimento": fields.Date(required=True, description="Data de vencimento", default="2025-08-10"),
    "status": fields.String(readOnly=True, description="Status do acordo"),
    "parcelamento": fields.Nested(parcelamento_model, description="Detalhes do parcelamento", skip_none=True)
})


boleto_model = acordo_ns.model('Boleto', {
    'id': fields.Integer(readonly=True, description='ID do boleto'),
    'acordo_id': fields.Integer(required=True, description='ID do acordo vinculado'),
    'caminho_pdf': fields.String(required=True, description='Caminho do arquivo PDF do boleto'),
    'criado_em': fields.DateTime(description='Data de criação do boleto'),
    'enviado': fields.Boolean(description='Indica se o boleto foi enviado'),
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

@acordo_ns.route("/buscar_por_contrato/<string:numero_contrato>")
@acordo_ns.param("numero_contrato", "Número do contrato")
class AcordoByContrato(Resource):
    def get(self, numero_contrato):
        """Obter acordo pelo número do contrato"""
        acordo = acordo_controller.obter_acordo_por_contrato(numero_contrato)
        if not acordo:
            return {"erro": "Acordo não encontrado"}, 404
        return acordo.to_dict(), 200

@acordo_ns.route("/simular")
class AcordoSimulacao(Resource):
    def post(self):
        """Simular acordo"""
        payload = request.get_json()
        try:
            resultado_simulacao = simular_acordo(payload)
            return resultado_simulacao, 200
        except ValueError as e:
            return {"erro": str(e)}, 400
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {"erro": "Erro interno ao processar a simulação"}, 500
        
@acordo_ns.route("/info_boleto/<int:acordo_id>")
@acordo_ns.param("acordo_id", "ID do acordo para consulta das informações do boleto", _in="path", required=True)
class InfoBoleto(Resource):
    @acordo_ns.response(200, "Informações do boleto retornadas com sucesso")
    @acordo_ns.response(404, "Acordo, contrato ou cliente não encontrado")
    @acordo_ns.response(500, "Erro interno ao buscar as informações do boleto")
    @acordo_ns.marshal_with(boleto_model)
    def get(self, acordo_id):
        """
        Retorna as informações necessárias para gerar o boleto do acordo especificado.

        As informações incluem:
        - Dados do cliente e endereço
        - Código de barras e linha digitável
        - Valores de documento, juros e desconto
        - Datas de vencimento, processamento e emissão
        - Informações adicionais para montagem do boleto

        Essa rota **não gera o PDF**, apenas retorna os dados em JSON.

        **Formato do retorno:** conforme `boleto_model`
        """
        try:
            boleto_info, status = acordo_controller.info_boleto(acordo_id)
            if status != 200:
                acordo_ns.abort(status, boleto_info.get("erro", "Erro ao obter boleto"))
            return boleto_info
        except Exception as e:
            current_app.logger.exception("Erro ao obter informações do boleto")
            acordo_ns.abort(500, str(e))



@acordo_ns.route("/gerar_boleto/<int:acordo_id>")
@acordo_ns.param("acordo_id", "ID do acordo para o qual o boleto será gerado", _in="path", required=True)
class GerarBoleto(Resource):
    @acordo_ns.response(200, "Boleto gerado com sucesso (PDF)")
    @acordo_ns.response(404, "Acordo não encontrado ou dados do boleto indisponíveis")
    @acordo_ns.response(500, "Erro interno ao gerar o boleto")
    @acordo_ns.produces(["application/pdf"])
    def get(self, acordo_id):
        """
        Gera e retorna o boleto em formato PDF para o acordo especificado.

        O boleto é montado a partir de um template `.docx`, convertido para PDF e enviado inline.
        
        **Cabeçalhos de resposta adicionais:**
        - `X-Boleto-Id`: ID do boleto gerado no banco de dados.
        """
        try:
            pdf, nome_arquivo, boleto_id = acordo_controller.gerar_boleto_novo(acordo_id)
            response = make_response(pdf)
            response.headers["Content-Type"] = "application/pdf"
            response.headers["Content-Disposition"] = f"inline; filename={nome_arquivo}"
            response.headers["X-Boleto-Id"] = str(boleto_id)
            return response
        except Exception as e:
            current_app.logger.exception("Erro ao gerar boleto")
            return {"erro": str(e)}, 500


@acordo_ns.route("/enviar_boleto/<int:boleto_id>")
@acordo_ns.param("boleto_id", "ID do boleto")
class EnviarBoleto(Resource):
    def post(self, boleto_id):
        """Enviar boleto por e-mail ou outro canal"""
        try:
            resultado = acordo_controller.enviar_boleto(boleto_id)
            return resultado, 200
        except ValueError as e:
            return {"erro": str(e)}, 404
        except Exception as e:
            return {"erro": str(e)}, 400

