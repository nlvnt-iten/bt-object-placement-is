from typing import Tuple
from copy import deepcopy

from algorithms.placement_efficiency.i_placement_efficiency_determinator import IPlacementEfficiencyDeterminator

from models import PlacementNetwork

class PEffAdjPenDeterminator(IPlacementEfficiencyDeterminator):
    def __init__(self, penalty: float = 0.0):
        self._penalty = penalty
    
    def get_penalty(self) -> float:
        return self._penalty
    
    def set_penalty(self, penalty: float) -> None:  
        self._penalty = penalty

    def calculate_placement_efficiency(self,
                                       pnetwork : PlacementNetwork) -> Tuple[PlacementNetwork, float]:
        result_rn = deepcopy(pnetwork)
        result_total_efficiency = 0.0

        penalty_multiplier = 1.0 - self._penalty


        to_visit = set(result_rn.get_graph().nodes(data=False))
        while len(to_visit):
            node_id = to_visit.pop()

            placement_point = result_rn.get_placement_point_data(node_id)
            if placement_point.get_object() is None:
                continue

            adjacent_nodes = list(result_rn.get_graph().adj[node_id])

            has_adjacent_same_type_object = False
            for adj_node_id in adjacent_nodes:
                adj_node_ppoint = result_rn.get_placement_point_data(adj_node_id)

                if adj_node_ppoint.get_object() is None:
                    if adj_node_id in to_visit:
                        to_visit.remove(adj_node_id)
                    continue

                if adj_node_ppoint.get_object() == placement_point.get_object():
                    has_adjacent_same_type_object = True
                    if adj_node_id in to_visit:
                        to_visit.remove(adj_node_id)

                        adj_node_object = adj_node_ppoint.get_object()
                        context_contribution = adj_node_object.get_independent_contribution_rate() * penalty_multiplier

                        adj_node_object.set_context_contribution_rate(context_contribution)
                        adj_node_ppoint.set_object(adj_node_object)
                        result_rn.set_placement_point_data(adj_node_id, adj_node_ppoint)

                        result_total_efficiency += context_contribution
                
            placement_object = placement_point.get_object()
            if has_adjacent_same_type_object:
                context_contribution = placement_object.get_independent_contribution_rate() * penalty_multiplier
            else:
                context_contribution = placement_object.get_independent_contribution_rate()

            placement_object.set_context_contribution_rate(context_contribution)
            placement_point.set_object(placement_object)
            result_rn.set_placement_point_data(node_id, placement_point)

            result_total_efficiency += context_contribution

        return result_rn, result_total_efficiency