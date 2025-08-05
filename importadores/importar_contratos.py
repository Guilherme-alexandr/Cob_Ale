from docx import Document
from datetime import datetime
from app.database import db
from app.models.contrato import Contrato
from run import create_app

def importar_contratos_docx(caminho_arquivo):
    doc = Document(caminho_arquivo)
    contratos_importados = 0

    for tabela in doc.tables:
        for i, linha in enumerate(tabela.rows):
            if i == 0:
                continue

            cliente_id = int(linha.cells[0].text.strip())
            numero_contrato = linha.cells[1].text.strip()
            vencimento_str = linha.cells[2].text.strip()
            valor_total = float(linha.cells[3].text.strip().replace(',', '.'))
            filial = linha.cells[4].text.strip()

            try:
                vencimento = datetime.strptime(vencimento_str, "%Y-%m-%d")
            except ValueError:
                print(f"Data inválida na linha {i + 1}: {vencimento_str}")
                continue

            contrato = Contrato(
                cliente_id=cliente_id,
                numero_contrato=numero_contrato,
                vencimento=vencimento,
                valor_total=valor_total,
                filial=filial
            )

            db.session.add(contrato)
            contratos_importados += 1

    db.session.commit()
    print(f"Importação concluída: {contratos_importados} contratos adicionados.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        importar_contratos_docx(
            "C:/Users/guilh/OneDrive/Documentos/contratos_exemplo.docx"
        )
