from flask_restx import Api

api = Api(
    version="1.0",
    title="API de Cobrança - CobAle",
    description="Documentação da API para Clientes, Contratos e Acordos",
    doc="/docs",
    mask_swagger=False,
)
