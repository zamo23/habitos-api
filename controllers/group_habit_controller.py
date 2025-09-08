from flask import request, jsonify, g, current_app
from models import db, Habit, Group, GroupMember, HabitEntry
from services.auth_service import auth_required
from services.habit_service import calculate_streak
from services.timezone_service import get_user_local_date
import uuid
from datetime import datetime

@auth_required
def create_group_habit(group_id):
    """Crear un hábito asociado a un grupo"""
    # Verificar pertenencia al grupo
    member = GroupMember.query.filter_by(
        id_grupo=group_id,
        id_clerk=g.current_user.id_clerk
    ).first()
    
    if not member:
        return jsonify({'error': {'code': 'forbidden', 'message': 'No eres miembro de este grupo'}}), 403
    
    # Solo propietarios y administradores pueden crear hábitos grupales
    if member.rol not in ['propietario', 'administrador']:
        return jsonify({'error': {'code': 'forbidden', 'message': 'No tienes permisos para crear hábitos grupales'}}), 403
    
    data = request.get_json()
    
    if not data.get('titulo'):
        return jsonify({'error': {'code': 'validation_error', 'message': 'El título del hábito es requerido'}}), 422
    
    # Crear el hábito grupal
    habit = Habit(
        id_propietario=g.current_user.id_clerk,
        id_grupo=group_id,
        titulo=data.get('titulo'),
        tipo=data.get('tipo', 'hacer')  # Valor por defecto: 'hacer'
    )
    
    db.session.add(habit)
    db.session.commit()
    
    return jsonify({
        'id': habit.id,
        'titulo': habit.titulo,
        'tipo': habit.tipo,
        'id_grupo': habit.id_grupo
    }), 201

@auth_required
def get_group_habits(group_id):
    """Obtener hábitos de un grupo"""
    # Verificar pertenencia al grupo
    member = GroupMember.query.filter_by(
        id_grupo=group_id,
        id_clerk=g.current_user.id_clerk
    ).first()
    
    if not member:
        return jsonify({'error': {'code': 'forbidden', 'message': 'No eres miembro de este grupo'}}), 403
    
    # Obtener todos los hábitos del grupo
    habits = Habit.query.filter_by(
        id_grupo=group_id,
        archivado=False
    ).all()
    
    result = []
    for habit in habits:
        result.append({
            'id': habit.id,
            'titulo': habit.titulo,
            'tipo': habit.tipo,
            'id_propietario': habit.id_propietario,
            'fecha_creacion': habit.fecha_creacion.isoformat()
        })
    
    return jsonify(result)

@auth_required
def get_group_habits_for_user():
    """Obtener solo los hábitos grupales del usuario"""
    estado = request.args.get('estado', 'activos')
    page = int(request.args.get('page', 1))
    limit = min(int(request.args.get('limit', 20)), 100)
    
    current_app.logger.info(f"get_group_habits_for_user llamado para usuario: {g.current_user.id_clerk}")
    current_app.logger.info(f"Parámetros: estado={estado}, page={page}, limit={limit}")
    
    # Obtener IDs de grupos a los que pertenece el usuario
    group_memberships = GroupMember.query.filter_by(id_clerk=g.current_user.id_clerk).all()
    group_ids = [membership.id_grupo for membership in group_memberships]
    
    current_app.logger.info(f"Usuario pertenece a {len(group_ids)} grupos: {group_ids}")
    
    if not group_ids:
        current_app.logger.info("Usuario no pertenece a ningún grupo, devolviendo lista vacía")
        return jsonify([])  # Usuario no pertenece a ningún grupo
    
    # Consultar hábitos grupales
    query = Habit.query.filter(
        Habit.id_grupo.in_(group_ids)
    )
    
    if estado == 'activos':
        query = query.filter(Habit.archivado == False)
    elif estado == 'archivados':
        query = query.filter(Habit.archivado == True)
    
    # Debug - Obtener la consulta SQL generada
    sql_statement = str(query.statement.compile(
        compile_kwargs={"literal_binds": True}
    ))
    current_app.logger.info(f"SQL generado: {sql_statement}")
    
    habits = query.offset((page - 1) * limit).limit(limit).all()
    current_app.logger.info(f"Se encontraron {len(habits)} hábitos grupales")
    
    if habits:
        habit_ids = [h.id for h in habits]
        current_app.logger.info(f"IDs de hábitos grupales encontrados: {habit_ids}")
    
    hoy_local = get_user_local_date(g.current_user.id_clerk)
    
    result = []
    for habit in habits:
        current_app.logger.info(f"Procesando hábito grupal: {habit.id}, grupo: {habit.id_grupo}")
        
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
            'es_grupal': True,
            'rachas': rachas,
            'registro_hoy': {
                'completado': registro_hoy is not None,
                'estado': registro_hoy.estado if registro_hoy else None,
                'comentario': registro_hoy.comentario if registro_hoy else None,
                'puede_registrar': registro_hoy is None,
                'fecha_local_usuario': hoy_local.isoformat()
            },
            'grupo': {
                'id': habit.group.id,
                'nombre': habit.group.nombre
            }
        }
        
        result.append(habit_data)
    
    return jsonify(result)

