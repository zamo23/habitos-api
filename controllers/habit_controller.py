from services.timezone_service import format_datetime, to_user_timezone, get_user_local_date
from flask import request, jsonify, g
from models import db, Habit, HabitEntry, HabitStreak, GroupMember
from services.auth_service import auth_required
from services.date_service import parse_date
from services.habit_service import calculate_streak, update_streak_on_entry, user_has_access_to_habit, can_edit_habit, get_habit_recent_entries
from sqlalchemy import or_, text
import uuid
from datetime import timedelta
from datetime import datetime
import pytz

from services.subscription_service import check_habit_limit

@auth_required
def get_habits():
    """Obtener hábitos del usuario"""
    tipo = request.args.get('tipo')
    estado = request.args.get('estado', 'activos')
    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 20)), 100)
    
    query = db.session.query(Habit).filter(
        or_(
            Habit.id_propietario == g.current_user.id_clerk,
            Habit.id_grupo.in_(
                db.session.query(GroupMember.id_grupo).filter_by(id_clerk=g.current_user.id_clerk)
            )
        )
    )
    
    if tipo:
        query = query.filter(Habit.tipo == tipo)
    
    if estado == 'activos':
        query = query.filter(Habit.archivado == False)
    elif estado == 'archivados':
        query = query.filter(Habit.archivado == True)
    
    habits = query.offset((page - 1) * limit).limit(limit).all()
    hoy_local = get_user_local_date(g.current_user.id_clerk)
    
    result = []
    for habit in habits:
        rachas = calculate_streak(habit.id, g.current_user.id_clerk)

        registro_hoy = HabitEntry.query.filter_by(
            id_habito=habit.id,
            id_clerk=g.current_user.id_clerk,
            fecha=hoy_local
        ).first()
        
        habit_data = {
            'id': habit.id,
            'titulo': habit.titulo,
            'tipo': habit.tipo,
            'archivado': habit.archivado,
            'es_grupal': habit.id_grupo is not None,
            'rachas': rachas,
            'registro_hoy': {
                'completado': registro_hoy is not None,
                'estado': registro_hoy.estado if registro_hoy else None,
                'comentario': registro_hoy.comentario if registro_hoy else None,
                'puede_registrar': registro_hoy is None,
                'fecha_local_usuario': hoy_local.isoformat()
            }
        }
        
        if habit.group:
            habit_data['grupo'] = {
                'id': habit.group.id,
                'nombre': habit.group.nombre
            }
        
        result.append(habit_data)
    
    return jsonify(result)

@auth_required
def create_habit():
    """Crear un nuevo hábito"""
    data = request.get_json()
    titulo = data.get('titulo')
    tipo = data.get('tipo')
    id_grupo = data.get('id_grupo')
    
    if not titulo or tipo not in ['hacer', 'dejar']:
        return jsonify({'error': {'code': 'validation_error', 'message': 'Datos inválidos'}}), 422
    
    result = check_habit_limit(g.current_user.id_clerk, id_grupo)
    if result.get('error'):
        return jsonify({'error': result['error']}), 403
    
    habit = Habit(
        titulo=titulo,
        tipo=tipo,
        id_propietario=g.current_user.id_clerk,
        id_grupo=id_grupo
    )
    
    db.session.add(habit)
    db.session.commit()
    
    return jsonify({
        'id': habit.id,
        'titulo': habit.titulo,
        'tipo': habit.tipo,
        'archivado': habit.archivado,
        'es_grupal': habit.id_grupo is not None
    }), 201

@auth_required
def get_habit(habit_id):
    """Obtener detalles de un hábito específico"""
    habit = Habit.query.get_or_404(habit_id)
    
    if not user_has_access_to_habit(habit_id, g.current_user.id_clerk):
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin acceso'}}), 403
    
    rachas = calculate_streak(habit.id, g.current_user.id_clerk)
    hoy_local = get_user_local_date(g.current_user.id_clerk)
    
    registro_hoy = HabitEntry.query.filter_by(
        id_habito=habit.id,
        id_clerk=g.current_user.id_clerk,
        fecha=hoy_local
    ).first()
    
    result = {
        'id': habit.id,
        'titulo': habit.titulo,
        'tipo': habit.tipo,
        'archivado': habit.archivado,
        'rachas_usuario': rachas,
        'registro_hoy': {
            'completado': registro_hoy is not None,
            'estado': registro_hoy.estado if registro_hoy else None,
            'comentario': registro_hoy.comentario if registro_hoy else None,
            'puede_registrar': registro_hoy is None,
            'fecha_local_usuario': hoy_local.isoformat()
        }
    }
    
    if habit.group:
        result['grupo'] = {
            'id': habit.group.id,
            'nombre': habit.group.nombre
        }
    
    return jsonify(result)

