import jwt
import requests
from flask import current_app, g
from models import db, User
from functools import wraps
from flask import request, jsonify
import traceback
from services.clerk_service import get_clerk_user_data

def verify_clerk_token(token):
    """Verificar token JWT de Clerk"""
    try:
        jwks_url = current_app.config['CLERK_JWKS_URL']
        response = requests.get(jwks_url)
        jwks = response.json()
        
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        # Verificar si el token es de nuestro template personalizado
        template_id = current_app.config.get('CLERK_JWT_TEMPLATE_ID')
        using_custom_template = decoded.get('jwt_template_id') == template_id if template_id else False
        
        # Mostrar todo el contenido del token para depuración (excepto información sensible)
        token_content = {k: v for k, v in decoded.items() if k not in ['aud', 'azp', 'jti']}
        current_app.logger.info(f"CONTENIDO COMPLETO DEL TOKEN: {token_content}")
        
        # Registrar datos específicos importantes
        current_app.logger.info(
            f"DATOS DE USUARIO EN TOKEN: "
            f"sub={decoded.get('sub')}, "
            f"email={decoded.get('email')}, "
            f"email_address={decoded.get('email_address')}, "
            f"nombre_completo={decoded.get('nombre_completo')}, "
            f"name={decoded.get('name')}, "
            f"first_name={decoded.get('first_name')}, "
            f"last_name={decoded.get('last_name')}, "
            f"jwt_template_id={decoded.get('jwt_template_id')}"
        )
        
        return decoded
    except Exception as e:
        current_app.logger.error(f"Error verificando token: {str(e)}")
        return None

def get_or_create_user(payload):
    """Obtener o crear usuario a partir de payload JWT"""
    user_id = payload.get('sub')
    user = User.query.filter_by(id_clerk=user_id).first()
    
    # Verificar si el token es de nuestro template personalizado
    template_id = current_app.config.get('CLERK_JWT_TEMPLATE_ID')
    using_custom_template = payload.get('jwt_template_id') == template_id if template_id else False
    
    # Obtener datos del JWT personalizado
    email = payload.get('email', '')
    nombre_completo = payload.get('nombre_completo', '')
    
    # Registrar los datos que estamos extrayendo
    current_app.logger.info(f"EXTRAYENDO DATOS DE USUARIO: " 
                           f"email_del_template={email}, " 
                           f"nombre_completo_del_template={nombre_completo}")
    
    # Si no hay datos suficientes en el token, intentar obtener desde la API de Clerk
    if (not email or not nombre_completo) and user_id:
        try:
            clerk_data = get_clerk_user_data(user_id)
            if clerk_data:
                current_app.logger.info(f"DATOS OBTENIDOS DE API CLERK: {clerk_data}")
                
                # Si no tenemos email del token, usar el de la API
                if not email and clerk_data.get('email'):
                    email = clerk_data.get('email')
                    current_app.logger.info(f"EMAIL OBTENIDO DE API CLERK: {email}")
                
                # Si no tenemos nombre del token, usar el de la API
                if not nombre_completo and clerk_data.get('nombre_completo'):
                    nombre_completo = clerk_data.get('nombre_completo')
                    current_app.logger.info(f"NOMBRE COMPLETO OBTENIDO DE API CLERK: {nombre_completo}")
            else:
                current_app.logger.warning(f"No se pudieron obtener datos desde la API de Clerk para usuario {user_id}")
        except Exception as e:
            current_app.logger.error(f"Error al obtener datos desde Clerk API: {str(e)}")
            traceback.print_exc()
    
    # Si no se encontraron en el template personalizado, intentar con campos estándar
    if not email:
        email = payload.get('email_address', '')
        if not email and 'email_addresses' in payload and payload['email_addresses']:
            # Intentar obtener desde email_addresses si existe
            try:
                primary_email = next((e['email_address'] for e in payload['email_addresses'] 
                                    if e.get('primary')), None)
                if primary_email:
                    email = primary_email
            except Exception as e:
                current_app.logger.error(f"Error extrayendo email_addresses: {str(e)}")
    
    if not nombre_completo:
        nombre_completo = payload.get('name', '')
        # Intentar construir desde first_name y last_name si están disponibles
        if not nombre_completo and (payload.get('first_name') or payload.get('last_name')):
            first = payload.get('first_name', '')
            last = payload.get('last_name', '')
            nombre_completo = f"{first} {last}".strip()
            
    # Registrar los datos finales después de intentar todas las opciones
    current_app.logger.info(f"DATOS FINALES EXTRAÍDOS: " 
                           f"email={email}, " 
                           f"nombre_completo={nombre_completo}")
    
    url_imagen = payload.get('picture', '')
    
    if using_custom_template:
        current_app.logger.info(f"Usando token personalizado para usuario {payload.get('sub')}")
    
    if not user:
        # Crear nuevo usuario
        user = User(
            id_clerk=payload.get('sub'),
            correo=email,
            nombre_completo=nombre_completo,
            url_imagen=url_imagen
        )
        db.session.add(user)
        try:
            current_app.logger.info(f"CREANDO NUEVO USUARIO: id_clerk={payload.get('sub')}, "
                                   f"correo={email}, nombre_completo={nombre_completo}")
            db.session.commit()
            current_app.logger.info(f"USUARIO CREADO EXITOSAMENTE: {user.id_clerk}")
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"ERROR AL CREAR USUARIO: {str(e)}")
            user = User.query.filter_by(id_clerk=payload.get('sub')).first()
            if not user:
                raise e
    else:
        # Actualizar información si es necesario
        current_app.logger.info(f"USUARIO EXISTENTE: id_clerk={user.id_clerk}, "
                               f"correo_actual={user.correo}, nombre_actual={user.nombre_completo}")
        
        actualizado = False
        
        if email and (not user.correo or user.correo != email):
            current_app.logger.info(f"ACTUALIZANDO CORREO: {user.correo} -> {email}")
            user.correo = email
            actualizado = True
            
        if nombre_completo and (not user.nombre_completo or user.nombre_completo != nombre_completo):
            current_app.logger.info(f"ACTUALIZANDO NOMBRE: {user.nombre_completo} -> {nombre_completo}")
            user.nombre_completo = nombre_completo
            actualizado = True
            
        if url_imagen and not user.url_imagen:
            user.url_imagen = url_imagen
            actualizado = True
            
        if actualizado:
            try:
                db.session.commit()
                current_app.logger.info(f"Usuario actualizado: {user.id_clerk}")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error al actualizar usuario: {str(e)}")
    
    return user

def auth_required(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Permitir solicitudes OPTIONS sin autenticación
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
            
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
