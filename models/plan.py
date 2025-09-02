import uuid
from datetime import datetime
from models import db

class Plan(db.Model):
    __tablename__ = 'planes'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    precio_centavos = db.Column(db.Integer, nullable=False, default=0)
    moneda = db.Column(db.String(3), default='USD')
    max_habitos = db.Column(db.Integer)
    permite_grupos = db.Column(db.Boolean, default=False)
    descripcion = db.Column(db.Text)
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

class Subscription(db.Model):
    __tablename__ = 'suscripciones'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_clerk = db.Column(db.String(191), db.ForeignKey('usuarios.id_clerk'), nullable=False)
    id_plan = db.Column(db.Integer, db.ForeignKey('planes.id'), nullable=False)
    estado = db.Column(db.Enum('activa','cancelada','vencida'), default='activa')
    ciclo = db.Column(db.Enum('gratuito','mensual','anual'))
    es_actual = db.Column(db.Boolean, default=True)
    periodo_inicio = db.Column(db.DateTime)
    periodo_fin = db.Column(db.DateTime)
    cancelar_en = db.Column(db.DateTime)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_actualizacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='subscriptions')
    plan = db.relationship('Plan', backref='subscriptions')
