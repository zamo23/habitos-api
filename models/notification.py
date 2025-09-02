import uuid
from datetime import datetime
from models import db

class Notification(db.Model):
    __tablename__ = 'notificaciones'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_clerk = db.Column(db.String(191), db.ForeignKey('usuarios.id_clerk'), nullable=False)
    tipo = db.Column(db.Enum('recordatorio', 'logro', 'sistema'), nullable=False)
    datos_json = db.Column(db.JSON)
    programada_para = db.Column(db.DateTime)
    enviada_en = db.Column(db.DateTime)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='notifications')
