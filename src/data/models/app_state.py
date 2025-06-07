from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional

import networkx as nx


@dataclass
class NodeAttr:
    lon: float
    lat: float
    placed_object_type: Optional[str] = None
    placed_object_color: Optional[Tuple[float, float, float]] = None
    independent_contribution_rate: Optional[float] = None
    context_contribution_rate: Optional[float] = None


@dataclass
class EdgeAttr:
    type: Optional[str] = None
    weight: Optional[float] = None


@dataclass
class AppState:
    placement_graph_nodes: Dict[int, NodeAttr] = field(default_factory=dict)
    placement_graph_edges: List[Tuple[int, int, EdgeAttr]] = field(default_factory=list)
    placement_object_types: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    distance_resolver_type: str = "GEODETIC"
    adjacent_same_type_penalty: float = 0.0

    @classmethod
    def from_vm(cls, vm: "PlacementGraphVM") -> "AppState":
        nodes = {
            nid: NodeAttr(
                lon=d["lon"], lat=d["lat"],
                placed_object_type=d.get("placed_object_type"),
                placed_object_color=tuple(d["placed_object_color"]) if "placed_object_color" in d else None,
                independent_contribution_rate=d.get("independent_contribution_rate"),
                context_contribution_rate=d.get("context_contribution_rate"),
            )
            for nid, d in vm.graph.nodes(data=True)
        }
        edges = [
            (u, v, EdgeAttr(type=e.get("type"), weight=e.get("weight")))
            for u, v, e in vm.graph.edges(data=True)
        ]
        return cls(
            placement_graph_nodes=nodes,
            placement_graph_edges=edges,
            placement_object_types=vm.placement_object_types,
            distance_resolver_type=vm.distance_resolver_type.name,
            adjacent_same_type_penalty=vm.adjacent_st_penalty #,
            # overall_placement_efficiency=vm.overall_placement_efficiency,
        )

    def to_vm(self, vm: "PlacementGraphVM") -> None:
        graph = nx.Graph()
        for nid, attr in self.placement_graph_nodes.items():
            graph.add_node(
                nid, lon=attr.lon, lat=attr.lat,
                placed_object_type=attr.placed_object_type,
                placed_object_color=attr.placed_object_color,
                independent_contribution_rate=attr.independent_contribution_rate,
                context_contribution_rate=attr.context_contribution_rate,
            )
        for u, v, ea in self.placement_graph_edges:
            graph.add_edge(u, v, type=ea.type, weight=ea.weight)
        
        vm._id_generator.set_min(max(self.placement_graph_nodes.keys(), default=0) + 1)
        vm._distance_resolver_type = \
            getattr(vm._distance_resolver_type.__class__, self.distance_resolver_type)
        vm._adjacent_st_penalty = self.adjacent_same_type_penalty

        for obj_type_name, data in self.placement_object_types.items():
            if data["count"] > 0:
                vm._color_generator.add_used_color(tuple(data["color"]))

        vm._placement_graph = graph
        vm._placement_object_types = self.placement_object_types
        # vm._overall_placement_efficiency = self.overall_placement_efficiency
