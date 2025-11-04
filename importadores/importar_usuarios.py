import os
from docx import Document
from app.database import db
from app.models.usuario import Usuario
from werkzeug.security import generate_password_hash

def importar_usuarios_docx(caminho_arquivo, app):
    with app.app_context():
        doc = Document(caminho_arquivo)
        usuarios_importados = 0
        erro_ocorrido = False

        for tabela in doc.tables:
            for i, linha in enumerate(tabela.rows):
                if i == 0:
                    continue
                
                try:
                    nome = linha.cells[0].text.strip()
                    login = linha.cells[1].text.strip()
                    senha = linha.cells[2].text.strip()
                    cargo = linha.cells[3].text.strip()

                    usuario_existente = Usuario.query.filter_by(login=login).first()
                    if usuario_existente:
                        print(f"Login duplicado encontrado para {login}. Usuário não será inserido.")
                        continue

                    usuario = Usuario(
                        nome=nome,
                        login=login,
                        cargo=cargo
                    )
                    usuario.set_senha(senha)

                    db.session.add(usuario)
                    usuarios_importados += 1
                except Exception as e:
                    erro_ocorrido = True
                    print(f"Erro ao processar a linha {i + 1}: {e}")

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao realizar commit: {e}")
            erro_ocorrido = True

        # Retorno
        if erro_ocorrido:
            print(f"Importação concluída com {usuarios_importados} usuários, mas houve erros durante o processo.")
        else:
            print(f"Importação concluída: {usuarios_importados} usuários adicionados.")


if __name__ == "__main__":
    from run import create_app
    app = create_app()
    with app.app_context():
        base_dir = os.path.dirname(os.path.abspath(__file__))
        caminho = os.path.join(base_dir, "usuarios_exemplo.docx")
        importar_usuarios_docx(caminho, app)



# python -m importadores.importar_usuarios