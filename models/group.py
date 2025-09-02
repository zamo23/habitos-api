import uuid
from datetime import datetime
from models import db

class Group(db.Model):
    __tablename__ = 'grupos'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_propietario = db.Column(db.String(191), db.ForeignKey('usuarios.id_clerk'), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    descripcion = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    propietario = db.relationship('User', backref='grupos_propios')

class GroupMember(db.Model):
    __tablename__ = 'grupo_miembros'
    id_grupo = db.Column(db.String(36), db.ForeignKey('grupos.id'), primary_key=True)
    id_clerk = db.Column(db.String(191), db.ForeignKey('usuarios.id_clerk'), primary_key=True)
    rol = db.Column(db.Enum('propietario', 'administrador', 'miembro'), default='miembro')
    fecha_union = db.Column(db.DateTime, default=datetime.utcnow)
    
    group = db.relationship('Group', backref='members')
    user = db.relationship('User', backref='group_memberships')

class GroupInvite(db.Model):
    __tablename__ = 'grupo_invitaciones'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_grupo = db.Column(db.String(36), db.ForeignKey('grupos.id'), nullable=False)
    id_invitador = db.Column(db.String(191), db.ForeignKey('usuarios.id_clerk'), nullable=False)
    correo_invitado = db.Column(db.String(191), nullable=False)
    token = db.Column(db.String(64), nullable=False, unique=True)
    estado = db.Column(db.Enum('pendiente', 'aceptada', 'expirada', 'revocada'), default='pendiente')
    expira_en = db.Column(db.DateTime, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    group = db.relationship('Group', backref='invites')
    invitador = db.relationship('User', backref='invites_sent')
