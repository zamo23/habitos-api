import uuid
from flask import request, jsonify, g
from models import db, Coupon, Plan, PaymentHistory
from services.auth_service import auth_required, verify_clerk_token, get_or_create_user
from datetime import datetime

def verify_coupon():
    """Verificar validez de un cupón"""
    if request.method == 'OPTIONS':
        return '', 200

    if not request.is_json:
        return jsonify({"error": {"code": "invalid_request", "message": "Content-Type debe ser application/json"}}), 400

    data = request.json
    codigo = data.get('codigo')
    if not codigo:
        return jsonify({"error": {"code": "validation_error", "message": "Se requiere el código del cupón"}}), 400

    coupon = Coupon.query.filter_by(codigo=codigo).first()
    if not coupon:
        return jsonify({"error": {"code": "not_found", "message": "Cupón no encontrado"}}), 404

    if not coupon.activo:
        return jsonify({"error": {"code": "invalid_coupon", "message": "El cupón no está activo"}}), 400

    if coupon.usos_actuales >= coupon.max_usos:
        return jsonify({"error": {"code": "invalid_coupon", "message": "El cupón ha alcanzado el límite de usos"}}), 400

    now = datetime.utcnow()
    if coupon.fecha_inicio and now < coupon.fecha_inicio:
        return jsonify({"error": {"code": "invalid_coupon", "message": "El cupón aún no está vigente"}}), 400
    if coupon.fecha_fin and now > coupon.fecha_fin:
        return jsonify({"error": {"code": "invalid_coupon", "message": "El cupón ha expirado"}}), 400

    return jsonify({
        "valido": True,
        "tipo_descuento": coupon.tipo_descuento,
        "valor": coupon.valor
    })

def redeem_free_coupon():
    """Redimir un cupón del 100% de descuento"""
    if request.method == 'OPTIONS':
        return '', 200
    
    if request.method != 'OPTIONS':
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': {'code': 'unauthorized', 'message': 'Token requerido'}}), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_clerk_token(token)
        if not payload:
            return jsonify({'error': {'code': 'invalid_token', 'message': 'Token inválido'}}), 401
        
        try:
            user = get_or_create_user(payload)
            g.current_user = user
        except Exception as e:
            return jsonify({'error': {'code': 'server_error', 'message': f'Error al obtener usuario: {str(e)}'}}), 500
        
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400

    data = request.json
    required_fields = ['codigo', 'id_plan']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Se requiere el código del cupón y el ID del plan"}), 400

    try:

        print(f"Procesando cupón: {data}")  # Debug log
        coupon = Coupon.query.filter_by(codigo=data['codigo']).first()
        if not coupon:
            return jsonify({"error": "Cupón no encontrado"}), 404
        
        if not coupon.activo:
            return jsonify({"error": "El cupón no está activo"}), 400

        if coupon.usos_actuales >= coupon.max_usos:
            return jsonify({"error": "El cupón ha alcanzado el límite de usos"}), 400

        now = datetime.utcnow()
        if coupon.fecha_inicio and now < coupon.fecha_inicio:
            return jsonify({"error": "El cupón aún no está vigente"}), 400
        if coupon.fecha_fin and now > coupon.fecha_fin:
            return jsonify({"error": "El cupón ha expirado"}), 400

        plan = Plan.query.get(data['id_plan'])
        if not plan:
            return jsonify({"error": "Plan no encontrado"}), 404

        precio_original = plan.precio_centavos
        es_gratuito = False

        if coupon.tipo_descuento == 'porcentaje':
            es_gratuito = coupon.valor >= 100
        elif coupon.tipo_descuento == 'fijo':
            es_gratuito = coupon.valor >= precio_original

        if not es_gratuito:
            return jsonify({"error": "Este cupón no es válido para suscripción gratuita"}), 400

        try:
            # Crear registro en historial de pagos con fecha UTC
            utc_now = datetime.utcnow()
            payment_history = PaymentHistory(
                id=str(uuid.uuid4()),
                id_pago_inbox=None, 
                id_clerk=g.current_user.id_clerk,
                id_plan=plan.id,
                id_cupon=coupon.id,
                monto_centavos=0,
                moneda='PEN',
                estado='confirmado',
                descripcion=f'Suscripción gratuita con cupón {coupon.codigo}',
                fecha_aplicacion=utc_now 
            )
            
            db.session.add(payment_history)

            coupon.usos_actuales += 1
            db.session.execute(
                db.text("""
                    DELETE FROM suscripciones 
                    WHERE id_clerk = :id_clerk
                """),
                {"id_clerk": g.current_user.id_clerk}
            )
            db.session.flush()
            
            # Crear nueva suscripción usando UTC
            fecha_inicio = utc_now  
            fecha_fin = fecha_inicio.replace(month=fecha_inicio.month + 1) if fecha_inicio.month < 12 else fecha_inicio.replace(year=fecha_inicio.year + 1, month=1)
            
            nueva_suscripcion = {
                'id': str(uuid.uuid4()),
                'id_clerk': g.current_user.id_clerk,
                'id_plan': plan.id,
                'estado': 'activa',
                'ciclo': 'mensual',
                'es_actual': 1,
                'periodo_inicio': fecha_inicio,
                'periodo_fin': fecha_fin
            }
            
            db.session.execute(
                db.text("""
                    INSERT INTO suscripciones 
                    (id, id_clerk, id_plan, estado, ciclo, es_actual, periodo_inicio, periodo_fin)
                    VALUES 
                    (:id, :id_clerk, :id_plan, :estado, :ciclo, :es_actual, :periodo_inicio, :periodo_fin)
                """),
                nueva_suscripcion
            )
            
            # Un solo commit para toda la transacción
            db.session.commit()

            return jsonify({
                "mensaje": "Cupón redimido correctamente",
                "suscripcion": {
                    "id": nueva_suscripcion['id'],
                    "plan": plan.nombre,
                    "periodo_inicio": fecha_inicio.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "periodo_fin": fecha_fin.strftime('%Y-%m-%dT%H:%M:%SZ')
                },
                "pago": {
                    "id": payment_history.id,
                    "monto": 0,
                    "moneda": "PEN",
                    "fecha": utc_now.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "estado": "confirmado",
                    "descuento": {
                        "tipo": coupon.tipo_descuento,
                        "valor": coupon.valor,
                        "codigo": coupon.codigo
                    }
                }
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": f"Error al actualizar suscripción: {str(e)}"}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al redimir cupón: {str(e)}"}), 500

