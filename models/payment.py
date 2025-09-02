from . import db

class PaymentInbox(db.Model):
    __tablename__ = 'pagos_inbox'

    id = db.Column(db.String(36), primary_key=True)
    remitente = db.Column(db.String(191), nullable=False)
    monto_texto = db.Column(db.String(50), nullable=False)
    codigo_seguridad = db.Column(db.String(191), nullable=False)
    fecha_hora = db.Column(db.DateTime, nullable=False)
    fecha_creacion = db.Column(db.DateTime, server_default=db.func.now())

class PaymentHistory(db.Model):
    __tablename__ = 'pagos_historial'

    id = db.Column(db.String(36), primary_key=True)
    id_pago_inbox = db.Column(db.String(36), db.ForeignKey('pagos_inbox.id', ondelete='CASCADE'), nullable=False)
    id_clerk = db.Column(db.String(191), db.ForeignKey('usuarios.id_clerk', ondelete='CASCADE'), nullable=False)
    id_plan = db.Column(db.Integer, db.ForeignKey('planes.id'), nullable=False)
    monto_centavos = db.Column(db.Integer, nullable=False)
    moneda = db.Column(db.String(3), nullable=False)
    estado = db.Column(db.Enum('confirmado', 'rechazado'), nullable=False, default='confirmado')
    descripcion = db.Column(db.String(255))
    fecha_aplicacion = db.Column(db.DateTime, server_default=db.func.now())

    # Relaciones
    pago_inbox = db.relationship('PaymentInbox', backref=db.backref('historial', uselist=False))
