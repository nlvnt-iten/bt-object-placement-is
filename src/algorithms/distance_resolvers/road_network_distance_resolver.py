from typing import Optional, Tuple
from collections import OrderedDict
from geopy.distance import geodesic
import osmnx as ox
import networkx as nx

from algorithms.distance_resolvers.i_distance_resolver import IDistanceResolver


class RoadNetworkDistanceResolver(IDistanceResolver):
    def __init__(self):
        self._cached_graph: Optional[nx.MultiDiGraph] = None
        self._cached_center: Optional[Tuple[float, float]] = None
        self._cached_radius_km: Optional[float] = None
        self._buffer_km = 1.0

        self._dist_cache: "OrderedDict[Tuple[float, float, float, float], float]" = OrderedDict()
        self._max_cache_size = 4096

    def set_road_network(self, graph: nx.MultiDiGraph | None = None,
                         center_coords: Tuple[float, float] | None = None,
                         radius_km: float | None = None):
        if graph is None:
            self._cached_graph = None
            self._cached_center = None
            self._cached_radius_km = None
            self._dist_cache.clear()
        else:
            self._cached_graph = graph
            self._cached_center = center_coords
            self._cached_radius_km = radius_km
    
    def clear_cache(self):
        self._cached_graph = None
        self._cached_center = None
        self._cached_radius_km = None
        self._dist_cache.clear()

    def get_distance_in_meters(
        self,
        origin_lon: float,
        origin_lat: float,
        dest_lon: float,
        dest_lat: float,
        origin_alt: Optional[float] = None,
        dest_alt: Optional[float] = None,
    ) -> float:

        key = (origin_lon, origin_lat, dest_lon, dest_lat)
        if key in self._dist_cache:
            print("RoadNetworkDistanceResolver: distance retrieved from cache.")
            self._dist_cache.move_to_end(key)
            return self._dist_cache[key]

        origin = (origin_lat, origin_lon)
        dest = (dest_lat, dest_lon)
        geo_dist_km = geodesic(origin, dest).km

        if geo_dist_km > 35:
            raise ValueError("Distance is too large, consider using a different method.")

        radius_km = max(geo_dist_km / 2 + self._buffer_km, self._buffer_km)

        center_lat = (origin_lat + dest_lat) / 2
        center_lon = (origin_lon + dest_lon) / 2
        center = (center_lat, center_lon)

        if not self._is_within_cache(origin, dest):
            try:
                G = ox.graph_from_point(center, dist=int(radius_km * 1000),
                                        network_type="drive",
                                        simplify=True,
                                        truncate_by_edge=True)
                self._cached_graph = G
                self._cached_center = center
                self._cached_radius_km = radius_km
                print(f"Fetched new graph with {len(G.nodes())} nodes, {len(G.edges())} edges")
            except Exception:
                return float("inf")

        try:
            origin_node = ox.nearest_nodes(self._cached_graph, X=origin_lon, Y=origin_lat)
            dest_node = ox.nearest_nodes(self._cached_graph, X=dest_lon, Y=dest_lat)
            print(f"Origin node: {origin_node}, Dest node: {dest_node}")
        except Exception as e:
            print(f"Error snapping to road nodes: {e}")
            return float("inf")

        try:
            route = nx.shortest_path(self._cached_graph, origin_node, dest_node, weight="length")
            dist_m = nx.path_weight(self._cached_graph, route, weight="length")
        except nx.NetworkXNoPath:
            dist_m = float("inf")

        if dist_m != float("inf"):
            if len(self._dist_cache) >= self._max_cache_size:
                old_key, _ = self._dist_cache.popitem(last=False)
                print(f"RoadNetworkDistanceResolver: cache full, evicted {old_key}")
            self._dist_cache[key] = dist_m

        return dist_m

    def _is_within_cache(self, origin: Tuple[float, float], dest: Tuple[float, float]) -> bool:
        if not self._cached_graph or not self._cached_center or self._cached_radius_km is None:
            return False
        radius = self._cached_radius_km - self._buffer_km * 0.25
        return all(geodesic(self._cached_center, pt).km <= radius for pt in [origin, dest])
