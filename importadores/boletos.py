import smtplib, os
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText
from app.config import Config
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

def gerar_boleto(contrato, acordo, cliente, caminho_pdf, pasta_img):
    c = canvas.Canvas(caminho_pdf, pagesize=A4)
    largura, altura = A4

    logo_path = pasta_img
    if os.path.exists(logo_path):
        c.drawImage(logo_path, 15*mm, altura - 30*mm, width=40*mm, height=15*mm, preserveAspectRatio=True)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(60*mm, altura - 25*mm, "CobAle - Sistema de Cobrança")
    c.setFont("Helvetica", 10)
    c.drawString(60*mm, altura - 30*mm, "CNPJ: 00.000.000/0001-00")
    c.drawString(60*mm, altura - 35*mm, "Rua Exemplo, 123 - Goiânia - GO")

    caixa_x = 15*mm
    caixa_y = altura - 250*mm
    caixa_largura = largura - 30*mm
    caixa_altura = 200*mm
    c.rect(caixa_x, caixa_y, caixa_largura, caixa_altura)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, caixa_y + caixa_altura - 15*mm, "Boleto de Cobrança")
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, caixa_y + caixa_altura - 25*mm, f"Contrato: {contrato['numero_contrato']} | Filial: {contrato['filial']}")
    c.drawString(20*mm, caixa_y + caixa_altura - 35*mm, f"Vencimento: {acordo['vencimento']}")
    c.drawString(20*mm, caixa_y + caixa_altura - 45*mm, f"Valor: R$ {acordo['valor']:.2f}")
    c.drawString(20*mm, caixa_y + caixa_altura - 55*mm, f"Nosso número: {str(acordo['id']).zfill(7)}")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(20*mm, caixa_y + caixa_altura - 70*mm, "Sacado:")
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, caixa_y + caixa_altura - 80*mm, f"{cliente['nome']} - CPF: {cliente['cpf']}")
    c.drawString(20*mm, caixa_y + caixa_altura - 90*mm, f"Email: {cliente['email']}")

    c.setFont("Helvetica-Bold", 10)
    c.drawString(20*mm, caixa_y + caixa_altura - 110*mm, "Instruções:")
    c.setFont("Helvetica", 10)
    c.drawString(20*mm, caixa_y + caixa_altura - 120*mm, "- Pagável em qualquer banco até a data de vencimento")
    c.drawString(20*mm, caixa_y + caixa_altura - 130*mm, "- Após o vencimento, juros podem ser aplicados")

    c.line(caixa_x + 5*mm, caixa_y + 15*mm, caixa_x + caixa_largura - 5*mm, caixa_y + 15*mm)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, caixa_y + 5*mm, f"Código de barras: | {str(acordo['id']).zfill(7)} | {acordo['valor']:.2f} |")

    c.showPage()
    c.save()

    return caminho_pdf




def enviar_boleto_email(destinatario, caminho_pdf):
    remetente = Config.MAIL_USERNAME
    senha = Config.MAIL_PASSWORD

    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = destinatario
    msg['Subject'] = "Boleto do seu acordo - CobAle"

    corpo = "Olá, segue em anexo o boleto referente ao seu acordo."
    msg.attach(MIMEText(corpo, 'plain'))
    with open(caminho_pdf, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="pdf")
        attach.add_header('Content-Disposition', 'attachment', filename="boleto.pdf")
        msg.attach(attach)

    with smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT) as servidor:
        servidor.login(remetente, senha)
        servidor.send_message(msg)
