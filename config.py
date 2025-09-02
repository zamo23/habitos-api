from config.app_config import configure_app as configure_app_settings
from config.encoding_config import configure_encoding
from config.timezone_config import configure_timezone

def configure_app(app):
    """Configurar la aplicación Flask con todas las configuraciones"""
    configure_app_settings(app)
    configure_encoding(app)
    configure_timezone(app)
