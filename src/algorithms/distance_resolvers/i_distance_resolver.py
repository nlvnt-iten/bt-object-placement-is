from abc import ABC, abstractmethod
from typing import Optional

class IDistanceResolver(ABC):
    @abstractmethod
    def get_distance_in_meters(
        self,
        origin_lon: float,
        origin_lat: float,
        dest_lon: float,
        dest_lat: float,
        origin_alt: Optional[float] = None,
        dest_alt:   Optional[float] = None,
    ) -> float:
        raise NotImplementedError