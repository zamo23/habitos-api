from flask import request, jsonify, g, current_app
from models import db, Group, GroupMember, GroupInvite, User
from services.auth_service import auth_required
from services.subscription_service import check_group_access
from services.email_service import send_group_invitation
import uuid
from datetime import datetime, timedelta
import secrets
import logging

logger = logging.getLogger(__name__)

@auth_required
def get_groups():
    """Obtener grupos del usuario"""
    groups = db.session.query(Group).join(GroupMember).filter(
        GroupMember.id_clerk == g.current_user.id_clerk
    ).all()
    
    result = []
    for group in groups:
        member = GroupMember.query.filter_by(
            id_grupo=group.id,
            id_clerk=g.current_user.id_clerk
        ).first()
        
        result.append({
            'id': group.id,
            'nombre': group.nombre,
            'descripcion': group.descripcion,
            'miembros_count': len(group.members),
            'soy_rol': member.rol if member else 'miembro'
        })
    
    return jsonify(result)

@auth_required
def create_group():
    """Crear un nuevo grupo"""
    data = request.get_json()
    nombre = data.get('nombre')
    descripcion = data.get('descripcion', '')
    
    if not nombre:
        return jsonify({'error': {'code': 'validation_error', 'message': 'Nombre requerido'}}), 422
    
    access_check = check_group_access(g.current_user.id_clerk)
    if not access_check['allowed']:
        return jsonify({'error': {'code': 'plan_required', 'message': 'Plan requerido para crear grupos'}}), 403
    
    group = Group(
        nombre=nombre,
        descripcion=descripcion,
        id_propietario=g.current_user.id_clerk
    )
    
    db.session.add(group)
    db.session.flush() 
    
    member = GroupMember(
        id_grupo=group.id,
        id_clerk=g.current_user.id_clerk,
        rol='propietario'
    )
    
    db.session.add(member)
    db.session.commit()
    
    return jsonify({
        'id': group.id,
        'nombre': group.nombre
    }), 201

@auth_required
def get_group(group_id):
    """Obtener detalles de un grupo"""
    group = Group.query.get_or_404(group_id)
    member = GroupMember.query.filter_by(
        id_grupo=group_id,
        id_clerk=g.current_user.id_clerk
    ).first()
    
    if not member:
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin acceso al grupo'}}), 403
    
    members_data = []
    for member in group.members:
        members_data.append({
            'id_clerk': member.id_clerk,
            'rol': member.rol
        })
    
    return jsonify({
        'id': group.id,
        'nombre': group.nombre,
        'descripcion': group.descripcion,
        'propietario': {'id_clerk': group.id_propietario},
        'miembros': members_data
    })

@auth_required
def update_group(group_id):
    """Actualizar información de un grupo"""
    group = Group.query.get_or_404(group_id)
    member = GroupMember.query.filter_by(
        id_grupo=group_id,
        id_clerk=g.current_user.id_clerk
    ).first()
    
    if not member or member.rol not in ['propietario', 'administrador']:
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin permisos para editar el grupo'}}), 403
    
    data = request.get_json()
    
    if 'nombre' in data:
        group.nombre = data['nombre']
    
    if 'descripcion' in data:
        group.descripcion = data['descripcion']
    
    db.session.commit()
    
    return jsonify({
        'id': group.id,
        'nombre': group.nombre,
        'descripcion': group.descripcion
    })

@auth_required
def add_member(group_id):
    """Agregar miembro a un grupo"""
    group = Group.query.get_or_404(group_id)
    member = GroupMember.query.filter_by(
        id_grupo=group_id,
        id_clerk=g.current_user.id_clerk
    ).first()
    
    if not member or member.rol not in ['propietario', 'administrador']:
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin permisos para agregar miembros'}}), 403
    
    data = request.get_json()
    id_clerk = data.get('id_clerk')
    rol = data.get('rol', 'miembro')
    
    if not id_clerk:
        return jsonify({'error': {'code': 'validation_error', 'message': 'ID de usuario requerido'}}), 422
    
    if rol not in ['administrador', 'miembro']:
        return jsonify({'error': {'code': 'validation_error', 'message': 'Rol inválido'}}), 422
    
    existing_member = GroupMember.query.filter_by(
        id_grupo=group_id,
        id_clerk=id_clerk
    ).first()
    
    if existing_member:
        return jsonify({'error': {'code': 'already_exists', 'message': 'El usuario ya es miembro del grupo'}}), 409
    
    new_member = GroupMember(
        id_grupo=group_id,
        id_clerk=id_clerk,
        rol=rol
    )
    
    db.session.add(new_member)
    db.session.commit()
    
    return jsonify({
        'id_grupo': group_id,
        'id_clerk': id_clerk,
        'rol': rol
    }), 201

