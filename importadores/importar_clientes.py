import os
from docx import Document
from app.database import db
from app.models.cliente import Cliente, Endereco
import re

def validar_telefone(telefone):
    return bool(re.match(r'^\d{10,11}$', telefone))

def importar_clientes_docx(caminho_arquivo, app):
    with app.app_context():
        doc = Document(caminho_arquivo)
        clientes_importados = 0
        clientes_atualizados = 0

        for tabela in doc.tables:
            for i, linha in enumerate(tabela.rows):
                if i == 0:
                    continue

                cells = [c.text.strip() for c in linha.cells]

                if len(cells) < 4:
                    print(f"Linha {i+1} inválida (faltando colunas). Ignorada.")
                    continue

                nome = cells[0]
                cpf = cells[1]
                telefone = cells[2]
                email = cells[3]
                rua = cells[4] if len(cells) > 4 else ""
                numero_end = cells[5].strip() if len(cells) > 5 else None
                cidade = cells[6] if len(cells) > 6 else ""
                estado = cells[7] if len(cells) > 7 else ""
                cep = cells[8] if len(cells) > 8 else ""

                if not nome or not cpf:
                    print(f"Registro inválido na linha {i + 1}")
                    continue

                if not validar_telefone(telefone):
                    print(f"Telefone inválido na linha {i + 1}. Ignorado.")
                    continue

                cliente = Cliente.query.filter_by(cpf=cpf).first()
                if cliente is not None:
                    cliente.nome = nome
                    cliente.numero = telefone
                    cliente.email = email

                    if rua or numero_end or cidade or estado or cep:
                        Endereco.query.filter_by(cliente_id=cliente.id).delete()
                        endereco = Endereco(
                            rua=rua,
                            numero=int(numero_end) if numero_end and numero_end.isdigit() else None,
                            cidade=cidade,
                            estado=estado,
                            cep=cep,
                            cliente_id=cliente.id
                        )
                        db.session.add(endereco)

                    clientes_atualizados += 1
                    print(f"Cliente com CPF {cpf} atualizado.")
                else:
                    cliente = Cliente(
                        nome=nome,
                        cpf=cpf,
                        numero=telefone,
                        email=email
                    )
                    db.session.add(cliente)
                    db.session.flush()

                    if rua or numero_end or cidade or estado or cep:
                        endereco = Endereco(
                            rua=rua,
                            numero=int(numero_end) if numero_end and numero_end.isdigit() else None,
                            cidade=cidade,
                            estado=estado,
                            cep=cep,
                            cliente_id=cliente.id
                        )
                        db.session.add(endereco)

                    clientes_importados += 1
                    print(f"Cliente com CPF {cpf} adicionado.")

        db.session.commit()
        print(f"Importação concluída: {clientes_importados} clientes adicionados, {clientes_atualizados} clientes atualizados.")

if __name__ == "__main__":
    from run import create_app
    app = create_app()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    caminho = os.path.join(base_dir, "clientes_exemplo.docx")
    importar_clientes_docx(caminho, app)

# python -m importadores.importar_clientes