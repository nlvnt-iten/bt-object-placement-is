from typing import List, Dict
from copy import deepcopy

from algorithms.placement_solvers import IPlacementAlgorithm

from models import PlacementNetwork, PlacementObject

class AdjPenPlacementAlgorithmGreedy(IPlacementAlgorithm):
    def __init__(self, penalty: float = 0.5):
        self._penalty = penalty

    def get_penalty(self) -> float:
        return self._penalty
    
    def set_penalty(self, penalty: float) -> None:
        self._penalty = penalty

    def compute_placement(self, pnetwork : PlacementNetwork,
                          to_place : List[PlacementObject]) -> PlacementNetwork:
        penalty_multiplier = 1.0 - self._penalty

        result_rn = deepcopy(pnetwork)

        sorted_nodes = sorted(deepcopy(pnetwork.get_graph().nodes(data=False)),
                              key=lambda node_id: pnetwork.get_graph().degree(node_id))
        objects_to_place = self._construct_placement_objects_dict(to_place)

        for node_id in sorted_nodes:
            adjacent_nodes = list(result_rn.get_graph().adj[node_id])
            
            max_context_contribution = -1
            max_context_contribution_object = None
            for object, count in objects_to_place.items():
                if count == 0:
                    continue

                has_adjacent_same_type_object = any(
                    ((object == result_rn.get_placement_point_data(adj_node_id).get_object()) if \
                      result_rn.get_placement_point_data(adj_node_id).get_object() is not None else False) \
                        for adj_node_id in adjacent_nodes
                )

                potential_context_contribution = object.get_independent_contribution_rate() * \
                    (penalty_multiplier if has_adjacent_same_type_object else 1.0)
                
                if potential_context_contribution > max_context_contribution:
                    max_context_contribution = potential_context_contribution
                    max_context_contribution_object = object

            result_rn.get_placement_point_data(node_id).set_object(
                deepcopy(max_context_contribution_object)
            )

            objects_to_place[max_context_contribution_object] -= 1
            if objects_to_place[max_context_contribution_object] == 0:
                del objects_to_place[max_context_contribution_object]

        return result_rn

    def _construct_placement_objects_dict(self, to_place: List[PlacementObject]) -> Dict[PlacementObject, int]:
        placement_objects_dict = {}
        for obj in to_place:
            if obj not in placement_objects_dict:
                placement_objects_dict[obj] = 0
            placement_objects_dict[obj] += 1
        return placement_objects_dict