@auth_required
def remove_member(group_id, member_id):
    """Eliminar miembro de un grupo"""
    group = Group.query.get_or_404(group_id)
    member = GroupMember.query.filter_by(
        id_grupo=group_id,
        id_clerk=g.current_user.id_clerk
    ).first()
    
    if not member or member.rol not in ['propietario', 'administrador']:
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin permisos para eliminar miembros'}}), 403
    
    if group.id_propietario == member_id:
        return jsonify({'error': {'code': 'forbidden', 'message': 'No se puede eliminar al propietario del grupo'}}), 403
    
    member_to_remove = GroupMember.query.filter_by(
        id_grupo=group_id,
        id_clerk=member_id
    ).first()
    
    if not member_to_remove:
        return jsonify({'error': {'code': 'not_found', 'message': 'Miembro no encontrado'}}), 404
    
    db.session.delete(member_to_remove)
    db.session.commit()
    
    return jsonify({'ok': True})

@auth_required
def leave_group(group_id):
    """Salir voluntariamente de un grupo"""
    group = Group.query.get_or_404(group_id)
    
    # Verificar si el usuario es miembro del grupo
    member = GroupMember.query.filter_by(
        id_grupo=group_id,
        id_clerk=g.current_user.id_clerk
    ).first()
    
    if not member:
        return jsonify({'error': {'code': 'not_found', 'message': 'No eres miembro de este grupo'}}), 404
    
    # No permitir que el propietario abandone el grupo (tendría que transferir la propiedad o eliminar el grupo)
    if group.id_propietario == g.current_user.id_clerk:
        return jsonify({
            'error': {
                'code': 'forbidden', 
                'message': 'El propietario no puede abandonar el grupo. Debes transferir la propiedad o eliminar el grupo.'
            }
        }), 403
    
    # Eliminar al miembro del grupo
    db.session.delete(member)
    db.session.commit()
    
    return jsonify({'ok': True, 'message': 'Has abandonado el grupo exitosamente'})

def verify_invitation():
    """Verificar validez de una invitación a un grupo sin necesidad de autenticación"""
    token = request.args.get('token')
    
    if not token:
        return jsonify({'error': {'code': 'validation_error', 'message': 'Token de invitación requerido'}}), 422
    
    invitacion = GroupInvite.query.filter_by(token=token).first()
    
    if not invitacion:
        return jsonify({'error': {'code': 'not_found', 'message': 'Invitación no encontrada'}}), 404
    
    if invitacion.estado != 'pendiente':
        return jsonify({'error': {'code': 'invalid_status', 'message': f'La invitación está {invitacion.estado}'}}), 400
    
    if invitacion.expira_en < datetime.utcnow():
        invitacion.estado = 'expirada'
        db.session.commit()
        return jsonify({'error': {'code': 'expired', 'message': 'La invitación ha expirado'}}), 400
    
    # Obtener información del grupo y del invitador
    group = Group.query.get(invitacion.id_grupo)
    invitador = User.query.filter_by(id_clerk=invitacion.id_invitador).first()
    
    return jsonify({
        'invitation': {
            'id': invitacion.id,
            'token': invitacion.token,
            'email': invitacion.correo_invitado,
            'status': invitacion.estado,
            'expires_at': invitacion.expira_en.isoformat()
        },
        'group': {
            'id': group.id,
            'name': group.nombre,
            'description': group.descripcion
        },
        'inviter': {
            'id': invitador.id_clerk,
            'name': invitador.nombre_completo
        }
    })

