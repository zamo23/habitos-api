from datetime import timedelta
from models import db, Habit, HabitEntry, HabitStreak, GroupMember
from sqlalchemy import or_

from services.timezone_service import get_timezone_service

def calculate_streak(habit_id, user_id):
    """Calcular racha con verificación diaria de ruptura"""
    timezone_service = get_timezone_service()
    hoy_local = timezone_service.get_user_local_date(user_id)
    ayer_local = hoy_local - timedelta(days=1)
    
    # Obtener o crear registro de racha
    streak_record = HabitStreak.query.filter_by(id_habito=habit_id, id_clerk=user_id).first()
    
    if not streak_record:
        # Crear nuevo registro de racha
        streak_record = HabitStreak(
            id_habito=habit_id,
            id_clerk=user_id,
            racha_actual=0,
            mejor_racha=0,
            ultima_fecha=None,
            ultima_revision_local=hoy_local
        )
        db.session.add(streak_record)
        db.session.commit()
        return {'actual': 0, 'mejor': 0}
    
    # Verificar si ya revisamos hoy
    if streak_record.ultima_revision_local == hoy_local:
        return {'actual': streak_record.racha_actual, 'mejor': streak_record.mejor_racha}
    
    # Verificar entrada de ayer
    yesterday_entry = HabitEntry.query.filter_by(
        id_habito=habit_id,
        id_clerk=user_id,
        fecha=ayer_local
    ).first()
    
    # Actualizar racha basada en el estado de ayer
    if yesterday_entry and yesterday_entry.estado == 'exito':
        # La racha continúa (no cambiar racha_actual)
        pass
    else:
        # Verificar si había una racha activa
        if streak_record.racha_actual > 0:
            # Si había una racha activa, registrar fallo automáticamente
            hora_local = timezone_service.get_user_local_datetime(user_id)
            fallo_automatico = HabitEntry(
                id_habito=habit_id,
                id_clerk=user_id,
                fecha=ayer_local,
                fecha_hora_local=hora_local,
                estado='fallo',
                comentario='Registro automático - No se completó el hábito'
            )
            db.session.add(fallo_automatico)
            # La racha se rompe
            streak_record.racha_actual = 0
        else:
            # Si no había racha activa (racha_actual = 0), no registrar fallo
            pass
    
    streak_record.ultima_revision_local = hoy_local
    db.session.commit()
    
    return {'actual': streak_record.racha_actual, 'mejor': streak_record.mejor_racha}

def update_streak_on_entry(habit_id, user_id, fecha, estado):
    """Actualizar racha cuando se crea un nuevo registro"""
    timezone_service = get_timezone_service()
    hoy_local = timezone_service.get_user_local_date(user_id)
    ayer_local = hoy_local - timedelta(days=1)
    
    # Obtener o crear registro de racha
    streak_record = HabitStreak.query.filter_by(id_habito=habit_id, id_clerk=user_id).first()
    
    if not streak_record:
        streak_record = HabitStreak(
            id_habito=habit_id,
            id_clerk=user_id,
            racha_actual=0,
            mejor_racha=0,
            ultima_fecha=None,
            ultima_revision_local=hoy_local
        )
        db.session.add(streak_record)
    
    if estado == 'exito':
        # Verificar si ayer también fue un éxito
        if fecha == hoy_local:  # Registro de hoy
            yesterday_entry = HabitEntry.query.filter_by(
                id_habito=habit_id,
                id_clerk=user_id,
                fecha=ayer_local
            ).first()
            
            if yesterday_entry and yesterday_entry.estado == 'exito':
                # Continuar racha
                streak_record.racha_actual += 1
            else:
                # Iniciar nueva racha
                streak_record.racha_actual = 1
        else:
            # Entrada histórica - recalcular desde cero
            entries = HabitEntry.query.filter_by(
                id_habito=habit_id,
                id_clerk=user_id,
                estado='exito'
            ).order_by(HabitEntry.fecha.desc()).all()
            
            if entries:
                # Calcular racha actual desde la fecha más reciente
                current_streak = 0
                check_date = entries[0].fecha
                
                for entry in entries:
                    if entry.fecha == check_date:
                        current_streak += 1
                        check_date -= timedelta(days=1)
                    else:
                        break
                
                streak_record.racha_actual = current_streak
            else:
                streak_record.racha_actual = 1
        
        # Actualizar mejor racha
        if streak_record.racha_actual > streak_record.mejor_racha:
            streak_record.mejor_racha = streak_record.racha_actual
        
        # Actualizar última fecha
        streak_record.ultima_fecha = fecha
        
    elif estado == 'fallo':
        # La racha se rompe
        streak_record.racha_actual = 0
        # No actualizar ultima_fecha en caso de fallos
    
    # Actualizar fecha de revisión
    streak_record.ultima_revision_local = hoy_local
    db.session.commit()
    
    return {'actual': streak_record.racha_actual, 'mejor': streak_record.mejor_racha}

def user_has_access_to_habit(habit_id, user_id):
    """Verificar si un usuario tiene acceso a un hábito"""
    habit = Habit.query.get(habit_id)
    if not habit:
        return False
    
    # Es propietario
    if habit.id_propietario == user_id:
        return True
    
    # Es miembro del grupo
    if habit.id_grupo:
        member = GroupMember.query.filter_by(
            id_grupo=habit.id_grupo,
            id_clerk=user_id
        ).first()
        return member is not None
    
    return False

def can_edit_habit(habit_id, user_id):
    """Verificar si un usuario puede editar un hábito"""
    habit = Habit.query.get(habit_id)
    if not habit:
        return False
    
    # Es propietario
    if habit.id_propietario == user_id:
        return True
    
    # Es administrador/propietario del grupo
    if habit.id_grupo:
        member = GroupMember.query.filter_by(
            id_grupo=habit.id_grupo,
            id_clerk=user_id
        ).first()
        return member and member.rol in ['propietario', 'administrador']
    
    return False

def get_habit_recent_entries(habit_id, user_id, limit=10):
    """Obtener entradas recientes de un hábito"""
    return HabitEntry.query.filter_by(
        id_habito=habit_id,
        id_clerk=user_id
    ).order_by(HabitEntry.fecha.desc()).limit(limit).all()