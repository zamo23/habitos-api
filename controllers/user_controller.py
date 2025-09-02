from flask import request, jsonify, g
from models import db, User
from services.auth_service import auth_required
from services.timezone_service import get_user_local_date
from sqlalchemy import text
from datetime import datetime, timedelta
import pytz

@auth_required
def me():
    """Obtener información del usuario autenticado"""
    user = g.current_user
    return jsonify({
        'id_clerk': user.id_clerk,
        'correo': user.correo,
        'nombre_completo': user.nombre_completo,
        'url_imagen': user.url_imagen,
        'idioma': user.idioma,
        'zona_horaria': getattr(user, 'zona_horaria', 'America/Lima'),
        'cierre_dia_hora': getattr(user, 'cierre_dia_hora', 0)
    })

@auth_required
def update_me():
    """Actualizar información del usuario"""
    user = g.current_user
    data = request.get_json()
    
    # Lista de zonas horarias válidas comunes
    valid_timezones = [
        'America/Lima', 'America/Bogota', 'America/Mexico_City', 'America/Buenos_Aires',
        'America/Santiago', 'America/Caracas', 'America/New_York', 'America/Los_Angeles',
        'Europe/Madrid', 'Europe/London', 'Asia/Tokyo', 'Australia/Sydney',
        'UTC', 'America/Sao_Paulo', 'America/Montevideo', 'America/La_Paz'
    ]
    
    if 'zona_horaria' in data:
        timezone = data['zona_horaria']
        if timezone in valid_timezones:
            try:
                # Verificar que la zona horaria sea válida
                pytz.timezone(timezone)
                user.zona_horaria = timezone
            except pytz.exceptions.UnknownTimeZoneError:
                return jsonify({'error': {'code': 'invalid_timezone', 'message': 'Zona horaria inválida'}}), 422
        else:
            return jsonify({'error': {'code': 'invalid_timezone', 'message': 'Zona horaria no soportada'}}), 422
    
    if 'cierre_dia_hora' in data:
        hour = data['cierre_dia_hora']
        if isinstance(hour, int) and 0 <= hour <= 23:
            user.cierre_dia_hora = hour
        else:
            return jsonify({'error': {'code': 'invalid_hour', 'message': 'Hora debe ser entre 0 y 23'}}), 422
    
    if 'idioma' in data and data['idioma'] in ['es', 'en']:
        user.idioma = data['idioma']
    
    if 'nombre_completo' in data:
        user.nombre_completo = data['nombre_completo']
    
    db.session.commit()
    
    return jsonify({
        'id_clerk': user.id_clerk,
        'correo': user.correo,
        'nombre_completo': user.nombre_completo,
        'url_imagen': user.url_imagen,
        'idioma': user.idioma,
        'zona_horaria': user.zona_horaria,
        'cierre_dia_hora': user.cierre_dia_hora
    })

@auth_required
def get_local_time():
    """Obtener información de fecha y hora local del usuario"""
    hoy_local = get_user_local_date(g.current_user.id_clerk)
    
    # Get timezone info
    user = g.current_user
    timezone_name = getattr(user, 'zona_horaria', 'America/Lima')
    closure_hour = getattr(user, 'cierre_dia_hora', 0)
    
    try:
        tz = pytz.timezone(timezone_name)
        now_local = datetime.now(tz)
        
        return jsonify({
            'fecha_local': hoy_local.isoformat(),
            'hora_local': now_local.strftime('%H:%M:%S'),
            'zona_horaria': timezone_name,
            'cierre_dia_hora': closure_hour,
            'timestamp': now_local.isoformat()
        })
    except pytz.exceptions.UnknownTimeZoneError:
        return jsonify({'error': {'code': 'invalid_timezone', 'message': 'Zona horaria configurada inválida'}}), 500

