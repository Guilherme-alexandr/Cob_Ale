from flask import request, jsonify
from flask_restx import Namespace, Resource, fields
from app.controllers import cliente_controller
from app.models.cliente import Cliente

cliente_ns = Namespace("clientes", description="Operações com clientes")

endereco_model = cliente_ns.model("Endereco", {
    "id": fields.Integer(readOnly=True, description="ID do endereço"),
    "rua": fields.String(required=True, description="Rua do endereço", default="Rua das Flores"),
    "numero": fields.String(required=True, description="Número do endereço", default="123"),
    "cidade": fields.String(required=True, description="Cidade do endereço", default="São Paulo"),
    "estado": fields.String(required=True, description="Estado do endereço (UF)", default="SP"),
    "cep": fields.String(required=True, description="CEP do endereço", default="01001000")
})

cliente_model = cliente_ns.model("Cliente", {
    "id": fields.Integer(readOnly=True),
    "nome": fields.String(required=True, description="Nome do cliente", default="João da Silva"),
    "cpf": fields.String(required=True, description="CPF do cliente", default="12345678901"),
    "telefone": fields.String(required=True, description="Número de telefone do cliente", default="11999998888"),
    "email": fields.String(required=True, description="Email do cliente", default="joao.silva@email.com"),
    "enderecos": fields.List(fields.Nested(endereco_model), description="Lista de endereços do cliente")
})




@cliente_ns.route("/")
class ClienteList(Resource):
    @cliente_ns.marshal_list_with(cliente_model)
    def get(self):
        """Listar todos os clientes"""
        return cliente_controller.listar_clientes()

    @cliente_ns.expect(cliente_model)
    @cliente_ns.marshal_with(cliente_model, code=201)
    def post(self):
        """Criar um novo cliente"""
        data = request.get_json()
        return cliente_controller.criar_cliente(data), 201


@cliente_ns.route("/<int:id>")
@cliente_ns.param("id", "ID do cliente")
class ClienteDetail(Resource):
    @cliente_ns.marshal_with(cliente_model)
    def get(self, id):
        """Obter cliente por ID"""
        cliente = cliente_controller.obter_cliente(id)
        if not cliente:
            cliente_ns.abort(404, "Cliente não encontrado")
        return cliente

    @cliente_ns.expect(cliente_model)
    @cliente_ns.marshal_with(cliente_model)
    def put(self, id):
        """Atualizar dados do cliente"""
        data = request.get_json()
        cliente = cliente_controller.atualizar_cliente(id, data)
        if not cliente:
            cliente_ns.abort(404, "Cliente não encontrado")
        return cliente

    def delete(self, id):
        """Deletar cliente"""
        cliente = cliente_controller.deletar_cliente(id)
        if not cliente:
            cliente_ns.abort(404, "Cliente não encontrado")
        return {"mensagem": "Cliente deletado com sucesso"}, 204


@cliente_ns.route("/buscar_por_cpf/<string:cpf>")
@cliente_ns.param("cpf", "CPF do cliente")
class ClientePorCPF(Resource):
    @cliente_ns.marshal_with(cliente_model)
    def get(self, cpf):
        """Buscar cliente pelo CPF"""
        clientes = cliente_controller.buscar_clientes_por_cpf(cpf)
        if not clientes:
            cliente_ns.abort(404, "Cliente não encontrado")
        return clientes


@cliente_ns.route("/buscar_por_nome/<string:nome>")
@cliente_ns.param("nome", "Nome do cliente")
class ClientePorNome(Resource):
    def get(self, nome):
        """Buscar clientes pelo nome (parcial, sem erro de atributo)"""
        try:
            clientes = Cliente.query.filter(Cliente.nome.ilike(f"%{nome}%")).all()

            if not clientes:
                return jsonify({"error": "Nenhum cliente encontrado"}), 404

            resultado = []
            for c in clientes:
                resultado.append({
                    "id": c.id,
                    "nome": c.nome,
                    "cpf": c.cpf,
                    "telefone": c.telefone,
                    "email": c.email,
                    "enderecos": [{
                        "id": e.id,
                        "rua": e.rua,
                        "numero": e.numero,
                        "cidade": e.cidade,
                        "estado": e.estado,
                        "cep": e.cep
                    } for e in c.enderecos]
                })

            return jsonify(resultado)

        except Exception as e:
            print(f"❌ Erro em buscar_por_nome: {e}")
            return {"erro": str(e)}, 500