@auth_required
def accept_invite():
    """Aceptar invitación para unirse a un grupo"""
    data = request.get_json()
    invite_token = data.get('token')
    
    if not invite_token:
        return jsonify({'error': {'code': 'validation_error', 'message': 'Token de invitación requerido'}}), 422
    
    invitacion = GroupInvite.query.filter_by(token=invite_token).first()
    
    if not invitacion:
        return jsonify({'error': {'code': 'not_found', 'message': 'Invitación no encontrada'}}), 404
    
    if invitacion.estado != 'pendiente':
        return jsonify({'error': {'code': 'invalid_status', 'message': f'La invitación está {invitacion.estado}'}}), 400
    
    if invitacion.expira_en < datetime.utcnow():
        invitacion.estado = 'expirada'
        db.session.commit()
        return jsonify({'error': {'code': 'expired', 'message': 'La invitación ha expirado'}}), 400
    
    # Verificar si el usuario ya es miembro
    existing_member = GroupMember.query.filter_by(
        id_grupo=invitacion.id_grupo,
        id_clerk=g.current_user.id_clerk
    ).first()
    
    if existing_member:
        return jsonify({'error': {'code': 'already_member', 'message': 'Ya eres miembro de este grupo'}}), 400
    
    # Agregar al usuario como miembro
    new_member = GroupMember(
        id_grupo=invitacion.id_grupo,
        id_clerk=g.current_user.id_clerk,
        rol='miembro'
    )
    
    # Actualizar estado de la invitación
    invitacion.estado = 'aceptada'
    
    db.session.add(new_member)
    db.session.commit()
    
    # Obtener información del grupo
    group = Group.query.get(invitacion.id_grupo)
    
    return jsonify({
        'id_grupo': group.id,
        'nombre_grupo': group.nombre,
        'rol': 'miembro'
    }), 200

@auth_required
def get_invites():
    """Obtener todas las invitaciones del usuario por correo electrónico"""
    # Obtener las invitaciones por correo del usuario actual
    user_email = g.current_user.email
    
    invitations = GroupInvite.query.filter_by(
        correo_invitado=user_email,
        estado='pendiente'
    ).all()
    
    result = []
    for invite in invitations:
        if invite.expira_en < datetime.utcnow():
            invite.estado = 'expirada'
            continue
            
        group = Group.query.get(invite.id_grupo)
        result.append({
            'id': invite.id,
            'token': invite.token,
            'id_grupo': invite.id_grupo,
            'nombre_grupo': group.nombre if group else "Grupo desconocido",
            'invitador': invite.id_invitador,
            'fecha_creacion': invite.fecha_creacion.isoformat(),
            'expira_en': invite.expira_en.isoformat()
        })
    
    # Si hubo cambios de estado por expiración, guardarlos
    if any(inv.estado == 'expirada' for inv in invitations if inv not in result):
        db.session.commit()
    
    return jsonify(result)

@auth_required
def get_group_invites(group_id):
    """Obtener todas las invitaciones de un grupo"""
    # Verificar permisos
    member = GroupMember.query.filter_by(
        id_grupo=group_id,
        id_clerk=g.current_user.id_clerk
    ).first()
    
    if not member or member.rol not in ['propietario', 'administrador']:
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin permisos para ver invitaciones del grupo'}}), 403
    
    invitations = GroupInvite.query.filter_by(
        id_grupo=group_id
    ).all()
    
    result = []
    for invite in invitations:
        result.append({
            'id': invite.id,
            'correo_invitado': invite.correo_invitado,
            'estado': invite.estado,
            'fecha_creacion': invite.fecha_creacion.isoformat(),
            'expira_en': invite.expira_en.isoformat()
        })
    
    return jsonify(result)

@auth_required
def create_invite(group_id):
    """Crear invitación para unirse a un grupo"""
    group = Group.query.get_or_404(group_id)
    member = GroupMember.query.filter_by(
        id_grupo=group_id,
        id_clerk=g.current_user.id_clerk
    ).first()
    
    if not member or member.rol not in ['propietario', 'administrador']:
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin permisos para crear invitaciones'}}), 403
    
    data = request.get_json()
    correo_invitado = data.get('correo')
    id_usuario_existente = data.get('id_usuario')
    
    if not correo_invitado and not id_usuario_existente:
        return jsonify({'error': {'code': 'validation_error', 'message': 'Correo o ID de usuario requerido'}}), 422
    
    # Si se proporciona un ID de usuario, obtener su correo
    if id_usuario_existente:
        user = User.query.filter_by(id_clerk=id_usuario_existente).first()
        if user and user.email:
            correo_invitado = user.email
        else:
            return jsonify({'error': {'code': 'user_not_found', 'message': 'No se encontró el correo del usuario'}}), 404
    
    token = secrets.token_hex(32)
    
    invitacion = GroupInvite(
        id_grupo=group_id,
        id_invitador=g.current_user.id_clerk,
        correo_invitado=correo_invitado,
        token=token,
        estado='pendiente',
        expira_en=datetime.utcnow() + timedelta(days=7)
    )
    
    db.session.add(invitacion)
    db.session.flush()  # Para obtener el ID de la invitación
    
    # Crear notificación interna si es un usuario existente
    if id_usuario_existente:
        from models.notification import Notification
        
        notificacion = Notification(
            id_clerk=id_usuario_existente,
            tipo='sistema',
            datos_json={
                'subtipo': 'invitacion_grupo',
                'id_grupo': group_id,
                'nombre_grupo': group.nombre,
                'id_invitacion': invitacion.id,
                'token': token
            }
        )
        db.session.add(notificacion)
    
    # Enviar correo electrónico
    try:
        # Obtener información del invitador
        invitador = User.query.filter_by(id_clerk=g.current_user.id_clerk).first()
        invitador_nombre = invitador.nombre if invitador and hasattr(invitador, 'nombre') else "Un usuario"
        
        # Datos para la invitación
        invitation_data = {
            'invitador_nombre': invitador_nombre,
            'nombre_grupo': group.nombre,
            'descripcion_grupo': group.descripcion or "Sin descripción",
            'token': token,
            'url_base': current_app.config.get('FRONTEND_URL', 'https://habitos.cvpx.lat')
        }
        
        # Enviar correo
        sent = send_group_invitation(correo_invitado, invitation_data)
        if not sent:
            logger.warning(f"No se pudo enviar el correo de invitación a {correo_invitado}")
    except Exception as e:
        logger.error(f"Error al enviar invitación por correo: {str(e)}")
    
    db.session.commit()
    
    return jsonify({
        'id': invitacion.id,
        'token': invitacion.token,
        'correo_invitado': correo_invitado,
        'expira_en': invitacion.expira_en.isoformat()
    }), 201
    
