import requests
from flask import current_app

def get_clerk_user_data(user_id):
    """
    Obtiene datos de usuario directamente desde la API de Clerk
    """
    if not user_id:
        current_app.logger.error("No se puede obtener datos de usuario: ID no proporcionado")
        return None
    
    api_key = current_app.config.get('CLERK_API_KEY')
    if not api_key:
        current_app.logger.error("No se puede obtener datos de usuario: CLERK_API_KEY no configurada")
        return None
    
    base_url = current_app.config.get('CLERK_API_BASE', 'https://api.clerk.dev/v1')
    url = f"{base_url}/users/{user_id}"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        current_app.logger.info(f"Consultando API de Clerk para usuario {user_id}")
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            current_app.logger.error(f"Error al obtener datos de usuario desde Clerk: {response.status_code} - {response.text}")
            return None
        
        user_data = response.json()
        current_app.logger.info(f"Datos de usuario obtenidos correctamente desde API de Clerk")
        
        # Extraer los datos relevantes
        result = {
            'id': user_data.get('id'),
            'email': None,
            'nombre_completo': None,
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'image_url': user_data.get('image_url')
        }
        
        # Obtener el email primario
        email_addresses = user_data.get('email_addresses', [])
        primary_email = next((email.get('email_address') for email in email_addresses 
                             if email.get('id') == user_data.get('primary_email_address_id')), None)
        
        if primary_email:
            result['email'] = primary_email
        
        # Construir nombre completo
        if user_data.get('first_name') or user_data.get('last_name'):
            result['nombre_completo'] = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
        
        return result
    except Exception as e:
        current_app.logger.error(f"Error al consultar API de Clerk: {str(e)}")
        return None
