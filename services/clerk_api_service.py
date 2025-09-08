import requests
from flask import current_app

class ClerkAPIClient:
    """Cliente para interactuar con la API de Clerk"""
    
    def __init__(self):
        self.api_key = current_app.config.get('CLERK_API_KEY')
        self.base_url = "https://api.clerk.dev/v1"
        
    def get_user_data(self, user_id):
        """
        Obtiene los datos de un usuario de Clerk usando su ID
        
        Args:
            user_id: ID del usuario en Clerk (sub del token JWT)
            
        Returns:
            dict: Datos del usuario o None si hay error
        """
        if not self.api_key:
            current_app.logger.error("CLERK_API_KEY no configurada")
            return None
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/users/{user_id}",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Error al obtener datos de usuario: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            current_app.logger.error(f"Error de conexión con Clerk API: {str(e)}")
            return None
            
    def get_user_email(self, user_id):
        """Obtiene el email principal del usuario"""
        user_data = self.get_user_data(user_id)
        if not user_data:
            return None
            
        try:
            email_addresses = user_data.get('email_addresses', [])
            if not email_addresses:
                return None
                
            # Buscar el email principal
            primary_email = next(
                (email['email_address'] for email in email_addresses if email.get('primary')), 
                None
            )
            
            # Si no hay email principal, tomar el primero
            if not primary_email and email_addresses:
                primary_email = email_addresses[0].get('email_address')
                
            return primary_email
        except Exception as e:
            current_app.logger.error(f"Error al extraer email: {str(e)}")
            return None
            
    def get_user_name(self, user_id):
        """Obtiene el nombre completo del usuario"""
        user_data = self.get_user_data(user_id)
        if not user_data:
            return None
            
        try:
            # Intentar obtener el nombre completo
            first_name = user_data.get('first_name', '')
            last_name = user_data.get('last_name', '')
            
            if first_name or last_name:
                return f"{first_name} {last_name}".strip()
            else:
                return None
        except Exception as e:
            current_app.logger.error(f"Error al extraer nombre: {str(e)}")
            return None
