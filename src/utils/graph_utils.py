import math

class GraphUtils:
    @staticmethod
    def get_min_density_connected_graph(node_count : int) -> float:
        if node_count > 1:
            return 2 / node_count
        return 0.0
    
    @staticmethod
    def get_min_edges_count_connected_graph(node_count : int) -> int:
        if node_count > 1:
            return node_count - 1
        return 0
    
    @staticmethod 
    def get_edges_count_from_density(node_count : int,
                                     density : float) -> int:
        if node_count <= 1:
            return 0

        raw_edges = (density * node_count * (node_count - 1)) / 2

        return int(math.floor(raw_edges + 0.5))