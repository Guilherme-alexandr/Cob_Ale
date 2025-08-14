import os
from dotenv import load_dotenv

load_dotenv()

db_url = os.getenv("DATABASE_URL", "postgresql://cobranca_db_user:ZYFg0U0nE12kqCYLjuVWCYN7ZLUgjxqS@dpg-d2f7a0mmcj7s73eft3r0-a.ohio-postgres.render.com/cobranca_db")

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

class Config:
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
