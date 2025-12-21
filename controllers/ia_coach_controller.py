from flask import request, jsonify, g, current_app
from services.auth_service import auth_required
from datetime import date
import logging

logger = logging.getLogger(__name__)


class IACoachController:
    """Controlador para los endpoints de IA Coach"""

    def __init__(self, ia_coach_service):
        """
        Inicializa el controlador con el servicio de IA Coach.
        
        Args:
            ia_coach_service: Instancia del servicio IACoachService
        """
        self.service = ia_coach_service

    def obtener_consejo_del_dia(self):
        """
        GET /api/ia-coach/consejo-diario
        
        Obtiene o genera el consejo del día para el usuario.
        Marca automáticamente como leído.
        
        Returns:
            JSON con los consejos del día
        """
        try:
            # Obtener ID del usuario desde el contexto
            id_clerk = g.current_user.id_clerk

            if not id_clerk:
                return jsonify({
                    'success': False,
                    'message': 'No se pudo obtener el ID del usuario'
                }), 401

            logger.info(f"Obteniendo consejo del día para {id_clerk}")

            # Obtener o generar análisis del día
            analisis = self.service.obtener_o_generar_analisis_diario(id_clerk)

            # Si el análisis está pendiente, generar consejos
            if analisis['estado_procesamiento'] == 'pendiente':
                logger.info(f"Generando consejos para análisis {analisis['id']}")
                self.service.generar_consejos_con_ia(analisis['id'], id_clerk)

            # Obtener consejos del día
            consejos = self.service.obtener_consejos_del_dia(id_clerk)

            # Marcar todos como leídos
            for consejo in consejos:
                if not consejo['leido']:
                    try:
                        self.service.marcar_consejo_como_leido(consejo['id'], id_clerk)
                        consejo['leido'] = True
                    except Exception as e:
                        logger.warning(f"Error marcando consejo como leído: {str(e)}")

            # Obtener fecha actual del usuario en su zona horaria
            from services.timezone_service import TimezoneService
            tz_service = TimezoneService()
            fecha_usuario = tz_service.get_user_local_date(id_clerk)

            return jsonify({
                'success': True,
                'data': {
                    'consejos': consejos,
                    'total_consejos': len(consejos),
                    'fecha': str(fecha_usuario)
                }
            }), 200

        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400

        except Exception as e:
            logger.error(f"Error en obtener_consejo_del_dia: {str(e)}")
            import os
            error_detail = str(e) if os.getenv('DEBUG', 'False').lower() == 'true' else None
            return jsonify({
                'success': False,
                'message': 'Error al obtener el consejo del día',
                'error': error_detail
            }), 500

    def registrar_interaccion(self):
        """
        POST /api/ia-coach/interaccion
        
        Registra la interacción del usuario con un consejo.
        
        Body (JSON):
        {
            "id_consejo": "uuid-del-consejo",
            "accion": "visto|archivado|seguido|ignorado"
        }
        
        Returns:
            JSON con el resultado
        """
        try:
            # Obtener ID del usuario desde el contexto
            id_clerk = g.current_user.id_clerk

            if not id_clerk:
                return jsonify({
                    'success': False,
                    'message': 'No se pudo obtener el ID del usuario'
                }), 401

            # Obtener datos del request
            datos = request.get_json()

            if not datos:
                return jsonify({
                    'success': False,
                    'message': 'Body del request no puede estar vacío'
                }), 400

            id_consejo = datos.get('id_consejo')
            accion = datos.get('accion')

            # Validar parámetros
            if not id_consejo or not accion:
                return jsonify({
                    'success': False,
                    'message': 'id_consejo y accion son requeridos'
                }), 400

            logger.info(f"Registrando interacción: {id_consejo} - {accion}")

            # Registrar interacción
            self.service.registrar_interaccion(id_consejo, id_clerk, accion)

            return jsonify({
                'success': True,
                'message': 'Interacción registrada correctamente'
            }), 200

        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400

        except Exception as e:
            logger.error(f"Error en registrar_interaccion: {str(e)}")
            error_detail = str(e) if current_app.config.get('DEBUG', False) else None
            return jsonify({
                'success': False,
                'message': 'Error al registrar la interacción',
                'error': error_detail
            }), 500

    def actualizar_consejo_diario(self):
        """
        POST /api/v1/ia-coach/actualizar-consejo
        
        Fuerza la regeneración del consejo del día si hay cambios significativos.
        Útil cuando el usuario completa más hábitos después de ver el primer consejo.
        
        Returns:
            JSON con los consejos actualizados o los mismos si no hay cambios
        """
        try:
            id_clerk = g.current_user.id_clerk

            if not id_clerk:
                return jsonify({
                    'success': False,
                    'message': 'No se pudo obtener el ID del usuario'
                }), 401

            logger.info(f"Actualizando consejo para {id_clerk}")

            # Regenerar análisis forzadamente
            analisis = self.service.obtener_o_generar_analisis_diario(id_clerk, forzar_regenerar=True)

            # Si el análisis está pendiente, generar consejos
            if analisis['estado_procesamiento'] == 'pendiente':
                logger.info(f"Regenerando consejos para análisis {analisis['id']}")
                self.service.generar_consejos_con_ia(analisis['id'], id_clerk)

            # Obtener consejos del día
            consejos = self.service.obtener_consejos_del_dia(id_clerk)

            # Marcar todos como leídos
            for consejo in consejos:
                if not consejo['leido']:
                    try:
                        self.service.marcar_consejo_como_leido(consejo['id'], id_clerk)
                        consejo['leido'] = True
                    except Exception as e:
                        logger.warning(f"Error marcando consejo como leído: {str(e)}")

            # Obtener fecha actual del usuario en su zona horaria
            from services.timezone_service import TimezoneService
            tz_service = TimezoneService()
            fecha_usuario = tz_service.get_user_local_date(id_clerk)

            return jsonify({
                'success': True,
                'data': {
                    'consejos': consejos,
                    'total_consejos': len(consejos),
                    'fecha': str(fecha_usuario),
                    'actualizado': True
                }
            }), 200

        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400

        except Exception as e:
            logger.error(f"Error en actualizar_consejo_diario: {str(e)}")
            error_detail = str(e) if current_app.config.get('DEBUG', False) else None
            return jsonify({
                'success': False,
                'message': 'Error al actualizar el consejo del día',
                'error': error_detail
            }), 500


    def generar_sugerencias_habitos(self):
        """
        POST /api/ia-coach/sugerencias-habitos
        
        Genera sugerencias de hábitos basadas en un input del usuario y sus hábitos actuales.
        
        Body (JSON):
            {
                "input_usuario": "bajar 10 kg"
            }
        
        Returns:
            JSON con sugerencias de hábitos
        """
        try:
            # Obtener ID del usuario desde el contexto
            id_clerk = g.current_user.id_clerk

            if not id_clerk:
                return jsonify({
                    'success': False,
                    'message': 'No se pudo obtener el ID del usuario'
                }), 401

            # Obtener datos del request
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'message': 'Se requiere body JSON'
                }), 400

            input_usuario = data.get('input_usuario', '').strip()

            if not input_usuario:
                return jsonify({
                    'success': False,
                    'message': 'input_usuario es requerido'
                }), 400

            logger.info(f"Generando sugerencias de hábitos para {id_clerk} con input: {input_usuario}")

            # Generar sugerencias con IA
            sugerencias = self.service.generar_sugerencias_habitos(id_clerk, input_usuario)

            return jsonify({
                'success': True,
                'data': sugerencias
            }), 200

        except ValueError as e:
            logger.error(f"Error de validación: {str(e)}")
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400

        except Exception as e:
            logger.error(f"Error en generar_sugerencias_habitos: {str(e)}")
            error_detail = str(e) if current_app.config.get('DEBUG', False) else None
            return jsonify({
                'success': False,
                'message': 'Error al generar sugerencias de hábitos',
                'error': error_detail
            }), 500


def crear_controlador(ia_coach_service):
    """
    Factory function para crear una instancia del controlador.
    
    Args:
        ia_coach_service: Instancia del servicio IACoachService
        
    Returns:
        IACoachController: Instancia del controlador
    """
    return IACoachController(ia_coach_service)
