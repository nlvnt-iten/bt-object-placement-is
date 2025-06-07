from typing import Optional

import networkx as nx

from models import PlacementPoint, PlacementPointID

class PlacementNetwork:
    def __init__(self, graph : nx.Graph, placement_point_data_key : str = "ppdata"):
        self._graph = graph
        self._placement_point_data_key = placement_point_data_key

    def get_graph(self) -> nx.Graph:
        return self._graph
    
    def set_graph(self, graph : nx.Graph) -> None:
        self._graph = graph
    
    def get_placement_point_data_key(self) -> str:
        return self._placement_point_data_key
    
    def set_placement_point_data_key(self, key : str) -> None:
        self._placement_point_data_key = key

    def get_placement_point_data(self, node_id : PlacementPointID) -> Optional[PlacementPoint]:
        if node_id in self._graph:
            return self._graph.nodes[node_id].get(self._placement_point_data_key, None)
        return None

    def set_placement_point_data(self, node_id : PlacementPointID, data : PlacementPoint) -> None:
        if node_id in self._graph:
            self._graph.nodes[node_id][self._placement_point_data_key] = data
        else:
            raise ValueError(f"Node {node_id} not found in the graph.")