from . import db
from datetime import datetime

class Coupon(db.Model):
    __tablename__ = 'cupones'

    id = db.Column(db.String(36), primary_key=True)
    codigo = db.Column(db.String(50), nullable=False, unique=True)
    tipo_descuento = db.Column(db.Enum('porcentaje', 'fijo'), nullable=False)
    valor = db.Column(db.Integer, nullable=False)
    max_usos = db.Column(db.Integer, nullable=False, default=1)
    usos_actuales = db.Column(db.Integer, nullable=False, default=0)
    fecha_inicio = db.Column(db.DateTime, nullable=True)
    fecha_fin = db.Column(db.DateTime, nullable=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    fecha_creacion = db.Column(db.DateTime, server_default=db.func.now())

    # Relaciones
    pagos = db.relationship('models.payment.PaymentHistory', back_populates='cupon', lazy='dynamic')
