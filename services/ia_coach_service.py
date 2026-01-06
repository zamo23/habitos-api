import json
import logging
from datetime import datetime, date
from uuid import uuid4
import pytz
import google.generativeai as genai
from sqlalchemy import func

from models import db
from models.ia_coach import IAAnalisisDiario, IAConsejo, IAConsejoInteraccion
from models.habit import Habit, HabitEntry, HabitStreak
from models.user import User

logger = logging.getLogger(__name__)


class IACoachService:
    """Servicio para gestionar el coaching con IA"""

    def __init__(self, api_key, model_name):
        """
        Inicializa el servicio de IA Coach
        
        Args:
            api_key: Clave API de Google Generative AI
            model_name: Nombre del modelo a usar (ej: gemini-2.5-flash-lite)
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.logger = logger

    def obtener_o_generar_analisis_diario(self, id_clerk, forzar_regenerar=False):
        """
        Obtiene el análisis del día o crea uno nuevo si no existe.
        Regenera si hay cambios significativos en los datos.
        
        Args:
            id_clerk: ID del usuario en Clerk
            forzar_regenerar: Si True, regenera aunque ya exista
            
        Returns:
            dict: Con 'id' y 'estado_procesamiento'
        """
        try:
            # Obtener la fecha actual del usuario en su zona horaria
            from services.timezone_service import TimezoneService
            tz_service = TimezoneService()
            hoy = tz_service.get_user_local_date(id_clerk)

            # Verificar si existe análisis para hoy
            analisis_existente = IAAnalisisDiario.query.filter_by(
                id_clerk=id_clerk,
                fecha_analisis=hoy
            ).first()

            # Recopilar datos actuales
            datos_actuales = self.recopilar_datos_usuario(id_clerk)

            if analisis_existente:
                if forzar_regenerar:
                    # Forzar regeneración: actualizar datos y marcar como pendiente
                    analisis_existente.datos_enviados = json.dumps(datos_actuales, ensure_ascii=False)
                    analisis_existente.estado_procesamiento = 'pendiente'
                    analisis_existente.respuesta_ia = None  # Limpiar respuesta anterior
                    db.session.commit()
                    
                    self.logger.info(f"Análisis forzado a regenerar para {id_clerk}")
                    
                    return {
                        'id': analisis_existente.id,
                        'estado_procesamiento': 'pendiente'
                    }
                
                else:
                    # No forzado: verificar si hay cambios significativos
                    datos_previos = json.loads(analisis_existente.datos_enviados)
                    cambio_significativo = self._detectar_cambios_significativos(datos_previos, datos_actuales)
                    
                    if cambio_significativo:
                        # Si hay cambios, actualizar los datos
                        analisis_existente.datos_enviados = json.dumps(datos_actuales, ensure_ascii=False)
                        analisis_existente.estado_procesamiento = 'pendiente'
                        db.session.commit()
                        
                        self.logger.info(f"Análisis actualizado por cambios significativos para {id_clerk}")
                        
                        return {
                            'id': analisis_existente.id,
                            'estado_procesamiento': 'pendiente'
                        }
                    
                    # Sin cambios significativos, retornar existente
                    return {
                        'id': analisis_existente.id,
                        'estado_procesamiento': analisis_existente.estado_procesamiento
                    }

            # Crear nuevo análisis (no existe para hoy)
            id_analisis = str(uuid4())

            analisis_nuevo = IAAnalisisDiario(
                id=id_analisis,
                id_clerk=id_clerk,
                fecha_analisis=hoy,
                datos_enviados=json.dumps(datos_actuales, ensure_ascii=False),
                estado_procesamiento='pendiente'
            )

            db.session.add(analisis_nuevo)
            db.session.commit()

            self.logger.info(f"Nuevo análisis creado para {id_clerk}: {id_analisis}")

            return {
                'id': id_analisis,
                'estado_procesamiento': 'pendiente'
            }

        except Exception as e:
            self.logger.error(f"Error en obtener_o_generar_analisis_diario: {str(e)}")
            db.session.rollback()
            raise

    def _detectar_cambios_significativos(self, datos_previos, datos_actuales):
        """
        Detecta si hay cambios significativos que justifiquen regenerar el consejo.
        
        Args:
            datos_previos: Datos anteriores recopilados
            datos_actuales: Datos actuales recopilados
            
        Returns:
            bool: True si hay cambios significativos
        """
        try:
            # Comparar tasa de éxito (cambio > 10%)
            tasa_anterior = datos_previos.get('resumen_hoy', {}).get('tasa_exito', 0)
            tasa_actual = datos_actuales.get('resumen_hoy', {}).get('tasa_exito', 0)
            
            if abs(tasa_actual - tasa_anterior) > 10:
                self.logger.info(f"Cambio en tasa de éxito: {tasa_anterior}% -> {tasa_actual}%")
                return True
            
            # Comparar hábitos completados
            habitos_anterior = datos_previos.get('resumen_hoy', {}).get('habitos_completados', 0)
            habitos_actual = datos_actuales.get('resumen_hoy', {}).get('habitos_completados', 0)
            
            if habitos_actual > habitos_anterior:
                self.logger.info(f"Más hábitos completados: {habitos_anterior} -> {habitos_actual}")
                return True
            
            # Comparar rachas (nueva racha rota o alcanzada)
            rachas_anterior = [r.get('dias_actuales', 0) for r in datos_previos.get('rachas_actuales', [])]
            rachas_actual = [r.get('dias_actuales', 0) for r in datos_actuales.get('rachas_actuales', [])]
            
            if len(rachas_actual) != len(rachas_anterior) or max(rachas_actual or [0]) != max(rachas_anterior or [0]):
                self.logger.info(f"Cambio en rachas detectado")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error en _detectar_cambios_significativos: {str(e)}")
            return False

    def recopilar_datos_usuario(self, id_clerk):
        """
        Recopila datos del usuario para enviar a IA.
        
        Args:
            id_clerk: ID del usuario en Clerk
            
        Returns:
            dict: Con datos del usuario, hábitos, estadísticas, etc.
        """
        try:
            hoy = date.today()
            hace_7_dias = date(hoy.year, hoy.month, hoy.day)
            
            # Obtener usuario
            usuario = User.query.filter_by(id_clerk=id_clerk).first()
            if not usuario:
                raise ValueError(f"Usuario no encontrado: {id_clerk}")

            # Obtener hábitos activos
            habitos = Habit.query.filter_by(
                id_propietario=id_clerk,
                archivado=False
            ).all()

            # Contar hábitos completados hoy
            registros_hoy = HabitEntry.query.filter(
                HabitEntry.id_clerk == id_clerk,
                func.date(HabitEntry.fecha) == hoy
            ).count()

            # Obtener estadísticas de la semana
            estadisticas_semana = []
            for habito in habitos:
                registros_semana = HabitEntry.query.filter(
                    HabitEntry.id_habito == habito.id,
                    HabitEntry.id_clerk == id_clerk,
                    func.date(HabitEntry.fecha) >= hace_7_dias,
                    func.date(HabitEntry.fecha) <= hoy
                ).count()

                dias_unicos_semana = db.session.query(
                    func.count(func.distinct(func.date(HabitEntry.fecha)))
                ).filter(
                    HabitEntry.id_habito == habito.id,
                    HabitEntry.id_clerk == id_clerk,
                    func.date(HabitEntry.fecha) >= hace_7_dias,
                    func.date(HabitEntry.fecha) <= hoy
                ).scalar() or 0

                tasa_exito = round((dias_unicos_semana / 7) * 100) if dias_unicos_semana > 0 else 0

                estadisticas_semana.append({
                    'habito_id': habito.id,
                    'titulo': habito.titulo,
                    'tipo': habito.tipo,
                    'dias_completados': dias_unicos_semana,
                    'tasa_exito_semana': tasa_exito
                })

            # Obtener rachas actuales
            rachas = HabitStreak.query.filter_by(id_clerk=id_clerk).all()
            rachas_actuales = [
                {
                    'dias_actuales': racha.racha_actual or 0,
                    'mejor_racha': racha.mejor_racha or 0,
                    'ultimo_registro': racha.ultima_fecha.isoformat() if racha.ultima_fecha else None
                }
                for racha in rachas
            ]

            datos = {
                'usuario': {
                    'id': id_clerk,
                    'nombre': usuario.nombre_completo or 'Usuario',
                    'idioma': usuario.idioma or 'es',
                    'zona_horaria': usuario.zona_horaria or 'America/Lima'
                },
                'resumen_hoy': {
                    'habitos_completados': registros_hoy,
                    'habitos_totales': len(habitos),
                    'tasa_exito': round((registros_hoy / len(habitos) * 100) if habitos else 0)
                },
                'estadisticas_semana': estadisticas_semana,
                'rachas_actuales': rachas_actuales,
                'habitos_totales': len(habitos),
                'fecha': datetime.now(pytz.UTC).isoformat()
            }

            return datos

        except Exception as e:
            self.logger.error(f"Error en recopilar_datos_usuario: {str(e)}")
            raise

    def generar_consejos_con_ia(self, id_analisis, id_clerk):
        """
        Genera consejos usando Google Gemini API.
        
        Args:
            id_analisis: ID del análisis
            id_clerk: ID del usuario en Clerk
            
        Returns:
            list: Lista de consejos generados
        """
        try:
            # Obtener análisis
            analisis = IAAnalisisDiario.query.filter_by(
                id=id_analisis,
                id_clerk=id_clerk
            ).first()

            if not analisis:
                raise ValueError("Análisis no encontrado")

            datos = json.loads(analisis.datos_enviados)
            prompt = self._construir_prompt(datos)

            # Llamar a Gemini
            self.logger.info(f"Llamando a Gemini para generar consejos...")
            response = self.model.generate_content(prompt)
            texto_respuesta = response.text

            # Parsear respuesta
            consejos = self._parsear_respuesta_ia(texto_respuesta)

            # Guardar respuesta en BD
            analisis.respuesta_ia = json.dumps(consejos, ensure_ascii=False)
            analisis.estado_procesamiento = 'procesado'
            db.session.commit()

            # Guardar consejos individuales
            for consejo_data in consejos:
                id_consejo = str(uuid4())
                ahora = datetime.now(pytz.UTC)

                consejo = IAConsejo(
                    id=id_consejo,
                    id_analisis=id_analisis,
                    id_clerk=id_clerk,
                    tipo_consejo=consejo_data['tipo'],
                    titulo=consejo_data['titulo'],
                    contenido=consejo_data['contenido'],
                    generado_en=ahora
                )
                db.session.add(consejo)

            db.session.commit()
            self.logger.info(f"Consejos generados exitosamente para {id_clerk}")

            return consejos

        except Exception as e:
            self.logger.error(f"Error en generar_consejos_con_ia: {str(e)}")
            analisis = IAAnalisisDiario.query.filter_by(id=id_analisis).first()
            if analisis:
                analisis.estado_procesamiento = 'error'
                analisis.error_mensaje = str(e)
                db.session.commit()
            db.session.rollback()
            raise

    def _construir_prompt(self, datos):
        """
        Construye el prompt para enviar a Gemini.
        
        Args:
            datos: Datos del usuario
            
        Returns:
            str: Prompt formateado
        """
        estadisticas_semana_str = "\n".join([
            f"- {e['titulo']} ({e['tipo']}): {e['dias_completados']}/7 días ({e['tasa_exito_semana']}%)"
            for e in datos.get('estadisticas_semana', [])
        ])

        rachas_str = "\n".join([
            f"- Racha: {r['dias_actuales']} días (mejor racha: {r['mejor_racha']})"
            for r in datos.get('rachas_actuales', [])
        ]) or "Sin rachas activas"

        idioma_completo = "ESPAÑOL" if datos['usuario'].get('idioma') == 'es' else "INGLÉS"

        prompt = f"""Eres un coach de hábitos experto, motivador y empático. Analiza los siguientes datos del usuario y genera consejos personalizados y accionables.

