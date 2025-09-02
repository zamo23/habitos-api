from datetime import datetime, date, timedelta
import pytz
import logging
from typing import Optional, Union
from models import User
from core.interfaces import IDateTimeService
from core.datetime_util import DateTimeUtil

logger = logging.getLogger(__name__)

class TimezoneService(IDateTimeService):
    def __init__(self, default_timezone='UTC'):
        self.default_timezone = default_timezone
        
    def to_utc(self, dt: datetime, timezone: str) -> datetime:
        """
        Convierte una fecha/hora de una zona horaria específica a UTC.
        
        Args:
            dt: DateTime a convertir
            timezone: Zona horaria de origen
            
        Returns:
            datetime: Fecha/hora en UTC
            
        Raises:
            ValueError: Si la fecha/hora o zona horaria son inválidas
        """
        try:
            validated_timezone = DateTimeUtil.validate_timezone(timezone)
            if not validated_timezone:
                raise ValueError(f"Zona horaria inválida: {timezone}")
                
            if dt.tzinfo is None:
                dt = pytz.timezone(validated_timezone).localize(dt)
                
            return dt.astimezone(pytz.UTC)
        except Exception as e:
            logger.error(f"Error al convertir a UTC: {str(e)}")
            raise
    
    def to_user_timezone(self, dt: datetime, user_id: str, default_timezone: str = None) -> datetime:
        """
        Convierte una fecha/hora UTC a la zona horaria del usuario.
        
        Args:
            dt: DateTime en UTC
            user_id: ID del usuario
            default_timezone: Zona horaria por defecto si no se encuentra el usuario
            
        Returns:
            datetime: DateTime en la zona horaria del usuario
        """
        if dt is None:
            return None
            
        try:
            dt = DateTimeUtil.ensure_utc(dt)
            
            user = User.query.get(user_id)
            timezone_name = user.zona_horaria if user else (default_timezone or self.default_timezone)
            
            validated_timezone = DateTimeUtil.validate_timezone(timezone_name)
            if not validated_timezone:
                logger.warning(f"Zona horaria inválida para usuario {user_id}, usando {self.default_timezone}")
                validated_timezone = self.default_timezone
                
            tz = pytz.timezone(validated_timezone)
            return dt.astimezone(tz)
        except Exception as e:
            logger.error(f"Error en conversión de zona horaria: {str(e)}")
            return dt
            
    def get_user_local_datetime(self, user_id: str) -> datetime:
        """
        Obtener la fecha y hora actual en la zona horaria del usuario.
        
        Args:
            user_id: ID del usuario
            
        Returns:
            datetime: Fecha y hora actual en la zona horaria del usuario
        """
        try:
            utc_now = datetime.now(pytz.UTC)
            user = User.query.filter_by(id_clerk=user_id).first()
            timezone_name = user.zona_horaria if user else self.default_timezone
            
            validated_timezone = DateTimeUtil.validate_timezone(timezone_name)
            if not validated_timezone:
                logger.warning(f"Zona horaria inválida para usuario {user_id}, usando {self.default_timezone}")
                validated_timezone = self.default_timezone
                
            return self.to_user_timezone(utc_now, user_id, validated_timezone)
        except Exception as e:
            logger.error(f"Error al obtener datetime local: {str(e)}")
            return datetime.now(pytz.UTC)

    def get_user_local_date(self, user_id: str, target_date: Optional[Union[datetime, date]] = None) -> date:
        """
        Obtener fecha local del usuario según su zona horaria y hora de cierre de día.
        
        Args:
            user_id: ID del usuario
            target_date: Fecha objetivo opcional (si no se proporciona, se usa la fecha actual)
            
        Returns:
            date: Fecha local del usuario ajustada según su configuración
        """
        try:
            user = User.query.filter_by(id_clerk=user_id).first()
            if not user:
                logger.warning(f"Usuario {user_id} no encontrado, usando configuración por defecto")
                timezone_name = self.default_timezone
                closure_hour = 0
            else:
                timezone_name = user.zona_horaria
                closure_hour = getattr(user, 'cierre_dia_hora', 0)
            
            # Validar y obtener zona horaria
            validated_timezone = DateTimeUtil.validate_timezone(timezone_name)
            if not validated_timezone:
                logger.warning(f"Zona horaria inválida para usuario {user_id}, usando {self.default_timezone}")
                validated_timezone = self.default_timezone
                
            tz = pytz.timezone(validated_timezone)
            
            # Obtener fecha/hora actual en la zona horaria del usuario
            if target_date is None:
                now_local = datetime.now(tz)
            else:
                # Convertir fecha objetivo a datetime si es necesario
                if isinstance(target_date, date):
                    target_date = datetime.combine(target_date, datetime.min.time())
                # Asegurar que tiene zona horaria
                if target_date.tzinfo is None:
                    target_date = tz.localize(target_date)
                now_local = target_date.astimezone(tz)
            
            # Ajustar por hora de cierre
            adjusted_date = now_local - timedelta(hours=closure_hour)
            return adjusted_date.date()
            
        except Exception as e:
            logger.error(f"Error al obtener fecha local para usuario {user_id}: {str(e)}")
            # En caso de error, retornar la fecha actual UTC
            return datetime.now(pytz.UTC).date()

