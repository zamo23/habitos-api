from flask import request, jsonify, g
from models import db, Group, GroupMember, GroupInvite
from services.auth_service import auth_required
from services.subscription_service import check_group_access
import uuid
from datetime import datetime, timedelta
import secrets

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
    
    if not correo_invitado:
        return jsonify({'error': {'code': 'validation_error', 'message': 'Correo del invitado requerido'}}), 422
    
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
    db.session.commit()
    
    return jsonify({
        'id': invitacion.id,
        'token': invitacion.token,
        'correo_invitado': invitacion.correo_invitado,
        'expira_en': invitacion.expira_en.isoformat()
    }), 201