def verify_coupon():
    """Verificar la validez de un cupón y determinar el flujo a seguir"""
    if request.method == 'OPTIONS':
        return '', 200
    
    if request.method != 'OPTIONS':
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': {'code': 'unauthorized', 'message': 'Token requerido'}}), 401
        
        token = auth_header.split(' ')[1]
        payload = verify_clerk_token(token)
        if not payload:
            return jsonify({'error': {'code': 'invalid_token', 'message': 'Token inválido'}}), 401
        
        try:
            user = get_or_create_user(payload)
            g.current_user = user
        except Exception as e:
            return jsonify({'error': {'code': 'server_error', 'message': f'Error al obtener usuario: {str(e)}'}}), 500
        
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400

    data = request.json
    required_fields = ['codigo', 'id_plan', 'ciclo']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Se requiere el código del cupón, el ID del plan y el ciclo (mensual/anual)"}), 400

    if data['ciclo'] not in ['mensual', 'anual']:
        return jsonify({"error": "El ciclo debe ser 'mensual' o 'anual'"}), 400

    try:
        coupon = Coupon.query.filter_by(codigo=data['codigo']).first()
        
        if not coupon:
            return jsonify({"error": "Cupón no encontrado"}), 404

        if not coupon.activo:
            return jsonify({"error": "El cupón no está activo"}), 400

        if coupon.usos_actuales >= coupon.max_usos:
            return jsonify({"error": "El cupón ha alcanzado el límite de usos"}), 400

        now = datetime.utcnow()
        if coupon.fecha_inicio and now < coupon.fecha_inicio:
            return jsonify({"error": "El cupón aún no está vigente"}), 400
        if coupon.fecha_fin and now > coupon.fecha_fin:
            return jsonify({"error": "El cupón ha expirado"}), 400

        plan = Plan.query.get(data['id_plan'])
        if not plan:
            return jsonify({"error": "Plan no encontrado"}), 404

        precio_original = plan.precio_centavos
        precio_final = precio_original
        es_gratuito = False
        
        if coupon.tipo_descuento == 'porcentaje':
            descuento = (precio_original * coupon.valor) // 100
            precio_final = precio_original - descuento
            es_gratuito = coupon.valor >= 100  
        elif coupon.tipo_descuento == 'fijo':
            descuento = coupon.valor
            precio_final = max(0, precio_original - descuento)
            es_gratuito = descuento >= precio_original 

        precio_final = max(0, precio_final)

        return jsonify({
            "valido": True,
            "id": coupon.id,
            "tipo_descuento": coupon.tipo_descuento,
            "valor": coupon.valor,
            "es_gratis": es_gratuito,
            "precio_original": precio_original,
            "precio_final": precio_final,
            "descuento_centavos": min(precio_original, coupon.valor if coupon.tipo_descuento == 'fijo' else descuento),
            "flujo_sugerido": "gratis" if es_gratuito else "pago",
            "plan": {
                "id": plan.id,
                "nombre": plan.nombre,
                "codigo": plan.codigo
            }
        }), 200

    except Exception as e:
        return jsonify({"error": f"Error al verificar el cupón: {str(e)}"}), 500

