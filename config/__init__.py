from .app_config import configure_app
from .encoding_config import configure_encoding
from .timezone_config import configure_timezone
from .blueprints_config import register_blueprints, configure_extensions, configure_cors
from .mail_config import configure_mail

def configure_application(app):
    """Configurar toda la aplicación Flask con todas las configuraciones"""
    configure_app(app)
    configure_encoding(app)
    configure_timezone(app)
    configure_extensions(app)
    # Configurar CORS antes de registrar los blueprints
    configure_cors(app)
    register_blueprints(app)
    configure_mail(app)

__all__ = ['configure_application']