@auth_required
def get_habit_details(habit_id):
    """Obtener detalles completos de un hábito específico"""
    habit = Habit.query.get_or_404(habit_id)
    
    if not user_has_access_to_habit(habit_id, g.current_user.id_clerk):
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin acceso al hábito'}}), 403
    
    hoy_local = get_user_local_date(g.current_user.id_clerk)
    rachas = calculate_streak(habit.id, g.current_user.id_clerk)
    total_registros = HabitEntry.query.filter_by(
        id_habito=habit.id,
        id_clerk=g.current_user.id_clerk
    ).count()
    
    total_exitos = HabitEntry.query.filter_by(
        id_habito=habit.id,
        id_clerk=g.current_user.id_clerk,
        estado='exito'
    ).count()
    
    total_fallos = HabitEntry.query.filter_by(
        id_habito=habit.id,
        id_clerk=g.current_user.id_clerk,
        estado='fallo'
    ).count()
    
    tasa_exito = (total_exitos / total_registros * 100) if total_registros > 0 else 0
    
    registros_recientes = HabitEntry.query.filter_by(
        id_habito=habit.id,
        id_clerk=g.current_user.id_clerk
    ).order_by(HabitEntry.fecha.desc()).limit(10).all()
    
    registro_hoy = HabitEntry.query.filter_by(
        id_habito=habit.id,
        id_clerk=g.current_user.id_clerk,
        fecha=hoy_local
    ).first()
    
    primer_registro = HabitEntry.query.filter_by(
        id_habito=habit.id,
        id_clerk=g.current_user.id_clerk
    ).order_by(HabitEntry.fecha.asc()).first()

    dias_desde_creacion = (hoy_local - habit.fecha_creacion.date()).days
    dias_desde_primer_registro = (hoy_local - primer_registro.fecha).days if primer_registro else None
    
    promedio_semanal = 0
    if primer_registro and dias_desde_primer_registro > 0:
        semanas_activas = max(1, dias_desde_primer_registro / 7)
        promedio_semanal = round(total_registros / semanas_activas, 1)
    
    result = {
        'id': habit.id,
        'titulo': habit.titulo,
        'tipo': habit.tipo,
        'archivado': habit.archivado,
        'es_grupal': habit.id_grupo is not None,
        'fecha_creacion': {
            'fecha': format_datetime(habit.fecha_creacion, g.current_user.id_clerk)[0],
            'hora': format_datetime(habit.fecha_creacion, g.current_user.id_clerk)[1]
        },
        'dias_desde_creacion': dias_desde_creacion,
        
        # Rachas
        'rachas': {
            'actual': rachas['actual'],
            'mejor': rachas['mejor']
        },
        
        # Estadísticas generales
        'estadisticas': {
            'total_registros': total_registros,
            'total_exitos': total_exitos,
            'total_fallos': total_fallos,
            'tasa_exito': round(tasa_exito, 1),
            'promedio_semanal': promedio_semanal,
            'primer_registro': {
                'fecha': format_datetime(primer_registro.fecha_hora_local, g.current_user.id_clerk)[0] if primer_registro else None,
                'hora': format_datetime(primer_registro.fecha_hora_local, g.current_user.id_clerk)[1] if primer_registro else None
            },
            'dias_desde_primer_registro': dias_desde_primer_registro
        },
        
        # Estado de hoy
        'registro_hoy': {
            'completado': registro_hoy is not None,
            'estado': registro_hoy.estado if registro_hoy else None,
            'comentario': registro_hoy.comentario if registro_hoy else None,
            'puede_registrar': registro_hoy is None,
            'fecha_local_usuario': hoy_local.isoformat()
        },
        
        # Registros recientes
        'registros_recientes': [{
            'id': entry.id,
            'fecha': format_datetime(entry.fecha_hora_local, g.current_user.id_clerk)[0],
            'hora': format_datetime(entry.fecha_hora_local, g.current_user.id_clerk)[1],
            'estado': entry.estado,
            'comentario': entry.comentario,
            'dias_atras': (hoy_local - entry.fecha).days
        } for entry in registros_recientes]
    }
    
    if habit.group:
        result['grupo'] = {
            'id': habit.group.id,
            'nombre': habit.group.nombre,
            'descripcion': habit.group.descripcion
        }
        
        member = GroupMember.query.filter_by(
            id_grupo=habit.id_grupo,
            id_clerk=g.current_user.id_clerk
        ).first()
        result['mi_rol_en_grupo'] = member.rol if member else 'miembro'
    
    return jsonify(result)

