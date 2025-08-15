import os
from flask import Blueprint, jsonify
from importadores.importar_clientes import importar_clientes_docx
from importadores.importar_contratos import importar_contratos_docx

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

    if not os.path.isfile(clientes_path) or not os.path.isfile(contratos_path):
        return jsonify({"erro": "Arquivos de exemplo não encontrados no servidor"}), 404

    importar_clientes_docx(clientes_path)
    importar_contratos_docx(contratos_path)

    ja_importado = True
    return jsonify({"mensagem": "Importação concluída com sucesso!"})