DATOS DEL USUARIO:
- Nombre: {datos['usuario']['nombre']}
- Idioma: {datos['usuario']['idioma']}
- Zona horaria: {datos['usuario']['zona_horaria']}
- Hábitos totales: {datos['habitos_totales']}

RESUMEN DE HOY:
- Hábitos completados: {datos['resumen_hoy']['habitos_completados']}/{datos['resumen_hoy']['habitos_totales']}
- Tasa de éxito: {datos['resumen_hoy']['tasa_exito']}%

ESTADÍSTICAS DE LA SEMANA:
{estadisticas_semana_str}

RACHAS ACTUALES:
{rachas_str}

INSTRUCCIONES IMPORTANTES:
1. Genera 1-3 consejos específicos, personalizados y accionables basados en los datos reales
2. Usa emojis para hacer el contenido más atractivo
3. Sé empático, motivador pero realista
4. Responde OBLIGATORIAMENTE en {idioma_completo}
5. Los consejos deben ser útiles y fáciles de implementar
6. NO hagas consejos genéricos

FORMATO DE RESPUESTA (IMPORTANTE - Devuelve SOLO un JSON válido):
{{
  "consejos": [
    {{
      "tipo": "motivacion|mejora_habito|nuevo_habito|ruptura_racha|felicitacion",
      "titulo": "Título corto y atractivo",
      "contenido": "Contenido en Markdown. Puede incluir emojis, saltos de línea (\\n), **texto en negrita**, y viñetas con - o *."
    }}
  ]
}}