@auth_required
def update_habit(habit_id):
    """Actualizar un hábito existente"""
    habit = Habit.query.get_or_404(habit_id)
    
    if not can_edit_habit(habit_id, g.current_user.id_clerk):
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin permisos para editar'}}), 403
    
    data = request.get_json()
    
    if 'titulo' in data:
        habit.titulo = data['titulo']
    if 'tipo' in data and data['tipo'] in ['hacer', 'dejar']:
        habit.tipo = data['tipo']
    if 'archivado' in data:
        habit.archivado = data['archivado']
    
    db.session.commit()
    
    return jsonify({
        'id': habit.id,
        'titulo': habit.titulo,
        'tipo': habit.tipo,
        'archivado': habit.archivado,
        'es_grupal': habit.id_grupo is not None
    })

@auth_required
def delete_habit(habit_id):
    """Eliminar un hábito"""
    habit = Habit.query.get_or_404(habit_id)
    
    if habit.id_propietario != g.current_user.id_clerk:
        return jsonify({'error': {'code': 'forbidden', 'message': 'Solo el propietario puede eliminar'}}), 403
    
    try:
        # 1. Eliminar registros de rachas
        db.session.execute(text("DELETE FROM habito_rachas WHERE id_habito = :habit_id"), {"habit_id": habit_id})
        
        # 2. Eliminar registros de entradas
        db.session.execute(text("DELETE FROM habito_registros WHERE id_habito = :habit_id"), {"habit_id": habit_id})
        
        # 3. Finalmente eliminar el hábito
        db.session.execute(text("DELETE FROM habitos WHERE id = :habit_id"), {"habit_id": habit_id})
        
        db.session.commit()
        return jsonify({'ok': True})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting habit: {e}")
        return jsonify({'error': {'code': 'database_error', 'message': 'Error al eliminar el hábito'}}), 500