@auth_required
def get_recent_activity():
    """Obtener la actividad reciente del usuario en los últimos 7 días"""
    user = g.current_user
    dias_recientes = 7  # Predeterminado a 7 días
    
    # Query SQL para obtener la actividad reciente
    sql = text("""
        SELECT 
            u.id_clerk,
            u.nombre_completo,
            h.titulo AS habito,
            r.fecha,
            r.estado,
            r.comentario,
            r.fecha_creacion AS registrado_en
        FROM habito_registros r
        JOIN habitos h ON h.id = r.id_habito
        JOIN usuarios u ON u.id_clerk = r.id_clerk
        WHERE u.id_clerk = :user_id
          AND r.fecha >= CURDATE() - INTERVAL :dias DAY
        ORDER BY r.fecha DESC, r.fecha_creacion DESC
    """)
    
    result = db.session.execute(sql, {
        'user_id': user.id_clerk,
        'dias': dias_recientes
    })
    
    # Convertir los resultados a una lista de diccionarios
    actividades = []
    for row in result:
        actividades.append({
            'id_clerk': row.id_clerk,
            'nombre_completo': row.nombre_completo,
            'habito': row.habito,
            'fecha': row.fecha.isoformat(),
            'estado': row.estado,
            'comentario': row.comentario,
            'registrado_en': row.registrado_en.isoformat() if row.registrado_en else None
        })
    
    return jsonify({
        'dias_recientes': dias_recientes,
        'total_registros': len(actividades),
        'actividades': actividades
    })

def get_timezones():
    """Obtener lista de zonas horarias disponibles"""
    timezones = [
        {'value': 'UTC', 'label': 'UTC (Tiempo Universal Coordinado)', 'offset': '+00:00'},
        {'value': 'America/Lima', 'label': 'Lima, Perú (PET)', 'offset': '-05:00'},
        {'value': 'America/Bogota', 'label': 'Bogotá, Colombia (COT)', 'offset': '-05:00'},
        {'value': 'America/Mexico_City', 'label': 'Ciudad de México (CST)', 'offset': '-06:00'},
        {'value': 'America/Buenos_Aires', 'label': 'Buenos Aires, Argentina (ART)', 'offset': '-03:00'},
        {'value': 'America/Santiago', 'label': 'Santiago, Chile (CLT)', 'offset': '-03:00'},
        {'value': 'America/Caracas', 'label': 'Caracas, Venezuela (VET)', 'offset': '-04:00'},
        {'value': 'America/Sao_Paulo', 'label': 'São Paulo, Brasil (BRT)', 'offset': '-03:00'},
        {'value': 'America/Montevideo', 'label': 'Montevideo, Uruguay (UYT)', 'offset': '-03:00'},
        {'value': 'America/La_Paz', 'label': 'La Paz, Bolivia (BOT)', 'offset': '-04:00'},
        {'value': 'America/New_York', 'label': 'Nueva York, EE.UU. (EST)', 'offset': '-05:00'},
        {'value': 'America/Los_Angeles', 'label': 'Los Ángeles, EE.UU. (PST)', 'offset': '-08:00'},
        {'value': 'Europe/Madrid', 'label': 'Madrid, España (CET)', 'offset': '+01:00'},
        {'value': 'Europe/London', 'label': 'Londres, Reino Unido (GMT)', 'offset': '+00:00'},
        {'value': 'Asia/Tokyo', 'label': 'Tokio, Japón (JST)', 'offset': '+09:00'},
        {'value': 'Australia/Sydney', 'label': 'Sídney, Australia (AEST)', 'offset': '+10:00'}
    ]
    
    return jsonify(timezones)

def detect_timezone():
    """Detectar zona horaria basada en offset del cliente"""
    data = request.get_json()
    offset_minutes = data.get('offset_minutes')  # Offset en minutos desde UTC
    
    if offset_minutes is None:
        return jsonify({'error': {'code': 'missing_offset', 'message': 'offset_minutes requerido'}}), 422
    
    # Mapear algunos offsets comunes a zonas horarias
    offset_to_timezone = {
        0: 'UTC',
        -300: 'America/Lima',      # UTC-5
        -360: 'America/Mexico_City', # UTC-6
        -180: 'America/Buenos_Aires', # UTC-3
        -240: 'America/Caracas',    # UTC-4
        60: 'Europe/Madrid',        # UTC+1
        540: 'Asia/Tokyo',          # UTC+9
        600: 'Australia/Sydney'     # UTC+10
    }
    
    suggested_timezone = offset_to_timezone.get(offset_minutes, 'America/Lima')
    
    return jsonify({
        'suggested_timezone': suggested_timezone,
        'offset_minutes': offset_minutes
    })

