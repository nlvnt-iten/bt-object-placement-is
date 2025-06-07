from typing import Optional
import math
from geopy.distance import geodesic

from algorithms.distance_resolvers.i_distance_resolver import IDistanceResolver

class GeodeticDistanceResolver(IDistanceResolver):
    def get_distance_in_meters(
        self,
        origin_lon: float,
        origin_lat: float,
        dest_lon: float,
        dest_lat: float,
        origin_alt: Optional[float] = None,
        dest_alt:   Optional[float] = None,
    ) -> float:

        horizontal = geodesic(
            (origin_lat, origin_lon),
            (dest_lat,   dest_lon),
        ).meters

        dz = (0.0 if dest_alt is None else dest_alt) - (0.0 if origin_alt is None else origin_alt)

        return math.hypot(horizontal, dz)

