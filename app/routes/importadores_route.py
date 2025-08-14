from flask import Blueprint, jsonify
from importadores.importar_clientes import importar_clientes_docx
from importadores.importar_contratos import importar_contratos_docx
import os

import_bp = Blueprint("import_bp", __name__)

ja_importado = False

@import_bp.route("/importar-exemplos")
def importar_exemplos():
    global ja_importado

    if ja_importado:
        return jsonify({"mensagem": "Os dados já foram importados, não é possível rodar novamente."}), 403

    base_dir = os.path.dirname(os.path.abspath(__file__))
    clientes_path = os.path.join(base_dir, "../importadores/clientes_exemplo.docx")
    contratos_path = os.path.join(base_dir, "../importadores/contratos_exemplo.docx")

    importar_clientes_docx(clientes_path)
    importar_contratos_docx(contratos_path)

    ja_importado = True
    return jsonify({"mensagem": "Importação concluída com sucesso!"})
