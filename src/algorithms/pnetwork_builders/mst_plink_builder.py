from typing import Optional
from copy import deepcopy

import networkx as nx

from models import PlacementNetwork, PlacementPoint

from utils import GraphUtils

from algorithms.distance_resolvers import IDistanceResolver
from algorithms.distance_resolvers import GeodeticDistanceResolver
from algorithms.pnetwork_builders import IPLinkBuilder

class MSTPLinkBuilder(IPLinkBuilder):
    def __init__(self,
                 distance_resolver : IDistanceResolver = GeodeticDistanceResolver(),
                 required_density : Optional[float] = None) -> None:
        self._distance_resolver = distance_resolver
        self._required_density = required_density

    def get_distance_resolver(self) -> IDistanceResolver:
        return self._distance_resolver
    
    def set_distance_resolver(self, resolver : IDistanceResolver) -> None:
        self._distance_resolver = resolver

    def get_required_density(self) -> Optional[float]:
        return self._required_density
    
    def set_required_density(self, density : Optional[float]) -> None:
        self._required_density = density

    def compute_placement_point_links(self,
                                      pnetwork : PlacementNetwork) -> PlacementNetwork:
        result_rn = deepcopy(pnetwork)
        
        initial_graph = deepcopy(pnetwork.get_graph())
        initial_edges = deepcopy(initial_graph.edges(data=True))

        initial_graph.remove_edges_from(initial_edges)

        try:
            complete_graph = self._create_complete_weighted_graph(pnetwork)
        except Exception as e:
            print(f"Error creating complete weighted graph: {e}")
            return None

        minimum_spanning_edges = nx.minimum_spanning_edges(complete_graph, data=True)

        def _add_type_to_edge(edge, type):
            edge[2]['type'] = type
            return edge
        
        result_rn.get_graph().add_edges_from([_add_type_to_edge(edge, "MST") for edge in minimum_spanning_edges if edge not in initial_edges])

        if self._required_density is not None:
            initial_edges_count = len(initial_edges)
            required_edges = GraphUtils.get_edges_count_from_density(pnetwork.get_graph().number_of_nodes(),
                                                                     self._required_density)
            
            for u, v, _ in sorted(complete_graph.edges(data=True), key=lambda x: x[2]['weight']):

                if len(result_rn.get_graph().edges()) - initial_edges_count >= required_edges:
                    break

                if not result_rn.get_graph().has_edge(u, v):
                    result_rn.get_graph().add_edge(u, v, type="Розширене MST")

        return result_rn
    
    def _create_complete_weighted_graph(self, pnetwork : PlacementNetwork) -> nx.Graph:
        complete_graph = nx.complete_graph(pnetwork.get_graph().nodes())

        for u, v in complete_graph.edges():
            u_ppoint : PlacementPoint = pnetwork.get_placement_point_data(u)
            v_ppoint : PlacementPoint = pnetwork.get_placement_point_data(v)

            if u_ppoint and v_ppoint:
                u_lon, u_lat, _ = u_ppoint.get_coordinates()
                v_lon, v_lat, _ = v_ppoint.get_coordinates()

                try:
                    distance = self._distance_resolver.get_distance_in_meters(
                        u_lon, u_lat,
                        v_lon, v_lat
                    )
                except Exception as e:
                    raise ValueError(f"Distance calculation failed for nodes {u} and {v}: {e}") from e

                print(f"Distance between {u} and {v}: {distance} m")

                complete_graph.add_edge(u, v, weight=distance)
            else:
                raise ValueError(f"Placement point data not found for nodes {u} or {v}.")

        return complete_graph
        