Recuerda: Devuelve SOLO el JSON sin comentarios, sin comillas de apertura extra, sin código markdown. El JSON debe ser válido y parseable."""

        return prompt

    def _parsear_respuesta_ia(self, texto):
        """
        Parsea la respuesta de Gemini y extrae los consejos.
        
        Args:
            texto: Texto de respuesta de Gemini
            
        Returns:
            list: Lista de consejos válidos
        """
        try:
            # Buscar JSON en la respuesta
            import re
            json_match = re.search(r'\{[\s\S]*\}', texto)

            if not json_match:
                self.logger.warning("No se encontró JSON en la respuesta de IA")
                return self._crear_consejo_default()

            json_str = json_match.group(0)
            datos = json.loads(json_str)

            if not isinstance(datos.get('consejos'), list):
                return self._crear_consejo_default()

            # Validar y limpiar consejos
            consejos_validos = []
            tipos_validos = {'motivacion', 'mejora_habito', 'nuevo_habito', 'ruptura_racha', 'felicitacion'}

            for c in datos['consejos']:
                if (c.get('tipo') in tipos_validos and 
                    c.get('titulo') and 
                    c.get('contenido')):
                    consejos_validos.append({
                        'tipo': c['tipo'],
                        'titulo': c['titulo'],
                        'contenido': c['contenido']
                    })

            return consejos_validos[:3]  # Máximo 3 consejos

        except Exception as e:
            self.logger.error(f"Error al parsear respuesta de IA: {str(e)}")
            return self._crear_consejo_default()

    def _crear_consejo_default(self):
        """
        Crea un consejo por defecto en caso de error.
        
        Returns:
            list: Consejo por defecto
        """
        return [
            {
                'tipo': 'motivacion',
                'titulo': '¡Sigue adelante!',
                'contenido': '### 💪 ¡Estás haciendo un gran trabajo!\n\nCada día que trabajas en tus hábitos te acerca a tu mejor versión.\n\nNo importa si hoy no fue perfecto, lo importante es que estás aquí intentando.\n\n**Recuerda:** El progreso no es lineal. ¡Vuelve a intentarlo mañana!'
            }
        ]

    def obtener_consejos_del_dia(self, id_clerk):
        """
        Obtiene los consejos del día actual para el usuario, considerando su zona horaria.
        
        Args:
            id_clerk: ID del usuario en Clerk
            
        Returns:
            list: Lista de consejos
        """
        try:
            # Obtener usuario y su zona horaria
            usuario = User.query.filter_by(id_clerk=id_clerk).first()
            if not usuario:
                raise ValueError(f"Usuario {id_clerk} no encontrado")
            
            # Obtener la fecha actual del usuario en su zona horaria
            from services.timezone_service import TimezoneService
            tz_service = TimezoneService()
            fecha_usuario = tz_service.get_user_local_date(id_clerk)
            
            self.logger.info(f"Obteniendo consejos para {id_clerk} del día {fecha_usuario} (zona: {usuario.zona_horaria})")

            # Obtener todos los consejos del usuario (sin filtrar por fecha aquí)
            consejos_db = IAConsejo.query.filter_by(
                id_clerk=id_clerk
            ).order_by(IAConsejo.generado_en.desc()).all()
            
            # Filtrar por fecha convertida a zona horaria del usuario
            consejos_filtrados = []
            for c in consejos_db:
                fecha_consejo_local = tz_service.to_user_timezone(c.generado_en, id_clerk)
                fecha_consejo = fecha_consejo_local.date() if hasattr(fecha_consejo_local, 'date') else fecha_consejo_local
                
                if fecha_consejo == fecha_usuario:
                    consejos_filtrados.append(c)

            return [
                {
                    'id': c.id,
                    'tipo': c.tipo_consejo,
                    'titulo': c.titulo,
                    'contenido': c.contenido,
                    'leido': c.leido,
                    'generado_en': c.generado_en.isoformat()
                }
                for c in consejos_filtrados
            ]

        except Exception as e:
            self.logger.error(f"Error en obtener_consejos_del_dia: {str(e)}")
            raise

    def marcar_consejo_como_leido(self, id_consejo, id_clerk):
        """
        Marca un consejo como leído.
        
        Args:
            id_consejo: ID del consejo
            id_clerk: ID del usuario en Clerk
            
        Returns:
            bool: True si se actualizó
        """
        try:
            consejo = IAConsejo.query.filter_by(
                id=id_consejo,
                id_clerk=id_clerk
            ).first()

            if not consejo:
                raise ValueError("Consejo no encontrado o sin permiso")

            consejo.leido = True
            consejo.fecha_lectura = datetime.now(pytz.UTC)
            db.session.commit()

            self.logger.info(f"Consejo {id_consejo} marcado como leído")
            return True

        except Exception as e:
            self.logger.error(f"Error en marcar_consejo_como_leido: {str(e)}")
            db.session.rollback()
            raise

    def registrar_interaccion(self, id_consejo, id_clerk, accion):
        """
        Registra la interacción del usuario con un consejo.
        
        Args:
            id_consejo: ID del consejo
            id_clerk: ID del usuario en Clerk
            accion: Tipo de acción ('visto', 'archivado', 'seguido', 'ignorado')
            
        Returns:
            bool: True si se registró
        """
        try:
            acciones_validas = {'visto', 'archivado', 'seguido', 'ignorado'}

            if accion not in acciones_validas:
                raise ValueError(f"Acción inválida: {accion}")

            # Verificar que el consejo existe y pertenece al usuario
            consejo = IAConsejo.query.filter_by(
                id=id_consejo,
                id_clerk=id_clerk
            ).first()

            if not consejo:
                raise ValueError("Consejo no encontrado o sin permiso")

            # Registrar interacción
            id_interaccion = str(uuid4())
            interaccion = IAConsejoInteraccion(
                id=id_interaccion,
                id_consejo=id_consejo,
                id_clerk=id_clerk,
                accion=accion
            )

            db.session.add(interaccion)
            db.session.commit()

            self.logger.info(f"Interacción registrada: {id_consejo} - {accion}")
            return True

        except Exception as e:
            self.logger.error(f"Error en registrar_interaccion: {str(e)}")
            db.session.rollback()
            raise

    def generar_sugerencias_habitos(self, id_clerk, input_usuario):
        """
        Genera sugerencias de hábitos usando Google Gemini API.
        
        Args:
            id_clerk: ID del usuario en Clerk
            input_usuario: Input proporcionado por el usuario (meta o descripción)
            
        Returns:
            dict: Sugerencias de hábitos
        """
        try:
            # Obtener información del usuario
            usuario = User.query.filter_by(id_clerk=id_clerk).first()
            if not usuario:
                raise ValueError("Usuario no encontrado")

            # Obtener hábitos actuales del usuario
            habitos_hacer, habitos_dejar = self._obtener_habitos_usuario(id_clerk)

            idioma = usuario.idioma or 'es'
            idioma_completo = "ESPAÑOL" if idioma == 'es' else "INGLÉS"

            # Construir prompt
            prompt = self._construir_prompt_sugerencias(input_usuario, habitos_hacer, habitos_dejar, idioma_completo)

            # Llamar a Gemini
            self.logger.info(f"Llamando a Gemini para generar sugerencias de hábitos...")
            response = self.model.generate_content(prompt)
            texto_respuesta = response.text

            # Parsear respuesta
            sugerencias = self._parsear_respuesta_sugerencias(texto_respuesta)

            self.logger.info(f"Sugerencias generadas exitosamente para {id_clerk}")

            return sugerencias

        except Exception as e:
            self.logger.error(f"Error en generar_sugerencias_habitos: {str(e)}")
            raise

    def _obtener_habitos_usuario(self, id_clerk):
        """
        Obtiene los hábitos activos del usuario separados por tipo.
        
        Args:
            id_clerk: ID del usuario en Clerk
            
        Returns:
            tuple: (habitos_hacer, habitos_dejar) - listas de strings
        """
        try:
            # Consultar hábitos activos (no archivados) del usuario
            habitos = Habit.query.filter_by(
                id_propietario=id_clerk,
                archivado=False
            ).all()

            habitos_hacer = []
            habitos_dejar = []

            for habito in habitos:
                if habito.tipo == 'hacer':
                    habitos_hacer.append(habito.titulo)
                elif habito.tipo == 'dejar':
                    habitos_dejar.append(habito.titulo)

            self.logger.info(f"Hábitos encontrados para {id_clerk}: {len(habitos_hacer)} hacer, {len(habitos_dejar)} dejar")
            
            return habitos_hacer, habitos_dejar

        except Exception as e:
            self.logger.error(f"Error obteniendo hábitos del usuario {id_clerk}: {str(e)}")
            return [], []

    def _construir_prompt_sugerencias(self, input_usuario, habitos_hacer, habitos_dejar, idioma_completo):
        """
        Construye el prompt para sugerencias de hábitos.
        
        Args:
            input_usuario: Input proporcionado por el usuario
            habitos_hacer: Lista de hábitos a hacer
            habitos_dejar: Lista de hábitos a dejar
            idioma_completo: Idioma para la respuesta
            
        Returns:
            str: Prompt formateado
        """
        habitos_hacer_str = "\n".join([f"- {h}" for h in habitos_hacer]) if habitos_hacer else "Ninguno"
        habitos_dejar_str = "\n".join([f"- {h}" for h in habitos_dejar]) if habitos_dejar else "Ninguno"

        prompt = f"""Eres un asistente especializado en diseño de hábitos diarios para una aplicación de seguimiento de hábitos.

