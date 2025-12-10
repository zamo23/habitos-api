import logging
from datetime import datetime
import pytz
from typing import Optional
from sqlalchemy import DateTime, TypeDecorator

logger = logging.getLogger(__name__)

class UTCDateTime(TypeDecorator):
    """
    Un tipo DateTime personalizado que asegura que todos los DateTime 
    se almacenan en UTC y se recuperan con zona horaria UTC.
    """
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Convierte el valor a UTC antes de almacenarlo en BD"""
        if value is None:
            return None
        
        if isinstance(value, datetime):
            if value.tzinfo is None:
                # Si es naive, asumir UTC
                logger.warning(f"DateTime naive detectado en bind: {value}, asumiendo UTC")
                value = pytz.UTC.localize(value)
            # Convertir a UTC
            return value.astimezone(pytz.UTC).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        """Recupera el valor de BD y asegura que tenga zona horaria UTC"""
        if value is None:
            return None
        
        if isinstance(value, datetime):
            if value.tzinfo is None:
                # Si es naive, asumir UTC (ya que se almacenó como UTC)
                return pytz.UTC.localize(value)
            return value.astimezone(pytz.UTC)
        return value

class DateTimeUtil:
    @staticmethod
    def ensure_utc(dt: datetime) -> datetime:
        """
        Asegura que una fecha/hora esté en UTC.
        
        Args:
            dt: Fecha/hora a convertir
            
        Returns:
            datetime: Fecha/hora en UTC
            
        Raises:
            ValueError: Si la fecha/hora no tiene información de zona horaria y no se puede convertir
        """
        if dt is None:
            raise ValueError("DateTime no puede ser None")
            
        if dt.tzinfo is None:
            logger.warning("DateTime sin zona horaria, asumiendo UTC")
            return pytz.UTC.localize(dt)
            
        return dt.astimezone(pytz.UTC)

    @staticmethod
    def validate_timezone(timezone: str) -> Optional[str]:
        """
        Valida una zona horaria y retorna su nombre canónico.
        
        Args:
            timezone: Nombre de la zona horaria a validar
            
        Returns:
            str: Nombre canónico de la zona horaria o None si es inválida
        """
        try:
            return pytz.timezone(timezone).zone
        except pytz.exceptions.UnknownTimeZoneError:
            logger.error(f"Zona horaria inválida: {timezone}")
            return None

    @staticmethod
    def get_current_utc() -> datetime:
        """
        Obtiene la fecha/hora actual en UTC.
        
        Returns:
            datetime: Fecha/hora actual en UTC
        """
        return datetime.now(pytz.UTC)
