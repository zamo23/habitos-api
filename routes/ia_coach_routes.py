from flask import Blueprint
from controllers.ia_coach_controller import crear_controlador
from services.ia_coach_service import IACoachService
from services.auth_service import auth_required
import os


def crear_rutas_ia_coach(app):
    """
    Crea y registra las rutas del API de IA Coach.
    
    Args:
        app: Aplicación Flask
        
    Returns:
        Blueprint: Blueprint con las rutas registradas
    """
    blueprint = Blueprint('ia_coach', __name__, url_prefix='/api/v1/ia-coach')

    # Inicializar servicio
    api_gemini = os.getenv('API_GEMINI')
    gemini_model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash-lite')

    if not api_gemini:
        raise ValueError("API_GEMINI no está configurada en .env")

    service = IACoachService(api_gemini, gemini_model)
    controlador = crear_controlador(service)

    # Rutas
    @blueprint.route('/consejo-diario', methods=['GET', 'OPTIONS'])
    @auth_required
    def obtener_consejo():
        """Obtiene o genera el consejo del día"""
        return controlador.obtener_consejo_del_dia()

    @blueprint.route('/interaccion', methods=['POST', 'OPTIONS'])
    @auth_required
    def registrar_interaccion():
        """Registra la interacción del usuario con un consejo"""
        return controlador.registrar_interaccion()

    @blueprint.route('/actualizar-consejo', methods=['POST', 'OPTIONS'])
    @auth_required
    def actualizar_consejo():
        """Fuerza la regeneración del consejo si hay cambios significativos"""
        return controlador.actualizar_consejo_diario()

    return blueprint
