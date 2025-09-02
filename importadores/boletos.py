import smtplib, os

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from app.config import Config

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
        attach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(caminho_pdf))
        msg.attach(attach)

    with smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT) as servidor:
        servidor.login(remetente, senha)
        servidor.send_message(msg)