@auth_required
def get_activity_heatmap():
    """Obtener datos para el heatmap de actividad al estilo GitHub"""
    user = g.current_user
    semanas = request.args.get('weeks', '53')  # Por defecto 53 semanas (1 año + 1 semana extra como GitHub)
    
    try:
        semanas = int(semanas)
        if semanas < 1:
            raise ValueError
    except ValueError:
        return jsonify({'error': {'code': 'invalid_weeks', 'message': 'El número de semanas debe ser un entero positivo'}}), 422
    
    # Query SQL para generar el heatmap
    sql = text("""
        WITH RECURSIVE cal AS (
            SELECT DATE_SUB(
                -- Comenzar desde el domingo de la semana actual
                DATE_SUB(CURDATE(), INTERVAL (DAYOFWEEK(CURDATE()) - 1) DAY),
                -- Retroceder 53 semanas (1 año + 1 semana) para asegurar cobertura completa
                INTERVAL 52 WEEK
            ) AS d
            UNION ALL
            SELECT DATE_ADD(d, INTERVAL 1 DAY) 
            FROM cal 
            WHERE d < CURDATE()
        ),
        agg AS (
            SELECT fecha, SUM(estado = 'exito') AS exitos
            FROM habito_registros
            WHERE id_clerk = :user_id
                AND fecha BETWEEN (
                    SELECT MIN(d) FROM cal
                ) AND CURDATE()
            GROUP BY fecha
        )
        SELECT
            (DAYOFWEEK(c.d) + 6) % 7 AS day_of_week_0_sun,
            TIMESTAMPDIFF(
                WEEK,
                (SELECT MIN(d) FROM cal),
                c.d
            ) AS week_index,
            COALESCE(a.exitos, 0) AS valor,
            c.d AS fecha
        FROM cal c
        LEFT JOIN agg a ON a.fecha = c.d
        ORDER BY week_index, day_of_week_0_sun;
    """)
    
    result = db.session.execute(sql, {
        'user_id': user.id_clerk,
        'weeks': semanas
    })
    
    # Convertir resultados a formato de heatmap
    heatmap_data = []
    current_week = None
    week_data = None
    
    for row in result:
        week_index = row.week_index
        
        if current_week != week_index:
            if week_data:
                heatmap_data.append(week_data)
            current_week = week_index
            week_data = {
                'week_index': week_index,
                'days': []
            }
        
        week_data['days'].append({
            'day_of_week': row.day_of_week_0_sun,
            'value': row.valor,
            'date': row.fecha.isoformat()
        })
    
    # Agregar la última semana
    if week_data:
        heatmap_data.append(week_data)
    
    # Calcular estadísticas
    total_dias = sum(len(week['days']) for week in heatmap_data)
    dias_con_actividad = sum(
        1 for week in heatmap_data
        for day in week['days']
        if day['value'] > 0
    )
    total_exitos = sum(
        day['value']
        for week in heatmap_data
        for day in week['days']
    )
    
    # Calcular fechas de inicio y fin del periodo
    fecha_inicio = min(
        day['date']
        for week in heatmap_data
        for day in week['days']
    ) if heatmap_data and heatmap_data[0]['days'] else None
    
    fecha_fin = max(
        day['date']
        for week in heatmap_data
        for day in week['days']
    ) if heatmap_data and heatmap_data[-1]['days'] else None
    
    return jsonify({
        'periodo_semanas': 53,  # Siempre 53 semanas (1 año + 1 semana extra)
        'rango_fechas': {
            'inicio': fecha_inicio,
            'fin': fecha_fin
        },
        'estadisticas': {
            'total_dias': total_dias,
            'dias_con_actividad': dias_con_actividad,
            'total_exitos': total_exitos,
            'porcentaje_actividad': round(dias_con_actividad * 100 / total_dias if total_dias > 0 else 0, 1),
            'promedio_diario': round(total_exitos / total_dias if total_dias > 0 else 0, 2),
            'mejor_dia': max(
                (day['value'] for week in heatmap_data for day in week['days']),
                default=0
            )
        },
        'heatmap': heatmap_data
    })

