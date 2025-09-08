from flask import request, jsonify, g
from models import db, Notification
from services.auth_service import auth_required
from datetime import datetime

@auth_required
def get_notifications():
    """Obtener notificaciones del usuario actual"""
    notifications = Notification.query.filter_by(
        id_clerk=g.current_user.id_clerk
    ).order_by(Notification.fecha_creacion.desc()).all()
    
    result = []
    for notification in notifications:
        notif_data = {
            'id': notification.id,
            'tipo': notification.tipo,
            'datos': notification.datos_json,
            'fecha_creacion': notification.fecha_creacion.isoformat()
        }
        
        # Agregar información adicional para invitaciones a grupos
        if notification.datos_json and notification.datos_json.get('subtipo') == 'invitacion_grupo':
            notif_data['subtipo'] = 'invitacion_grupo'
            notif_data['nombre_grupo'] = notification.datos_json.get('nombre_grupo')
            notif_data['id_grupo'] = notification.datos_json.get('id_grupo')
        
        result.append(notif_data)
    
    return jsonify(result)

@auth_required
def mark_notification_read(notification_id):
    """Marcar notificación como leída"""
    notification = Notification.query.filter_by(
        id=notification_id,
        id_clerk=g.current_user.id_clerk
    ).first_or_404()
    
    # Actualizar campo leída (si existe) o programada_para (como alternativa)
    if hasattr(notification, 'leida'):
        notification.leida = True
    elif notification.programada_para:
        notification.programada_para = None
    
    db.session.commit()
    
    return jsonify({'ok': True})

@auth_required
def delete_notification(notification_id):
    """Eliminar una notificación"""
    notification = Notification.query.filter_by(
        id=notification_id,
        id_clerk=g.current_user.id_clerk
    ).first_or_404()
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({'ok': True})
