from . import api
from swagger.namespaces.cliente_ns import cliente_ns
from swagger.namespaces.contrato_ns import contrato_ns
from swagger.namespaces.acordo_ns import acordo_ns


def configure_swagger(app):
    api.init_app(app)
    api.add_namespace(cliente_ns, path="/clientes")
    api.add_namespace(contrato_ns, path="/contratos")
    api.add_namespace(acordo_ns, path="/acordos")
    api.mask_swagger = False