@auth_required
def get_habit_entries(habit_id):
    """Obtener registros de un hábito"""
    habit = Habit.query.get_or_404(habit_id)
    
    if not user_has_access_to_habit(habit_id, g.current_user.id_clerk):
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin acceso'}}), 403
    
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 20)), 100)
    
    query = HabitEntry.query.filter_by(
        id_habito=habit_id,
        id_clerk=g.current_user.id_clerk
    )
    
    # Filtrar por fechas
    if from_date:
        parsed_date = parse_date(from_date)
        if parsed_date:
            query = query.filter(HabitEntry.fecha >= parsed_date)
        else:
            return jsonify({'error': {'code': 'validation_error', 'message': 'Formato de fecha "from" inválido'}}), 422
    
    if to_date:
        parsed_date = parse_date(to_date)
        if parsed_date:
            query = query.filter(HabitEntry.fecha <= parsed_date)
        else:
            return jsonify({'error': {'code': 'validation_error', 'message': 'Formato de fecha "to" inválido'}}), 422
    
    # Obtener registros con paginación
    entries = query.order_by(HabitEntry.fecha.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return jsonify([{
        'id': entry.id,
        'fecha': entry.fecha.isoformat(),
        'estado': entry.estado,
        'comentario': entry.comentario
    } for entry in entries])

@auth_required
def create_habit_entry(habit_id):
    """Crear un nuevo registro para un hábito"""
    habit = Habit.query.get_or_404(habit_id)
    data = request.get_json()
    
    if not user_has_access_to_habit(habit_id, g.current_user.id_clerk):
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin acceso al hábito'}}), 403
    
    estado = data.get('estado')
    if estado == 'success':  
        estado = 'exito'
    elif estado == 'failure': 
        estado = 'fallo'
    comentario = data.get('comentario', '')
    
    # Obtener zona horaria del usuario
    user = g.current_user
    user_tz = pytz.timezone(user.zona_horaria)
    
    # Obtener fecha y hora actual en UTC y convertirla a la zona horaria del usuario
    now_utc = datetime.now(pytz.UTC)
    now_user = now_utc.astimezone(user_tz)
    
    # Ajustar la fecha según la hora de cierre del día del usuario
    fecha_registro = now_user.date()
    if now_user.hour < user.cierre_dia_hora:
        fecha_registro = fecha_registro - timedelta(days=1)
    
    print("Datos a procesar:", {
        "estado": estado,
        "comentario": comentario,
        "zona_horaria": user.zona_horaria,
        "hora_cierre": user.cierre_dia_hora,
        "fecha_registro": fecha_registro,
        "fecha_hora_local": now_user
    })
    
    if not estado or estado not in ['exito', 'fallo']:
        return jsonify({'error': {'code': 'validation_error', 'message': 'Estado debe ser "exito" o "fallo"'}}), 422
    
    # Validar fecha y hora
    fecha_str = data.get('fecha')  
    try:
        if fecha_str:
            if 'T' in fecha_str:
                # Formato ISO (YYYY-MM-DDTHH:MM:SS)
                fecha = datetime.strptime(fecha_str, '%Y-%m-%dT%H:%M:%S')
            elif ' ' in fecha_str:
                # Formato con espacio (YYYY-MM-DD HH:MM:SS)
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
            else:
                # Solo fecha (YYYY-MM-DD)
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d')
                hora_actual = datetime.now().time()
                fecha = fecha.replace(hour=hora_actual.hour, minute=hora_actual.minute, second=hora_actual.second)
        else:
            fecha = now_user
    except ValueError:
        return jsonify({
            'error': {
                'code': 'validation_error',
                'message': 'Formato de fecha inválido. Use YYYY-MM-DD, YYYY-MM-DD HH:MM:SS o YYYY-MM-DDTHH:MM:SS'
            }
        }), 422
    
    try:
        entry_id = str(uuid.uuid4())

        fecha_hora_utc = now_user.astimezone(pytz.UTC)
        
        new_entry = HabitEntry(
            id=entry_id,
            id_habito=habit_id,
            id_clerk=g.current_user.id_clerk,
            fecha=fecha_registro, 
            fecha_hora_local=fecha_hora_utc,  # Almacenar en UTC
            estado=estado,
            comentario=comentario
        )
        
        db.session.add(new_entry)
        db.session.flush() 

        # Actualizar si ya existe
        db.session.execute(
            text("""
                UPDATE habito_registros 
                SET estado = :estado,
                    comentario = :comentario,
                    fecha_hora_local = :fecha_hora_local,
                    fecha_actualizacion = NOW()
                WHERE id_habito = :habit_id 
                AND id_clerk = :user_id 
                AND fecha = :fecha
            """),
            {
                "habit_id": habit_id,
                "user_id": g.current_user.id_clerk,
                "fecha": fecha_registro,
                "fecha_hora_local": fecha_hora_utc, 
                "estado": estado,
                "comentario": comentario
            }
        )
        db.session.commit()
        
        entry = HabitEntry.query.get(entry_id)
        if not entry:
            entry = HabitEntry.query.filter_by(
                id_habito=habit_id,
                id_clerk=g.current_user.id_clerk,
                fecha=fecha_registro
            ).first()
        
        if not entry:
            db.session.rollback()
            return jsonify({'error': {'code': 'database_error', 'message': 'Error al recuperar el registro creado'}}), 500
        
        rachas = update_streak_on_entry(habit_id, g.current_user.id_clerk, fecha_registro, estado)
        
        fecha_hora_local = entry.fecha_hora_local.astimezone(user_tz)
        
        response_data = {
            'id': entry.id,
            'fecha': fecha_hora_local.strftime('%d/%m/%Y'),
            'hora': fecha_hora_local.strftime('%H:%M:%S'),
            'estado': entry.estado,
            'comentario': entry.comentario or '', 
            'rachas_usuario': rachas,
            'zona_horaria': user.zona_horaria 
        }
        
        print("Respuesta a enviar:", response_data)
        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating habit entry: {e}")
        return jsonify({'error': {'code': 'database_error', 'message': 'Error al guardar el registro'}}), 500

@auth_required
def delete_habit_entry(habit_id, entry_id):
    """Eliminar un registro de hábito"""
    entry = HabitEntry.query.filter_by(
        id=entry_id,
        id_habito=habit_id,
        id_clerk=g.current_user.id_clerk
    ).first_or_404()
    
    db.session.delete(entry)
    db.session.commit()
    
    rachas = calculate_streak(habit_id, g.current_user.id_clerk)
    
    return jsonify({
        'ok': True,
        'rachas_usuario_actualizadas': rachas
    })

@auth_required
def get_habit_streak(habit_id):
    """Obtener información de racha de un hábito"""
    habit = Habit.query.get_or_404(habit_id)
    if not user_has_access_to_habit(habit_id, g.current_user.id_clerk):
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin acceso'}}), 403
    
    streak_record = HabitStreak.query.filter_by(
        id_habito=habit_id,
        id_clerk=g.current_user.id_clerk
    ).first()
    
    if streak_record:
        return jsonify({
            'racha_actual': streak_record.racha_actual,
            'mejor_racha': streak_record.mejor_racha,
            'ultima_fecha': streak_record.ultima_fecha.isoformat() if streak_record.ultima_fecha else None
        })
    else:
        return jsonify({
            'racha_actual': 0,
            'mejor_racha': 0,
            'ultima_fecha': None
        })

@auth_required
def get_habits_dashboard():
    """Obtener resumen completo de hábitos con último registro, rachas y estadísticas"""
    habits = db.session.query(Habit).filter(
        or_(
            Habit.id_propietario == g.current_user.id_clerk,
            Habit.id_grupo.in_(
                db.session.query(GroupMember.id_grupo).filter_by(id_clerk=g.current_user.id_clerk)
            )
        )
    ).filter(Habit.archivado == False).all()
    
    hoy_local = get_user_local_date(g.current_user.id_clerk)
    
    result = []
    for habit in habits:

        rachas = calculate_streak(habit.id, g.current_user.id_clerk)
        ultimo_registro = HabitEntry.query.filter_by(
            id_habito=habit.id,
            id_clerk=g.current_user.id_clerk
        ).order_by(HabitEntry.fecha.desc()).first()
        
        total_registros = HabitEntry.query.filter_by(
            id_habito=habit.id,
            id_clerk=g.current_user.id_clerk
        ).count()
        
        total_exitos = HabitEntry.query.filter_by(
            id_habito=habit.id,
            id_clerk=g.current_user.id_clerk,
            estado='exito'
        ).count()
        
        total_fallos = HabitEntry.query.filter_by(
            id_habito=habit.id,
            id_clerk=g.current_user.id_clerk,
            estado='fallo'
        ).count()
        
        registro_hoy = HabitEntry.query.filter_by(
            id_habito=habit.id,
            id_clerk=g.current_user.id_clerk,
            fecha=hoy_local
        ).first()
        
        tasa_exito = (total_exitos / total_registros * 100) if total_registros > 0 else 0
        
        fecha_creacion_local = format_datetime(habit.fecha_creacion, g.current_user.id_clerk)
        ultimo_registro_fecha = None
        ultimo_registro_hora = None
        if ultimo_registro and ultimo_registro.fecha_hora_local:
            ultimo_registro_fecha, ultimo_registro_hora = format_datetime(
                ultimo_registro.fecha_hora_local, 
                g.current_user.id_clerk
            )
        
        habit_data = {
            'id': habit.id,
            'titulo': habit.titulo,
            'tipo': habit.tipo,
            'es_grupal': habit.id_grupo is not None,
            'rachas': {
                'actual': rachas['actual'],
                'mejor': rachas['mejor']
            },
            'ultimo_registro': {
                'fecha': ultimo_registro_fecha,
                'hora': ultimo_registro_hora,
                'estado': ultimo_registro.estado if ultimo_registro else None,
                'comentario': ultimo_registro.comentario if ultimo_registro else None,
                'dias_desde_ultimo': (hoy_local - ultimo_registro.fecha).days if ultimo_registro else None,
                'zona_horaria': g.current_user.zona_horaria
            },
            'estadisticas': {
                'total_registros': total_registros,
                'total_exitos': total_exitos,
                'total_fallos': total_fallos,
                'tasa_exito': round(tasa_exito, 1)
            },
            'registro_hoy': {
                'completado': registro_hoy is not None,
                'estado': registro_hoy.estado if registro_hoy else None,
                'comentario': registro_hoy.comentario if registro_hoy else None,
                'puede_registrar': registro_hoy is None,
                'fecha_local_usuario': hoy_local.isoformat()
            },
            'fecha_creacion': {
                'fecha': fecha_creacion_local[0],
                'hora': fecha_creacion_local[1],
                'zona_horaria': g.current_user.zona_horaria
            }
        }
        
        if habit.group:
            habit_data['grupo'] = {
                'id': habit.group.id,
                'nombre': habit.group.nombre
            }
        
        result.append(habit_data)
    
    result.sort(key=lambda x: x['ultimo_registro']['fecha'] or '1900-01-01', reverse=True)
    
    return jsonify({
        'habitos': result,
        'resumen': {
            'total_habitos': len(result),
            'habitos_con_racha_activa': len([h for h in result if h['rachas']['actual'] > 0]),
            'habitos_registrados_hoy': len([h for h in result if h['registro_hoy']['completado']]),
            'fecha_local_usuario': hoy_local.isoformat()
        }
    })

@auth_required
def get_habit_stats(habit_id):
    """Obtener estadísticas de un hábito específico con registros recientes"""
    habit = Habit.query.get_or_404(habit_id)
    
    if not user_has_access_to_habit(habit_id, g.current_user.id_clerk):
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin acceso al hábito'}}), 403
    
    rachas = calculate_streak(habit_id, g.current_user.id_clerk)
    
    total_registros = HabitEntry.query.filter_by(
        id_habito=habit_id,
        id_clerk=g.current_user.id_clerk
    ).count()
    
    registros_recientes = get_habit_recent_entries(habit_id, g.current_user.id_clerk, limit=10)
    
    result = {
        'id': habit.id,
        'titulo': habit.titulo,
        'tipo': habit.tipo,
        'archivado': habit.archivado,
        'es_grupal': habit.id_grupo is not None,
        'rachas': {
            'actual': rachas['actual'],
            'mejor': rachas['mejor']
        },
        'estadisticas': {
            'total_registros': total_registros
        },
        'registros_recientes': [{
            'id': entry.id,
            'fecha': entry.fecha.isoformat(),
            'estado': entry.estado,
            'comentario': entry.comentario
        } for entry in registros_recientes]
    }
    
    if habit.group:
        result['grupo'] = {
            'id': habit.group.id,
            'nombre': habit.group.nombre
        }
    
    return jsonify(result)

@auth_required
def get_streaks_overview():
    pass

@auth_required
def get_weekly_progress():
    from services.timezone_service import get_user_local_date
    from datetime import datetime, timedelta
    
    hoy_local = get_user_local_date(g.current_user.id_clerk)
    
    dias_desde_lunes = hoy_local.weekday() 
    lunes = hoy_local - timedelta(days=dias_desde_lunes)
    
    domingo = lunes + timedelta(days=6)
    
    semana = []
    
    for i in range(7):
        fecha_actual = lunes + timedelta(days=i)
        
        exitos = HabitEntry.query.filter(
            HabitEntry.id_clerk == g.current_user.id_clerk,
            HabitEntry.fecha == fecha_actual,
            HabitEntry.estado == 'exito'
        ).count()
        
        fallos = HabitEntry.query.filter(
            HabitEntry.id_clerk == g.current_user.id_clerk,
            HabitEntry.fecha == fecha_actual,
            HabitEntry.estado == 'fallo'
        ).count()
        
        total_habitos = Habit.query.filter(
            or_(
                Habit.id_propietario == g.current_user.id_clerk,
                Habit.id_grupo.in_(
                    db.session.query(GroupMember.id_grupo).filter_by(id_clerk=g.current_user.id_clerk)
                )
            ),
            Habit.archivado == False
        ).count()
        
        pendientes = total_habitos - (exitos + fallos)
        
        semana.append({
            'fecha': fecha_actual.isoformat(),
            'dia_semana': ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][i],
            'exitos': exitos,
            'fallos': fallos,
            'pendientes': pendientes,
            'total': total_habitos,
            'es_hoy': fecha_actual == hoy_local
        })
    
    return jsonify({
        'semana_actual': {
            'fecha_inicio': lunes.isoformat(),
            'fecha_fin': domingo.isoformat(),
            'dias': semana
        }
    })