@auth_required
def get_habit_summary():
    """Obtener resumen acumulado de hábitos por periodo"""
    user = g.current_user
    semanas_atras = request.args.get('weeks', '8')  # Por defecto 8 semanas
    include_archived = request.args.get('include_archived', '0') == '1'
    
    try:
        semanas_atras = int(semanas_atras)
        if semanas_atras < 1:
            raise ValueError
    except ValueError:
        return jsonify({'error': {'code': 'invalid_weeks', 'message': 'El número de semanas debe ser un entero positivo'}}), 422
    
    # Query SQL para obtener resumen acumulado por hábito
    sql = text("""
        SELECT
            u.id_clerk,
            h.id AS id_habito,
            h.titulo AS habito,
            SUM(r.estado = 'exito') AS exitos,
            SUM(r.estado = 'fallo') AS fallos,
            COUNT(*) AS total_registros,
            ROUND(AVG(r.estado = 'exito') * 100, 1) AS tasa_exito_pct
        FROM habito_registros r
        JOIN usuarios u ON u.id_clerk = r.id_clerk
        JOIN habitos h ON h.id = r.id_habito
        WHERE u.id_clerk = :user_id
        AND r.fecha >= DATE_SUB(CURDATE(), INTERVAL :weeks WEEK)
        """ + ('' if include_archived else 'AND h.archivado = 0') + """
        GROUP BY u.id_clerk, h.id, h.titulo
        ORDER BY h.titulo
    """)
    
    result = db.session.execute(sql, {
        'user_id': user.id_clerk,
        'weeks': semanas_atras
    })
    
    # Convertir resultados a lista de diccionarios
    habitos_resumen = []
    for row in result:
        habitos_resumen.append({
            'id_habito': row.id_habito,
            'titulo': row.habito,
            'estadisticas': {
                'exitos': row.exitos,
                'fallos': row.fallos,
                'total_registros': row.total_registros,
                'tasa_exito': float(row.tasa_exito_pct)
            }
        })
    
    return jsonify({
        'periodo_semanas': semanas_atras,
        'total_habitos': len(habitos_resumen),
        'habitos': habitos_resumen
    })

@auth_required
def get_weekly_progress():
    """Obtener el resumen acumulado de hábitos por periodo"""
    user = g.current_user
    semanas_atras = request.args.get('weeks', '8')  # Por defecto 8 semanas
    try:
        semanas_atras = int(semanas_atras)
        if semanas_atras < 1:
            raise ValueError
    except ValueError:
        return jsonify({'error': {'code': 'invalid_weeks', 'message': 'El número de semanas debe ser un entero positivo'}}), 422
    
    # Obtener parámetro para incluir archivados
    include_archived = request.args.get('include_archived', '0') == '1'
    
    # Query SQL para obtener resumen acumulado por hábito
    sql = text("""
        SELECT
            u.id_clerk,
            h.id AS id_habito,
            h.titulo AS habito,
            SUM(r.estado = 'exito') AS exitos,
            SUM(r.estado = 'fallo') AS fallos,
            COUNT(*) AS total_registros,
            ROUND(AVG(r.estado = 'exito') * 100, 1) AS tasa_exito_pct
        FROM habito_registros r
        JOIN usuarios u ON u.id_clerk = r.id_clerk
        JOIN habitos h ON h.id = r.id_habito
        WHERE u.id_clerk = :user_id
        AND r.fecha >= DATE_SUB(CURDATE(), INTERVAL :weeks WEEK)
        """ + ('' if include_archived else 'AND h.archivado = 0') + """
        GROUP BY u.id_clerk, h.id, h.titulo
        ORDER BY h.titulo
    """)
    
    result = db.session.execute(sql, {
        'user_id': user.id_clerk,
        'weeks': semanas_atras
    })
    
    # Convertir resultados a lista de diccionarios
    habitos_resumen = []
    for row in result:
        habitos_resumen.append({
            'id_habito': row.id_habito,
            'titulo': row.habito,
            'estadisticas': {
                'exitos': row.exitos,
                'fallos': row.fallos,
                'total_registros': row.total_registros,
                'tasa_exito': float(row.tasa_exito_pct)
            }
        })
    
    return jsonify({
        'periodo_semanas': semanas_atras,
        'total_habitos': len(habitos_resumen),
        'habitos': habitos_resumen
    })