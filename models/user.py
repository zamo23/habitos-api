from datetime import datetime
import pytz
from models import db
from core.datetime_util import DateTimeUtil

class User(db.Model):
    __tablename__ = 'usuarios'
    id_clerk = db.Column(db.String(191), primary_key=True)
    correo = db.Column(db.String(191))
    nombre_completo = db.Column(db.String(191))
    url_imagen = db.Column(db.Text)
    idioma = db.Column(db.String(10), default='es')
    zona_horaria = db.Column(db.String(50), default='America/Lima')
    cierre_dia_hora = db.Column(db.Integer, default=0)
    fecha_creacion = db.Column(db.DateTime, default=lambda: DateTimeUtil.get_current_utc())
    fecha_actualizacion = db.Column(db.DateTime, default=lambda: DateTimeUtil.get_current_utc(), 
                                  onupdate=lambda: DateTimeUtil.get_current_utc())
    
    def set_timezone(self, timezone: str) -> bool:
        """
        Establece la zona horaria del usuario, validando que sea válida.
        
        Args:
            timezone: Zona horaria a establecer
            
        Returns:
            bool: True si se estableció correctamente, False si es inválida
        """
        validated_timezone = DateTimeUtil.validate_timezone(timezone)
        if validated_timezone:
            self.zona_horaria = validated_timezone
            return True
        return False
