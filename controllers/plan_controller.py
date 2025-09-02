from flask import request, jsonify, g
from models import db, Plan, Subscription, Habit, GroupMember
from services.auth_service import auth_required
from sqlalchemy import text
import uuid

@auth_required
def get_plans():
    """Obtener planes disponibles"""
    moneda = request.args.get('moneda', 'USD')
    plans = Plan.query.filter_by(activo=True, moneda=moneda).all()
    
    return jsonify([{
        'id': plan.id,
        'codigo': plan.codigo,
        'nombre': plan.nombre,
        'precio_centavos': plan.precio_centavos,
        'moneda': plan.moneda,
        'max_habitos': plan.max_habitos,
        'permite_grupos': plan.permite_grupos,
        'descripcion': plan.descripcion
    } for plan in plans])

@auth_required
def get_my_subscription():
    """Obtener suscripción actual del usuario"""
    subscription = Subscription.query.filter_by(id_clerk=g.current_user.id_clerk, es_actual=True).first()
    if not subscription:
        return jsonify({'error': {'code': 'not_found', 'message': 'Suscripción no encontrada'}}), 404
    
    plan_data = None
    if subscription.plan:
        plan_data = {
            'id': subscription.plan.id,
            'codigo': subscription.plan.codigo,
            'nombre': subscription.plan.nombre,
            'precio_centavos': subscription.plan.precio_centavos,
            'moneda': getattr(subscription.plan, 'moneda', 'USD'),
            'max_habitos': subscription.plan.max_habitos,
            'permite_grupos': subscription.plan.permite_grupos
        }
    
    return jsonify({
        'id': subscription.id,
        'plan': plan_data,
        'estado': subscription.estado,
        'ciclo': getattr(subscription, 'ciclo', None),
        'es_actual': getattr(subscription, 'es_actual', True),
        'periodo_inicio': subscription.periodo_inicio.isoformat() if subscription.periodo_inicio else None,
        'periodo_fin': subscription.periodo_fin.isoformat() if subscription.periodo_fin else None
    })

@auth_required
def create_subscription():
    """Crear nueva suscripción"""
    data = request.get_json()
    plan_codigo = data.get('plan_codigo')
    moneda = data.get('moneda', 'USD')
    
    plan = Plan.query.filter_by(codigo=plan_codigo, moneda=moneda).first()
    if not plan:
        return jsonify({'error': {'code': 'not_found', 'message': 'Plan no encontrado'}}), 404
    
    try:
        db.session.execute(
            text("UPDATE suscripciones SET es_actual = 0 WHERE id_clerk = :user_id AND es_actual = 1"),
            {"user_id": g.current_user.id_clerk}
        )
        
        subscription_id = str(uuid.uuid4())
        if plan.codigo == 'gratis':
            # Free plan
            db.session.execute(
                text("""
                    INSERT INTO suscripciones (id, id_clerk, id_plan, estado, ciclo, es_actual)
                    VALUES (:id, :user_id, :plan_id, 'activa', 'gratuito', 1)
                """),
                {"id": subscription_id, "user_id": g.current_user.id_clerk, "plan_id": plan.id}
            )
        else:
            db.session.execute(
                text("""
                    INSERT INTO suscripciones (id, id_clerk, id_plan, estado, ciclo, es_actual, periodo_inicio, periodo_fin)
                    VALUES (:id, :user_id, :plan_id, 'activa', 'mensual', 1, NOW(), DATE_ADD(NOW(), INTERVAL 30 DAY))
                """),
                {"id": subscription_id, "user_id": g.current_user.id_clerk, "plan_id": plan.id}
            )
        
        db.session.commit()
        
        return jsonify({
            'id': subscription_id,
            'plan': {
                'id': plan.id,
                'codigo': plan.codigo,
                'nombre': plan.nombre
            },
            'estado': 'activa'
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': {'code': 'server_error', 'message': f'Error al crear suscripción: {str(e)}'}}), 500

@auth_required
def get_habits_usage():
    """Obtener uso de hábitos y límites del plan actual"""
    active_habits = Habit.query.filter_by(
        id_propietario=g.current_user.id_clerk, 
        archivado=False
    ).count()
    
    group_habits = db.session.query(Habit).select_from(
        Habit.__table__.join(
            GroupMember.__table__,
            Habit.id_grupo == GroupMember.id_grupo
        )
    ).filter(
        GroupMember.id_clerk == g.current_user.id_clerk,
        Habit.archivado == False,
        Habit.id_propietario != g.current_user.id_clerk
    ).count()
    
    result = {
        'active_habits': active_habits,
        'group_habits': group_habits,
        'total_habits': active_habits + group_habits
    }
    
    subscription = Subscription.query.filter_by(id_clerk=g.current_user.id_clerk, es_actual=True).first()
    
    if subscription and subscription.plan:
        result['plan'] = {
            'codigo': subscription.plan.codigo,
            'nombre': subscription.plan.nombre,
            'max_habitos': subscription.plan.max_habitos,
            'permite_grupos': subscription.plan.permite_grupos,
            'estado': subscription.estado
        }
        
        if subscription.plan.max_habitos:
            result['usage_percentage'] = min(100, (active_habits / subscription.plan.max_habitos) * 100)
        else:
            result['usage_percentage'] = 0 
    else:
        result['plan'] = {
            'codigo': 'none',
            'nombre': 'Sin Plan',
            'max_habitos': 0,
            'permite_grupos': False,
            'estado': 'inactiva'
        }
        result['usage_percentage'] = 100 
    
    return jsonify(result)