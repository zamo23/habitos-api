from flask import jsonify, g
from models import db, Plan, Subscription
from services.auth_service import auth_required
from sqlalchemy.orm import joinedload
from sqlalchemy import text

@auth_required
def get_current_subscription():
    """Obtener la suscripción actual del usuario con historial de pagos"""
    try:
        subscription = Subscription.query.options(
            joinedload(Subscription.plan)
        ).filter_by(
            id_clerk=g.current_user.id_clerk,
            es_actual=True
        ).first()
        
        if not subscription or not subscription.plan:
            return jsonify({"error": "No se encontró suscripción activa"}), 404
        
        sql_query = text("""
            SELECT 
                ph.id,
                ph.monto_centavos,
                ph.moneda,
                ph.estado,
                ph.descripcion,
                ph.fecha_aplicacion,
                p.nombre as plan_nombre,
                COALESCE(pi.fecha_hora, ph.fecha_aplicacion) as fecha_pago,
                c.codigo as cupon_codigo,
                c.tipo_descuento,
                c.valor as valor_descuento
            FROM pagos_historial ph
            JOIN planes p ON ph.id_plan = p.id
            LEFT JOIN pagos_inbox pi ON ph.id_pago_inbox = pi.id
            LEFT JOIN cupones c ON ph.id_cupon = c.id
            WHERE ph.id_clerk = :id_clerk
            ORDER BY ph.fecha_aplicacion DESC
        """)
        
        pagos = db.session.execute(sql_query, {"id_clerk": g.current_user.id_clerk}).fetchall()
        
        historial_pagos = [{
            "id": pago.id,
            "monto_centavos": pago.monto_centavos,
            "moneda": pago.moneda,
            "fecha_pago": pago.fecha_pago.isoformat() if pago.fecha_pago else None,
            "estado": pago.estado,
            "plan": pago.plan_nombre,
            "descripcion": pago.descripcion,
            "descuento": {
                "codigo": pago.cupon_codigo,
                "tipo": pago.tipo_descuento,
                "valor": pago.valor_descuento
            } if pago.cupon_codigo else None
        } for pago in pagos]

        response = {
            "plan": {
                "codigo": subscription.plan.codigo,
                "nombre": subscription.plan.nombre,
                "precio_centavos": subscription.plan.precio_centavos,
                "moneda": subscription.plan.moneda,
                "max_habitos": subscription.plan.max_habitos,
                "permite_grupos": subscription.plan.permite_grupos
            },
            "suscripcion": {
                "id": subscription.id,
                "estado": subscription.estado,
                "ciclo": subscription.ciclo,
                "periodo_inicio": subscription.periodo_inicio.isoformat() if subscription.periodo_inicio else None,
                "periodo_fin": subscription.periodo_fin.isoformat() if subscription.periodo_fin else None
            },
            "historial_pagos": historial_pagos
        }
        
        return jsonify(response)

    except Exception as e:
        return jsonify({"error": f"Error al obtener suscripción: {str(e)}"}), 500