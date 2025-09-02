import uuid
from datetime import datetime

import pytz
from models import db
from core.datetime_util import DateTimeUtil

class Habit(db.Model):
    __tablename__ = 'habitos'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_propietario = db.Column(db.String(191), db.ForeignKey('usuarios.id_clerk'), nullable=False)
    id_grupo = db.Column(db.String(36), db.ForeignKey('grupos.id'))
    titulo = db.Column(db.String(255), nullable=False)
    tipo = db.Column(db.Enum('hacer', 'dejar'), nullable=False)
    archivado = db.Column(db.Boolean, default=False)
    fecha_creacion = db.Column(db.DateTime, default=lambda: DateTimeUtil.get_current_utc())
    
    user = db.relationship('User', backref='habits')
    group = db.relationship('Group', backref='habits')

class HabitEntry(db.Model):
    __tablename__ = 'habito_registros'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_habito = db.Column(db.String(36), db.ForeignKey('habitos.id'), nullable=False)
    id_clerk = db.Column(db.String(191), db.ForeignKey('usuarios.id_clerk'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    fecha_hora_local = db.Column(db.DateTime, nullable=False)
    estado = db.Column(db.Enum('exito', 'fallo'), nullable=False)
    comentario = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=lambda: datetime.now(pytz.UTC))
    fecha_actualizacion = db.Column(db.DateTime, default=lambda: datetime.now(pytz.UTC), onupdate=lambda: datetime.now(pytz.UTC))
    
    habit = db.relationship('Habit', backref='entries')
    user = db.relationship('User', backref='habit_entries')
    
    __table_args__ = (db.UniqueConstraint('id_habito', 'id_clerk', 'fecha', name='uniq_registro'),)

class HabitStreak(db.Model):
    __tablename__ = 'habito_rachas'
    id_habito = db.Column(db.String(36), db.ForeignKey('habitos.id'), primary_key=True)
    id_clerk = db.Column(db.String(191), db.ForeignKey('usuarios.id_clerk'), primary_key=True)
    racha_actual = db.Column(db.Integer, default=0)
    mejor_racha = db.Column(db.Integer, default=0)
    ultima_fecha = db.Column(db.Date)
    ultima_revision_local = db.Column(db.Date)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    habit = db.relationship('Habit', backref='streaks')
    user = db.relationship('User', backref='habit_streaks')