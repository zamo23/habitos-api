from dependency_injector import containers, providers
from services.timezone_service import TimezoneService

class Container(containers.DeclarativeContainer):
    
    config = providers.Configuration()
    
    timezone_service = providers.Singleton(
        TimezoneService,
        default_timezone=config.default_timezone
    )