El usuario proporcionará:
- Una meta general.
- Una lista de hábitos actuales, divididos en "Hacer" y "Dejar de hacer".

Tu tarea es convertir la meta en hábitos diarios simples, sostenibles y fácilmente marcables, tomando en cuenta los hábitos que el usuario ya realiza o intenta evitar.

REGLAS OBLIGATORIAS:
- No hagas preguntas ni solicites aclaraciones.
- Usa la meta únicamente para inferir el área de vida (salud, productividad, bienestar, etc.).
- Diseña hábitos mínimos que puedan realizarse incluso en un mal día.
- Prioriza acciones diarias, no resultados ni objetivos finales.
- Cada hábito debe poder completarse en pocos minutos.
- Cada hábito debe poder marcarse como "hecho" o "no hecho".
- No repitas hábitos existentes; crea hábitos complementarios o ajustes naturales.
- Evita lenguaje motivacional, inspiracional o teórico.

CRITERIOS DE DISEÑO:
- Traduce la meta en beneficios cotidianos implícitos (energía, claridad, calma, enfoque).
- Asume obstáculos comunes sin mencionarlos explícitamente.
- Comienza siempre con la versión de menor esfuerzo posible.
- Diseña hábitos que sigan siendo útiles incluso después de alcanzar la meta.
- Los hábitos propuestos deben integrarse sin conflicto con los hábitos actuales.

