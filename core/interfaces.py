from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Tuple, Union
from datetime import date

class IDateTimeService(ABC):
    @abstractmethod
    def to_utc(self, dt: datetime, timezone: str) -> datetime:
        pass

    @abstractmethod
    def to_user_timezone(self, dt: datetime, user_id: str, default_timezone: str = 'UTC') -> datetime:
        pass

    @abstractmethod
    def get_user_local_date(self, user_id: str, target_date: Optional[Union[datetime, date]] = None) -> date:
        pass

class IUserService(ABC):
    @abstractmethod
    def get_user_timezone(self, user_id: str) -> Tuple[str, int]:
        pass

    @abstractmethod
    def set_user_timezone(self, user_id: str, timezone: str) -> bool:
        pass
