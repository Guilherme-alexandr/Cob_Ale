from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

def role_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                verify_jwt_in_request()
                usuario = get_jwt_identity()
                if usuario['cargo'] not in roles:
                    return jsonify({"mensagem": "Acesso negado: usuario sem permissão."}), 403
            except Exception:
                return jsonify({"mensagem": "Acesso negado: token inválido ou não fornecido."}), 401
            return func(*args, **kwargs)
        return wrapper
    return decorator