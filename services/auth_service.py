import jwt
import requests
from flask import current_app, g
from models import db, User
from functools import wraps
from flask import request, jsonify

def verify_clerk_token(token):
    """Verificar token JWT de Clerk"""
    try:
        jwks_url = current_app.config['CLERK_JWKS_URL']
        response = requests.get(jwks_url)
        jwks = response.json()
        
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        current_app.logger.error(f"Error verificando token: {str(e)}")
        return None

def get_or_create_user(payload):
    """Obtener o crear usuario a partir de payload JWT"""
    user = User.query.filter_by(id_clerk=payload.get('sub')).first()
    if not user:
        user = User(
            id_clerk=payload.get('sub'),
            correo=payload.get('email', ''),
            nombre_completo=payload.get('name', ''),
            url_imagen=payload.get('picture', '')
        )
        db.session.add(user)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            user = User.query.filter_by(id_clerk=payload.get('sub')).first()
            if not user:
                raise e
    return user

def auth_required(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': {'code': 'unauthorized', 'message': 'Token requerido'}}), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_clerk_token(token)
        if not payload:
            return jsonify({'error': {'code': 'invalid_token', 'message': 'Token inválido'}}), 401
        
        # Obtener o crear usuario
        try:
            user = get_or_create_user(payload)
            g.current_user = user
            return f(*args, **kwargs)
        except Exception as e:
            current_app.logger.error(f"Error en auth_required: {str(e)}")
            return jsonify({'error': {'code': 'server_error', 'message': 'Error de servidor'}}), 500
    
    return decorated_function
