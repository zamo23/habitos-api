from flask import request, jsonify, g
from models import db, PaymentInbox, PaymentHistory, Plan
from services.auth_service import auth_required, verify_clerk_token, get_or_create_user
from datetime import datetime
import uuid

@auth_required
def confirm_payment():
    """Confirmar un pago entrante"""
    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400

    data = request.json
    required_fields = ['remitente', 'monto', 'codigo_seguridad', 'fecha_hora']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Faltan campos requeridos"}), 400

    try:
        # Convertir monto de formato "S/ X.XX" a centavos
        monto_str = data['monto'].replace('S/', '').strip()
        try:
            monto_float = float(monto_str)
            monto_centavos = int(monto_float * 100)
        except (ValueError, TypeError):
            return jsonify({"error": "Formato de monto inválido"}), 400
            
        # Validar que no haya un pago duplicado
        fecha_hora = datetime.fromisoformat(data['fecha_hora'].replace('Z', '+00:00'))
        existing_payment = PaymentInbox.query.filter_by(
            codigo_seguridad=data['codigo_seguridad'],
            monto_texto=data['monto'],
            fecha_hora=fecha_hora
        ).first()
        
        if existing_payment:
            return jsonify({"error": "Pago ya procesado"}), 409

        # Crear registro en bandeja de pagos
        payment = PaymentInbox(
            id=str(uuid.uuid4()),
            remitente=data['remitente'],
            monto_texto=data['monto'],
            codigo_seguridad=data['codigo_seguridad'],
            fecha_hora=fecha_hora
        )
        db.session.add(payment)
        db.session.commit()

        return jsonify({
            "mensaje": "Pago registrado correctamente",
            "id_pago": payment.id,
            "monto_recibido": data['monto'],
            "moneda": "PEN"
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al procesar el pago: {str(e)}"}), 500

def verify_payment():
    """Verificar un pago existente"""
    if request.method == 'OPTIONS':
        return '', 200 

    # Validar token de autorización
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'error': {'code': 'unauthorized', 'message': 'Token requerido'}}), 401
    
    token = auth_header.split(' ')[1]
    payload = verify_clerk_token(token)
    if not payload:
        return jsonify({'error': {'code': 'invalid_token', 'message': 'Token inválido'}}), 401
    
    # Obtener o crear usuario
    try:
        user = get_or_create_user(payload)
        g.current_user = user
    except Exception as e:
        return jsonify({'error': {'code': 'server_error', 'message': f'Error al obtener usuario: {str(e)}'}}), 500

    if not request.is_json:
        return jsonify({"error": "Content-Type debe ser application/json"}), 400

    data = request.json
    required_fields = ['primer_nombre', 'primer_apellido', 'id_plan']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Faltan campos requeridos"}), 400
        
    try:
        # Obtener información del plan
        plan = Plan.query.get(data['id_plan'])
        if not plan:
            return jsonify({"error": "Plan no encontrado"}), 404

        query = PaymentInbox.query
        codigo_seguridad = data.get('codigo_seguridad', '000')
        query = query.filter_by(codigo_seguridad=codigo_seguridad)
            
        # Obtener todos los pagos que coincidan
        pagos = query.all()
        for pago in pagos:
            # Verificar coincidencia de nombre y apellido
            nombre_completo_bd = ' '.join([part for part in pago.remitente.split() if len(part) > 1 and part[-1] != '.']).lower()
            nombre_buscar = data['primer_nombre'].lower()
            apellido_buscar = data['primer_apellido'].lower()
            
            if nombre_buscar in nombre_completo_bd and apellido_buscar in nombre_completo_bd:
                # Convertir monto a centavos
                monto_str = pago.monto_texto.replace('S/', '').strip()
                try:
                    monto_centavos = int(float(monto_str) * 100)
                except ValueError:
                    continue
                        
                # Verificar que el monto coincida con el plan
                if abs(monto_centavos - plan.precio_centavos) > 2:
                    return jsonify({
                        "error": "El monto del pago no coincide con el precio del plan",
                        "pago_realizado": pago.monto_texto,
                        "precio_plan": f"S/ {plan.precio_centavos/100:.2f}"
                    }), 400
                    
                # Verificar si ya existe un registro en historial
                existing_history = PaymentHistory.query.filter_by(id_pago_inbox=pago.id).first()
                if existing_history:
                    return jsonify({
                        "aprobado": True,
                        "error": "Este pago ya fue procesado anteriormente",
                        "id_pago": pago.id,
                        "id_historial": existing_history.id,
                        "remitente": pago.remitente,
                        "monto": pago.monto_texto,
                        "fecha_hora": pago.fecha_hora.isoformat(),
                        "fecha_aplicacion": existing_history.fecha_aplicacion.isoformat(),
                        "estado": existing_history.estado,
                        "plan": {
                            "id": plan.id,
                            "codigo": plan.codigo,
                            "nombre": plan.nombre,
                            "precio_centavos": plan.precio_centavos
                        },
                        "ya_procesado": True
                    }), 200

                # Crear registro en historial
                payment_history = PaymentHistory(
                    id=str(uuid.uuid4()),
                    id_pago_inbox=pago.id,
                    id_clerk=g.current_user.id_clerk,
                    id_plan=plan.id,
                    monto_centavos=monto_centavos,
                    moneda='PEN',
                    estado='confirmado',
                    descripcion=f'Pago verificado para plan {plan.nombre}'
                )
                
                db.session.add(payment_history)
                
                # Actualizar suscripción del usuario
                try:
                    # Eliminar suscripciones actuales
                    db.session.execute(
                        db.text("""
                            DELETE FROM suscripciones 
                            WHERE id_clerk = :id_clerk
                        """),
                        {"id_clerk": g.current_user.id_clerk}
                    )
                    db.session.flush()
                    
                    # Crear nueva suscripción premium
                    fecha_inicio = datetime.utcnow()
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
                    
                    db.session.commit()

                    return jsonify({
                        "aprobado": True,
                        "id_pago": pago.id,
                        "id_historial": payment_history.id,
                        "remitente": pago.remitente,
                        "monto": pago.monto_texto,
                        "fecha_hora": pago.fecha_hora.isoformat(),
                        "fecha_aplicacion": payment_history.fecha_aplicacion.isoformat(),
                        "plan": {
                            "id": plan.id,
                            "codigo": plan.codigo,
                            "nombre": plan.nombre,
                            "precio_centavos": plan.precio_centavos
                        }
                    }), 200
                    
                except Exception as e:
                    db.session.rollback()
                    raise Exception(f"Error al actualizar suscripción: {str(e)}")
                    
        # No se encontró pago que coincida
        error_info = {
            "aprobado": False,
            "error": "No se encontró un pago válido para los datos proporcionados",
            "codigo": "PAYMENT_NOT_FOUND",
            "debug": {
                "pagos_encontrados": len(pagos),
                "nombre_buscado": data['primer_nombre'].lower(),
                "apellido_buscado": data['primer_apellido'].lower(),
                "codigo_seguridad": codigo_seguridad
            }
        }
        
        if pagos:
            error_info["debug"]["pagos_encontrados"] = [{
                "remitente": pago.remitente,
                "monto": pago.monto_texto,
                "codigo": pago.codigo_seguridad,
                "fecha": pago.fecha_hora.isoformat()
            } for pago in pagos]
            
        return jsonify(error_info), 422

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Error al verificar pago: {str(e)}"}), 500