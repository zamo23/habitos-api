from flask import current_app, render_template
from flask_mail import Message
from config.mail_config import mail
import logging

logger = logging.getLogger(__name__)

def send_group_invitation(email, invitation_data):
    """
    Envía un correo electrónico de invitación para unirse a un grupo
    
    Args:
        email (str): Correo electrónico del destinatario
        invitation_data (dict): Datos de la invitación con los siguientes campos:
            - invitador_nombre: Nombre del usuario que invita
            - nombre_grupo: Nombre del grupo
            - descripcion_grupo: Descripción del grupo
            - token: Token de invitación
            - url_base: URL base de la aplicación (opcional)
    """
    try:
        # Configurar la URL de aceptación
        url_base = invitation_data.get('url_base', 'https://habitos.cvpx.lat')
        url_aceptar = f"{url_base}/join-group?token={invitation_data['token']}"
        
        # Renderizar la plantilla HTML
        html_content = render_template(
            'email/group_invitation.html',
            invitador_nombre=invitation_data['invitador_nombre'],
            nombre_grupo=invitation_data['nombre_grupo'],
            descripcion_grupo=invitation_data.get('descripcion_grupo', 'Sin descripción'),
            url_aceptar=url_aceptar
        )
        
        # Crear el mensaje
        subject = f"Invitación al grupo {invitation_data['nombre_grupo']}"
        msg = Message(
            subject=subject,
            recipients=[email],
            html=html_content
        )
        
        # Enviar el correo
        mail.send(msg)
        logger.info(f"Correo de invitación enviado a {email} para el grupo {invitation_data['nombre_grupo']}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar correo de invitación: {str(e)}")
        return False
