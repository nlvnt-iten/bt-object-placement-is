import osmnx as ox
import numpy as np
import miniball
from networkx import Graph, MultiDiGraph
from typing import Tuple
from math import sqrt


class RoadNetworkProvider:
    def __init__(self):
        self._cache_center: Tuple[float, float] | None = None
        self._cache_radius_m: float | None = None
        self._cache_network: MultiDiGraph | None = None

    def get_road_network_coverage(self, graph: Graph, buffer_km: float) -> MultiDiGraph:
            if graph.number_of_nodes() == 0:
                raise ValueError("Input graph has no nodes")

            coords = []
            for _, data in graph.nodes(data=True):
                lat = data.get("lat")
                lon = data.get("lon")
                if lat is not None and lon is not None:
                    coords.append((lat, lon))
                else:
                     raise ValueError("Node with no valid coordinates")

            points = np.array(coords)
            center, radius_sq = miniball.get_bounding_ball(points)
            radius_deg = np.sqrt(radius_sq)
            radius_with_buffer_deg = radius_deg + (buffer_km / 111.0)
            radius_m = radius_with_buffer_deg * 111000

            if radius_m > 35000 / 2:
                 raise ValueError("Distance is too large, consider using a different method.")

            center = (float(tuple(center)[0]), float(tuple(center)[1]))

            if self._cache_center and self._cache_radius_m and self._cache_network:
                d_lat = (center[0] - self._cache_center[0]) * 111_000.0
                d_lon = (center[1] - self._cache_center[1]) * 111_000.0
                centre_dist_m = sqrt(d_lat ** 2 + d_lon ** 2)

                if centre_dist_m + radius_m <= self._cache_radius_m:
                    print("RoadNetworkProvider: returning cached road network.")
                    return self._cache_network, self._cache_center, self._cache_radius_m / 1_000.0

            network = ox.graph_from_point(center,
                                          dist=radius_m,
                                          network_type='drive',
                                          simplify=True,
                                          truncate_by_edge=True)
            
            self._cache_center = center
            self._cache_radius_m = radius_m
            self._cache_network = network

            print(center)
            print(radius_m / 1000)
            return network, center, radius_m / 1000