@auth_required
def get_group_habit_details(habit_id):
    """
    Obtener detalles completos de un hábito grupal incluyendo el progreso de todos los miembros
    """
    # Verificar que el hábito existe y es grupal
    habit = Habit.query.get_or_404(habit_id)
    
    if not habit.id_grupo:
        return jsonify({'error': {'code': 'not_found', 'message': 'El hábito no es grupal'}}), 404
    
    # Verificar que el usuario pertenece al grupo
    member = GroupMember.query.filter_by(
        id_grupo=habit.id_grupo,
        id_clerk=g.current_user.id_clerk
    ).first()
    
    if not member:
        return jsonify({'error': {'code': 'forbidden', 'message': 'No eres miembro de este grupo'}}), 403
    
    # Obtener información del grupo
    group = Group.query.get(habit.id_grupo)
    
    # Obtener todos los miembros del grupo
    group_members = GroupMember.query.filter_by(id_grupo=habit.id_grupo).all()
    
    # Obtener la fecha local del usuario actual
    hoy_local = get_user_local_date(g.current_user.id_clerk)
    
    # Información básica del hábito
    result = {
        'id': habit.id,
        'titulo': habit.titulo,
        'tipo': habit.tipo,
        'archivado': habit.archivado,
        'es_grupal': True,
        'id_propietario': habit.id_propietario,
        'fecha_creacion': habit.fecha_creacion.isoformat(),
        'grupo': {
            'id': group.id,
            'nombre': group.nombre,
            'descripcion': group.descripcion
        },
        'mi_rol_en_grupo': member.rol,
        
        # Mi propio progreso
        'mi_progreso': get_user_progress_for_habit(habit.id, g.current_user.id_clerk, hoy_local),
        
        # Progreso de todos los miembros
        'progreso_miembros': []
    }
    
    # Añadir progreso de cada miembro
    for group_member in group_members:
        # Obtener usuario
        from models import User
        user = User.query.get(group_member.id_clerk)
        
        # Progreso del miembro
        member_progress = get_user_progress_for_habit(habit.id, group_member.id_clerk, hoy_local)
        
        result['progreso_miembros'].append({
            'id_clerk': group_member.id_clerk,
            'nombre': user.nombre_completo,
            'rol': group_member.rol,
            'progreso': member_progress
        })
    
    return jsonify(result)

def get_user_progress_for_habit(habit_id, user_id, fecha_local):
    """
    Obtener el progreso de un usuario específico para un hábito
    """
    # Rachas
    rachas = calculate_streak(habit_id, user_id)
    
    # Registro de hoy
    registro_hoy = HabitEntry.query.filter_by(
        id_habito=habit_id,
        id_clerk=user_id,
        fecha=fecha_local
    ).first()
    
    # Total de registros
    total_registros = HabitEntry.query.filter_by(
        id_habito=habit_id,
        id_clerk=user_id
    ).count()
    
    # Éxitos y fallos
    total_exitos = HabitEntry.query.filter_by(
        id_habito=habit_id,
        id_clerk=user_id,
        estado='exito'
    ).count()
    
    total_fallos = HabitEntry.query.filter_by(
        id_habito=habit_id,
        id_clerk=user_id,
        estado='fallo'
    ).count()
    
    # Calcular tasa de éxito
    tasa_exito = (total_exitos / total_registros * 100) if total_registros > 0 else 0
    
    # Registros recientes
    registros_recientes = HabitEntry.query.filter_by(
        id_habito=habit_id,
        id_clerk=user_id
    ).order_by(HabitEntry.fecha.desc()).limit(5).all()
    
    return {
        'rachas': rachas,
        'total_registros': total_registros,
        'total_exitos': total_exitos,
        'total_fallos': total_fallos,
        'tasa_exito': round(tasa_exito, 1),
        'registro_hoy': {
            'completado': registro_hoy is not None,
            'estado': registro_hoy.estado if registro_hoy else None,
            'comentario': registro_hoy.comentario if registro_hoy else None
        },
        'registros_recientes': [{
            'fecha': entry.fecha.isoformat(),
            'estado': entry.estado,
            'comentario': entry.comentario
        } for entry in registros_recientes]
    }
