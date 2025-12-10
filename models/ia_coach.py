from datetime import datetime
from models import db
import uuid
import pytz
from core.datetime_util import UTCDateTime

def utc_now():
    """Retorna la fecha/hora actual en UTC con zona horaria"""
    return datetime.now(pytz.UTC)

class IAAnalisisDiario(db.Model):
    """Modelo para almacenar análisis diarios de datos del usuario enviados a IA"""
    __tablename__ = 'ia_analisis_diario'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_clerk = db.Column(db.String(191), db.ForeignKey('usuarios.id_clerk', ondelete='CASCADE'), nullable=False, index=True)
    fecha_analisis = db.Column(db.Date, nullable=False, index=True)
    datos_enviados = db.Column(db.Text, nullable=True)
    respuesta_ia = db.Column(db.Text, nullable=True)
    estado_procesamiento = db.Column(
        db.Enum('pendiente', 'procesado', 'error'), 
        default='pendiente', 
        nullable=False,
        index=True
    )
    error_mensaje = db.Column(db.Text, nullable=True)
    fecha_creacion = db.Column(UTCDateTime, default=utc_now, nullable=False)

    # Relaciones
    usuario = db.relationship('User', backref='ia_analisis_diarios')
    consejos = db.relationship('IAConsejo', backref='analisis', cascade='all, delete-orphan')

    __table_args__ = (
        db.UniqueConstraint('id_clerk', 'fecha_analisis', name='uniq_analisis_usuario_fecha'),
    )

    def __repr__(self):
        return f'<IAAnalisisDiario {self.id} - {self.id_clerk} - {self.estado_procesamiento}>'


class IAConsejo(db.Model):
    """Modelo para almacenar los consejos generados por IA"""
    __tablename__ = 'ia_consejos'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_analisis = db.Column(db.String(36), db.ForeignKey('ia_analisis_diario.id', ondelete='CASCADE'), nullable=False, index=True)
    id_clerk = db.Column(db.String(191), db.ForeignKey('usuarios.id_clerk', ondelete='CASCADE'), nullable=False, index=True)
    tipo_consejo = db.Column(
        db.Enum('motivacion', 'mejora_habito', 'nuevo_habito', 'ruptura_racha', 'felicitacion'),
        nullable=False,
        index=True
    )
    titulo = db.Column(db.String(200), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    leido = db.Column(db.Boolean, default=False)
    fecha_lectura = db.Column(UTCDateTime, nullable=True)
    generado_en = db.Column(UTCDateTime, default=utc_now, nullable=False, index=True)
    fecha_creacion = db.Column(UTCDateTime, default=utc_now, nullable=False)

    # Relaciones
    usuario = db.relationship('User', backref='ia_consejos', foreign_keys=[id_clerk])
    interacciones = db.relationship('IAConsejoInteraccion', backref='consejo', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<IAConsejo {self.id} - {self.tipo_consejo}>'


class IAConsejoInteraccion(db.Model):
    """Modelo para registrar las interacciones del usuario con los consejos"""
    __tablename__ = 'ia_consejos_interacciones'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_consejo = db.Column(db.String(36), db.ForeignKey('ia_consejos.id', ondelete='CASCADE'), nullable=False, index=True)
    id_clerk = db.Column(db.String(191), db.ForeignKey('usuarios.id_clerk', ondelete='CASCADE'), nullable=False, index=True)
    accion = db.Column(db.Enum('visto', 'archivado', 'seguido', 'ignorado'), nullable=False)
    fecha_accion = db.Column(UTCDateTime, default=utc_now, nullable=False)

    # Relaciones
    usuario = db.relationship('User', backref='ia_interacciones', foreign_keys=[id_clerk])

    def __repr__(self):
        return f'<IAConsejoInteraccion {self.id} - {self.accion}>'
