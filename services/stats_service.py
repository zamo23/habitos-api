from models import db, User, Habit, HabitEntry, HabitStreak
from sqlalchemy import func
from datetime import datetime, timedelta

def get_system_stats():
    """Obtener estadísticas generales del sistema"""
    
    # Obtener usuarios activos (últimos 30 días)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = HabitEntry.query.with_entities(
        func.count(func.distinct(HabitEntry.id_clerk))
    ).filter(HabitEntry.fecha_creacion >= thirty_days_ago).scalar()

    # Obtener total de hábitos completados
    completed_habits = HabitEntry.query.filter_by(estado='exito').count()

    # Calcular tasa de éxito
    total_entries = HabitEntry.query.count()
    success_rate = 0
    if total_entries > 0:
        success_entries = HabitEntry.query.filter_by(estado='exito').count()
        success_rate = round((success_entries / total_entries) * 100, 2)

    # Calcular racha promedio
    avg_streak = db.session.query(
        func.avg(HabitStreak.racha_actual)
    ).filter(HabitStreak.racha_actual > 0).scalar()

    return {
        'active_users': active_users or 0,
        'completed_habits': completed_habits or 0,
        'success_rate': success_rate or 0,
        'average_streak': round(float(avg_streak or 0), 1)
    }
