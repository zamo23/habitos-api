import uuid
from datetime import datetime
import pytz
from models import db
from core.datetime_util import UTCDateTime

class Notification(db.Model):
    __tablename__ = 'notificaciones'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_clerk = db.Column(db.String(191), db.ForeignKey('usuarios.id_clerk'), nullable=False)
    tipo = db.Column(db.Enum('recordatorio', 'logro', 'sistema'), nullable=False)
    datos_json = db.Column(db.JSON)
    programada_para = db.Column(UTCDateTime)
    enviada_en = db.Column(UTCDateTime)
    fecha_creacion = db.Column(UTCDateTime, default=lambda: datetime.now(pytz.UTC))
    
    user = db.relationship('User', backref='notifications')
