from flask import request, jsonify, g
from models import db, Habit, HabitEntry, GroupMember
from services.auth_service import auth_required
from sqlalchemy import or_
from datetime import datetime, timedelta, date
from services.date_service import parse_date

@auth_required
def get_reports_overview():
    """Obtener resumen general de hábitos y rachas"""
    month = request.args.get('month')
    
    habits_query = db.session.query(Habit).filter(
        or_(
            Habit.id_propietario == g.current_user.id_clerk,
            Habit.id_grupo.in_(
                db.session.query(GroupMember.id_grupo).filter_by(id_clerk=g.current_user.id_clerk)
            )
        )
    ).filter(Habit.archivado == False)
    
    total_habitos = habits_query.count()
    rachas_activas = 0
    top_mejores = []
    
    from services.habit_service import calculate_streak
    for habit in habits_query.all():
        rachas = calculate_streak(habit.id, g.current_user.id_clerk)
        if rachas['actual'] > 0:
            rachas_activas += 1
        
        top_mejores.append({
            'habit_id': habit.id,
            'titulo': habit.titulo,
            'mejor_racha': rachas['mejor']
        })
    
    top_mejores.sort(key=lambda x: x['mejor_racha'], reverse=True)
    top_mejores = top_mejores[:5] 
    
    return jsonify({
        'total_habitos': total_habitos,
        'rachas_activas': rachas_activas,
        'top_mejores': top_mejores
    })

@auth_required
def get_reports_weekly():
    """Obtener reporte semanal de éxitos"""
    from_date = request.args.get('from')
    to_date = request.args.get('to')
    
    if not from_date or not to_date:
        return jsonify({'error': {'code': 'validation_error', 'message': 'from y to requeridos'}}), 422
    
    parsed_from = parse_date(from_date)
    parsed_to = parse_date(to_date)
    
    if not parsed_from or not parsed_to:
        return jsonify({'error': {'code': 'validation_error', 'message': 'Formato de fecha inválido'}}), 422
    
    entries = db.session.query(HabitEntry, Habit).join(Habit).filter(
        HabitEntry.id_clerk == g.current_user.id_clerk,
        HabitEntry.fecha >= parsed_from,
        HabitEntry.fecha <= parsed_to,
        HabitEntry.estado == 'exito'
    ).all()
    
    dias_detalle = {}
    current_date = parsed_from
    while current_date <= parsed_to:
        dias_detalle[current_date.isoformat()] = {
            'fecha': current_date.isoformat(),
            'exitos': 0
        }
        current_date += timedelta(days=1)
    
    for entry, _ in entries:
        fecha = entry.fecha.isoformat()
        dias_detalle[fecha]['exitos'] += 1
    
    return jsonify({
        'periodo': {
            'desde': parsed_from.isoformat(),
            'hasta': parsed_to.isoformat()
        },
        'total_exitos': len(entries),
        'dias': list(dias_detalle.values())
    })

@auth_required
def get_reports_heatmap():
    """Obtener mapa de calor de registros"""
    habit_id = request.args.get('habit_id')
    month = request.args.get('month')
    
    if not month:
        return jsonify({'error': {'code': 'validation_error', 'message': 'month requerido (YYYY-MM)'}}), 422
    
    try:
        year, month_num = map(int, month.split('-'))
    except ValueError:
        return jsonify({'error': {'code': 'validation_error', 'message': 'Formato de month inválido. Use YYYY-MM'}}), 422
    
    first_day = date(year, month_num, 1)
    if month_num == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month_num + 1, 1) - timedelta(days=1)
    
    query = HabitEntry.query.filter(
        HabitEntry.id_clerk == g.current_user.id_clerk,
        HabitEntry.fecha >= first_day,
        HabitEntry.fecha <= last_day
    )
    
    if habit_id and habit_id != 'all':
        query = query.filter(HabitEntry.id_habito == habit_id)
    
    entries = query.all()
    
    date_map = {}
    for entry in entries:
        date_key = entry.fecha.isoformat()
        date_map[date_key] = entry.estado
    
    days = []
    current_date = first_day
    while current_date <= last_day:
        days.append({
            'date': current_date.isoformat(),
            'estado': date_map.get(current_date.isoformat(), 'ninguno')
        })
        current_date += timedelta(days=1)
    
    return jsonify({
        'month': month,
        'days': days
    })

@auth_required
def get_streaks_overview():
    """Obtener resumen de rachas de todos los hábitos"""
    habits = db.session.query(Habit).filter(
        or_(
            Habit.id_propietario == g.current_user.id_clerk,
            Habit.id_grupo.in_(
                db.session.query(GroupMember.id_grupo).filter_by(id_clerk=g.current_user.id_clerk)
            )
        )
    ).filter(Habit.archivado == False).all()
    
    result = []
    from services.habit_service import calculate_streak
    for habit in habits:
        rachas = calculate_streak(habit.id, g.current_user.id_clerk)
        result.append({
            'habit_id': habit.id,
            'titulo': habit.titulo,
            'tipo': habit.tipo,
            'racha_actual': rachas['actual'],
            'mejor_racha': rachas['mejor']
        })
    
    return jsonify(result)