import os
from docx import Document
from app.database import db
from app.models.cliente import Cliente
from run import create_app

def importar_clientes_docx(caminho_arquivo):
    doc = Document(caminho_arquivo)
    clientes_importados = 0

    for tabela in doc.tables:
        for i, linha in enumerate(tabela.rows):
            if i == 0:
                continue

            nome = linha.cells[0].text.strip()
            cpf = linha.cells[1].text.strip()
            numero = linha.cells[2].text.strip()
            email = linha.cells[3].text.strip()

            if not nome or not cpf:
                print(f"Registro inválido na linha {i + 1}")
                continue

            cliente = Cliente(
                nome=nome,
                cpf=cpf,
                numero=numero,
                email=email
            )
            db.session.add(cliente)
            clientes_importados += 1

    db.session.commit()
    print(f"Importação concluída: {clientes_importados} clientes adicionados.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        base_dir = os.path.dirname(os.path.abspath(__file__))
        caminho = os.path.join(base_dir, "clientes_exemplo.docx")
        importar_clientes_docx(caminho)

# python -m importadores.importar_clientes