# Singleton instance
_instance = None

def get_timezone_service(default_timezone='UTC'):
    """
    Obtiene la instancia única del servicio de zona horaria.
    
    Args:
        default_timezone: Zona horaria por defecto a usar
        
    Returns:
        TimezoneService: Instancia única del servicio
    """
    global _instance
    if _instance is None:
        _instance = TimezoneService(default_timezone)
    return _instance

def get_user_local_date(user_id: str, target_date=None):
    """
    Obtiene la fecha local del usuario según su zona horaria.
    Wrapper para el método de TimezoneService.
    """
    service = get_timezone_service()
    return service.get_user_local_date(user_id, target_date)

def to_user_timezone(dt: datetime, user_id: str = None, user_timezone: str = None) -> datetime:
    """
    Convierte una fecha/hora UTC a la zona horaria del usuario.
    Args:
        dt: DateTime en UTC
        user_id: ID del usuario (opcional si se proporciona user_timezone)
        user_timezone: Zona horaria del usuario (opcional si se proporciona user_id)
    Returns:
        datetime: DateTime en la zona horaria del usuario
    """
    service = get_timezone_service()
    if user_timezone:
        timezone_name = user_timezone
    else:
        timezone_name = None
    return service.to_user_timezone(dt, user_id, timezone_name)

def format_datetime(dt, user_id=None, user_timezone=None, date_format='%d/%m/%Y', time_format='%H:%M:%S'):
    """
    Formatea una fecha/hora UTC a la zona horaria del usuario y devuelve strings formateados.

    Args:
        dt: DateTime en UTC
        user_id: ID del usuario (opcional si se proporciona user_timezone)
        user_timezone: Zona horaria del usuario (opcional si se proporciona user_id)
        date_format: Formato para la fecha
        time_format: Formato para la hora

    Returns:
        Tuple (fecha_str, hora_str)
    """
    if dt is None:
        return None, None

    local_dt = to_user_timezone(dt, user_id, user_timezone)
    return local_dt.strftime(date_format), local_dt.strftime(time_format)

def now_in_timezone(user_id=None, user_timezone=None):
    """
    Obtiene la fecha/hora actual en la zona horaria del usuario.

    Args:
        user_id: ID del usuario (opcional si se proporciona user_timezone)
        user_timezone: Zona horaria del usuario (opcional si se proporciona user_id)

    Returns:
        DateTime actual en la zona horaria del usuario
    """
    now_utc = datetime.now(pytz.UTC)
    return to_user_timezone(now_utc, user_id, user_timezone)