ENTRADA DEL USUARIO:
Meta:
"{input_usuario}"

Hábitos actuales — Hacer:
{habitos_hacer_str}

Hábitos actuales — Dejar de hacer:
{habitos_dejar_str}

FORMATO DE SALIDA:
- Genera entre 3 y 5 hábitos en total.
- Divide los hábitos en "hacer" y "dejar" solo si corresponde.
- Usa frases cortas, claras y accionables.
- No menciones la meta, identidad personal ni conceptos psicológicos.

IDIOMA:
Responde obligatoriamente en {idioma_completo}.

FORMATO DE RESPUESTA (OBLIGATORIO):
Devuelve ÚNICAMENTE un JSON válido, sin texto adicional, sin markdown y sin comentarios.

Estructura exacta:
{{
  "hacer": ["hábito 1", "hábito 2"],
  "dejar": ["hábito 1", "hábito 2"]
}}

El JSON debe ser completamente válido y parseable."""

        return prompt

    def _parsear_respuesta_sugerencias(self, texto):
        """
        Parsea la respuesta de Gemini para sugerencias de hábitos.
        
        Args:
            texto: Texto de respuesta de Gemini
            
        Returns:
            dict: Sugerencias parseadas
        """
        try:
            # Buscar JSON en la respuesta
            import re
            json_match = re.search(r'\{[\s\S]*\}', texto)

            if not json_match:
                self.logger.warning("No se encontró JSON en la respuesta de sugerencias")
                return {"hacer": [], "dejar": []}

            json_str = json_match.group(0)
            datos = json.loads(json_str)

            # Validar estructura
            hacer = datos.get('hacer', [])
            dejar = datos.get('dejar', [])

            if not isinstance(hacer, list) or not isinstance(dejar, list):
                return {"hacer": [], "dejar": []}

            return {
                "hacer": [str(h) for h in hacer if h],
                "dejar": [str(d) for d in dejar if d]
            }

        except Exception as e:
            self.logger.error(f"Error al parsear respuesta de sugerencias: {str(e)}")
            return {"hacer": [], "dejar": []}
