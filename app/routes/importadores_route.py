import os
from flask import Blueprint, jsonify, current_app
from ..controllers.cliente_controller import importar_clientes_docx
from ..controllers.contrato_controller import importar_contratos_docx
from ..controllers.usuario_controller import importar_usuarios_docx

import_bp = Blueprint("import_bp", __name__)

ja_importado = False

@import_bp.route("/importar-exemplos")
def importar_exemplos():
    global ja_importado

    if ja_importado:
        return jsonify({"mensagem": "Os dados já foram importados, não é possível rodar novamente."}), 403

    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    clientes_path = os.path.join(root_dir, "importadores/clientes_exemplo.docx")
    contratos_path = os.path.join(root_dir, "importadores/contratos_exemplo.docx")
    usuarios_path = os.path.join(root_dir, "importadores/usuarios_exemplo.docx")

    if not os.path.isfile(clientes_path) or not os.path.isfile(contratos_path) or not os.path.isfile(usuarios_path):
        return jsonify({"erro": "Arquivos de exemplo não encontrados no servidor"}), 404

    try:
        importar_clientes_docx(clientes_path, current_app)
        importar_contratos_docx(contratos_path, current_app)
        importar_usuarios_docx(usuarios_path, current_app)
    except Exception as e:
        return jsonify({"erro": f"Erro durante a importação: {str(e)}"}), 500

    ja_importado = True
    return jsonify({"mensagem": "Importação concluída com sucesso!"})

@import_bp.route("/importar-exemplo-cliente")
def importar_exemplo_cliente():
    global ja_importado

    if ja_importado:
        return jsonify({"mensagem": "Os dados já foram importados, não é possível rodar novamente."}), 403

    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    clientes_path = os.path.join(root_dir, "importadores/clientes_exemplo.docx")

    if not os.path.isfile(clientes_path):
        return jsonify({"erro": "Arquivo de exemplo de clientes não encontrado no servidor"}), 404

    try:
        importar_clientes_docx(clientes_path, current_app)
    except Exception as e:
        return jsonify({"erro": f"Erro durante a importação: {str(e)}"}), 500

    ja_importado = True
    return jsonify({"mensagem": "Importação do exemplo de cliente concluída com sucesso!"})

@import_bp.route("/importar-exemplo-contratos")
def importar_exemplo_contratos():
    global ja_importado

    if ja_importado:
        return jsonify({"mensagem": "Os dados já foram importados, não é possível rodar novamente."}), 403

    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    contratos_path = os.path.join(root_dir, "importadores/contratos_exemplo.docx")

    if not os.path.isfile(contratos_path):
        return jsonify({"erro": "Arquivo de exemplo de contratos não encontrado no servidor"}), 404

    try:
        importar_contratos_docx(contratos_path, current_app)
    except Exception as e:
        return jsonify({"erro": f"Erro durante a importação: {str(e)}"}), 500

    ja_importado = True
    return jsonify({"mensagem": "Importação do exemplo de contratos concluída com sucesso!"})

@import_bp.route("/importar-exemplo-usuarios")
def importar_exemplo_usuarios():
    global ja_importado

    if ja_importado:
        return jsonify({"mensagem": "Os dados já foram importados, não é possível rodar novamente."}), 403

    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    usuarios_path = os.path.join(root_dir, "importadores/usuarios_exemplo.docx")

    if not os.path.isfile(usuarios_path):
        return jsonify({"erro": "Arquivo de exemplo de usuários não encontrado no servidor"}), 404

    try:
        importar_usuarios_docx(usuarios_path, current_app)
    except Exception as e:
        return jsonify({"erro": f"Erro durante a importação: {str(e)}"}), 500

    ja_importado = True
    return jsonify({"mensagem": "Importação do exemplo de usuários concluída com sucesso!"})