@auth_required
def create_batch_invites(group_id):
    """Crear múltiples invitaciones para unirse a un grupo"""
    group = Group.query.get_or_404(group_id)
    member = GroupMember.query.filter_by(
        id_grupo=group_id,
        id_clerk=g.current_user.id_clerk
    ).first()
    
    if not member or member.rol not in ['propietario', 'administrador']:
        return jsonify({'error': {'code': 'forbidden', 'message': 'Sin permisos para crear invitaciones'}}), 403
    
    data = request.get_json()
    correos = data.get('correos', [])
    
    if not correos or not isinstance(correos, list) or len(correos) == 0:
        return jsonify({'error': {'code': 'validation_error', 'message': 'Se requiere una lista de correos'}}), 422
    
    # Limitar el número de invitaciones por solicitud
    max_invites = min(len(correos), 20)  # Máximo 20 invitaciones por solicitud
    
    invitaciones = []
    errores = []
    
    # Obtener información del invitador para correos
    invitador = User.query.filter_by(id_clerk=g.current_user.id_clerk).first()
    invitador_nombre = invitador.nombre_completo if invitador and hasattr(invitador, 'nombre_completo') else "Un usuario"
    
    for i in range(max_invites):
        correo_invitado = correos[i]
        
        if not correo_invitado or not isinstance(correo_invitado, str):
            errores.append({
                'correo': correo_invitado,
                'error': 'Formato de correo inválido'
            })
            continue
            
        try:
            token = secrets.token_hex(32)
            
            invitacion = GroupInvite(
                id_grupo=group_id,
                id_invitador=g.current_user.id_clerk,
                correo_invitado=correo_invitado,
                token=token,
                estado='pendiente',
                expira_en=datetime.utcnow() + timedelta(days=7)
            )
            
            db.session.add(invitacion)
            db.session.flush()  # Para obtener el ID de la invitación
            
            # Datos para la invitación por correo
            invitation_data = {
                'invitador_nombre': invitador_nombre,
                'nombre_grupo': group.nombre,
                'descripcion_grupo': group.descripcion or "Sin descripción",
                'token': token,
                'url_base': current_app.config.get('FRONTEND_URL', 'https://habitos.cvpx.lat')
            }
            
            # Intentar enviar correo
            try:
                sent = send_group_invitation(correo_invitado, invitation_data)
                if not sent:
                    logger.warning(f"No se pudo enviar el correo de invitación a {correo_invitado}")
            except Exception as e:
                logger.error(f"Error al enviar invitación por correo a {correo_invitado}: {str(e)}")
            
            invitaciones.append({
                'id': invitacion.id,
                'token': invitacion.token,
                'correo_invitado': correo_invitado,
                'expira_en': invitacion.expira_en.isoformat()
            })
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al crear invitación para {correo_invitado}: {str(e)}")
            errores.append({
                'correo': correo_invitado,
                'error': 'Error interno al crear la invitación'
            })
    
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al guardar invitaciones en la base de datos: {str(e)}")
        return jsonify({'error': {'code': 'database_error', 'message': 'Error al guardar invitaciones'}}), 500
    
    return jsonify({
        'invitaciones': invitaciones,
        'errores': errores,
        'total_exitosas': len(invitaciones),
        'total_errores': len(errores)
    }), 201