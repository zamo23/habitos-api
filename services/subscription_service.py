from models import db, Subscription, Habit, GroupMember

def get_user_subscription(user_id):
    """Obtener la suscripción actual de un usuario"""
    return Subscription.query.filter_by(id_clerk=user_id, es_actual=True).first()

def check_habit_limit(user_id, id_grupo=None):
    """Verificar si el usuario puede crear más hábitos según su plan"""
    subscription = get_user_subscription(user_id)
    
    # Si no hay suscripción, aplicar reglas básicas
    if not subscription or not subscription.plan:
        current_habits = Habit.query.filter_by(id_propietario=user_id, archivado=False).count()
        if current_habits >= 1:  # Free tier allows 1 habit
            return {'allowed': False, 'error': {'code': 'limit_exceeded', 'message': 'Límite de hábitos alcanzado para usuario sin plan'}}
        
        if id_grupo:
            return {'allowed': False, 'error': {'code': 'plan_required', 'message': 'Plan requerido para hábitos grupales'}}
        
        return {'allowed': True}
    
    # Verificar límite de hábitos del plan
    if subscription.plan.max_habitos:
        current_habits = Habit.query.filter_by(id_propietario=user_id, archivado=False).count()
        if current_habits >= subscription.plan.max_habitos:
            return {'allowed': False, 'error': {'code': 'limit_exceeded', 'message': 'Límite de hábitos alcanzado'}}
    
    # Verificar permisos para hábitos grupales
    if id_grupo:
        if not subscription.plan.permite_grupos:
            return {'allowed': False, 'error': {'code': 'plan_required', 'message': 'Plan requerido para hábitos grupales'}}
        
        # Verificar pertenencia al grupo
        member = GroupMember.query.filter_by(
            id_grupo=id_grupo,
            id_clerk=user_id
        ).first()
        
        if not member:
            return {'allowed': False, 'error': {'code': 'forbidden', 'message': 'Sin acceso al grupo'}}
    
    return {'allowed': True}

def check_group_access(user_id):
    """Verificar si el usuario puede crear o unirse a grupos según su plan"""
    subscription = get_user_subscription(user_id)
    
    # Si no hay suscripción o el plan no permite grupos
    if not subscription or not subscription.plan or not subscription.plan.permite_grupos:
        return {'allowed': False}
    
    return {'allowed': True}